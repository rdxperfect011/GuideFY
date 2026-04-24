"""
GuideFY AI Career Guidance System - Backend API
------------------------------------------------
This module serves as the primary backend server for GuideFY.
It handles routing, AI integrations (Google Gemini), file parsing for resumes,
and NLP-based context extraction to provide personalized career recommendations.
"""

import os
import io
import time
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import custom utilities for data formatting and fallback responses
from utils import (
    extract_json, 
    normalize_output, 
    fallback_response, 
    build_upskill, 
    load_upskill_db
)

# Import resume parsing and analysis utilities
from resume_utils import (
    extract_resume_text,
    preprocess_resume_text,
    analyze_resume_keywords,
    calculate_ats_score,
    RESUME_ANALYSIS_PROMPT,
    get_nlp_model,
    extract_nlp_analysis
)

# ==========================================
# ENVIRONMENT & AI CONFIGURATION
# ==========================================

# Load environment variables from .env file (e.g., API keys)
load_dotenv()

# Fetch the Gemini API key from the environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Track AI system health for frontend indicator
# This dictionary is served at /api-status to let the frontend know if the AI backend is ready.
AI_STATUS = {
    "api_key_loaded": bool(GEMINI_API_KEY),
    "model_responded": False,
    "model_parsed": False,
    "last_error": None
}

# Configure the Gemini client only if the API key is successfully loaded
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

def generate_with_retry(contents, primary_model="gemini-2.5-flash", fallback_model="gemini-flash-latest", max_retries=3, base_delay=2):
    """Call Gemini API with primary model, fallback to secondary model on 429 errors with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model=primary_model, contents=contents)
        except Exception as e:
            if "429" in str(e) or "ResourceExhausted" in str(type(e).__name__):
                print(f"⚠️ API Rate Limit (429) hit on {primary_model}. Trying fallback {fallback_model}...")
                try:
                    return client.models.generate_content(model=fallback_model, contents=contents)
                except Exception as fallback_e:
                    if "429" in str(fallback_e) or "ResourceExhausted" in str(type(fallback_e).__name__):
                        if attempt == max_retries - 1:
                            raise fallback_e
                        print(f"⚠️ Both models rate limited. Retrying in {base_delay * (2 ** attempt)}s (Attempt {attempt+1}/{max_retries})...")
                        time.sleep(base_delay * (2 ** attempt))
                    else:
                        raise fallback_e
            else:
                raise e

# ==========================================
# FLASK APPLICATION SETUP
# ==========================================

# Initialize the Flask web application
# static_folder="static" and static_url_path="" allow serving frontend files from the root URL
app = Flask(__name__, static_folder="static", static_url_path="")

# Configure file upload limits and allowed formats for resumes
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Enforce a 10MB maximum file size limit
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}  # Restrict allowed file types

def allowed_file(filename):
    """
    Checks if the uploaded file has a valid and permitted extension.
    
    Args:
        filename (str): The name of the uploaded file.
        
    Returns:
        bool: True if the file extension is allowed, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Load the upskilling database once at startup to optimize response times
UPSKILL_DB = load_upskill_db()

# ==========================================
# ROUTES
# ==========================================

@app.route("/")
def index():
    """Serves the main landing page of the application."""
    return send_from_directory("static", "home.html")


@app.route("/guidefy")
def guidefy():
    """Serves the career recommendation dashboard interface."""
    return send_from_directory("static", "guidefy.html")


@app.route("/resume")
def resume():
    """Serves the resume parsing and analysis interface."""
    return send_from_directory("static", "resume.html")


@app.route("/api-status")
def api_status():
    """
    Health check endpoint for the frontend.
    Returns the current operational status of the AI services.
    """
    return jsonify(AI_STATUS)


@app.route("/career", methods=["POST"])
def career():
    """
    Handles career recommendation requests from the user.
    
    Expected JSON payload: 
    {
        "interests": "...", 
        "career_goal": "...", 
        "strengths": "...", 
        "preferred_subjects": "..."
    }
    
    Returns:
        JSON response containing career paths, courses, next steps, confidence scores, 
        and upskilling resources generated by the AI model.
    """
    # Extract user input payload
    data = request.get_json(force=True)
    interests = data.get('interests', '')
    career_goal = data.get('career_goal', '')
    strengths = data.get('strengths', '')
    preferred_subjects = data.get('preferred_subjects', '')
    
    # Concatenate all inputs into a single context string for processing
    user_text = f"{interests} {career_goal} {strengths} {preferred_subjects}".strip()

    # ==========================================
    # NLP Context Extraction Pipeline
    # ==========================================
    # Instead of sending raw user input directly to the LLM (which can cause
    # loose interpretations or hallucinations), we intercept the text and 
    # analyze it using the spaCy Natural Language Processing library.
    # We explicitly tokenize the grammar to find Action Verbs (Methodology), 
    # Nouns (Hard Skills/Concepts), and Adjectives (Behavioral Traits).
    nlp_verbs, nlp_nouns, nlp_adjectives = [], [], []
    nlp = get_nlp_model()
    
    # Process text through spaCy if available
    if nlp and user_text:
        doc = nlp(f"{interests} {strengths} {preferred_subjects}")
        nlp_verbs = list(set([token.lemma_.lower() for token in doc if token.pos_ == 'VERB']))
        nlp_nouns = list(set([token.lemma_.lower() for token in doc if token.pos_ == 'NOUN']))
        nlp_adjectives = list(set([token.lemma_.lower() for token in doc if token.pos_ == 'ADJ']))

    try:
        # Construct the complex prompt incorporating the extracted NLP data
        prompt = f"""
Return ONLY raw JSON in this EXACT structure.
Calculate confidence_score.overall as weighted average of 4 dynamic 0-100 factors.
{{
  "careers":[{{"name":"","justification":"20+ words"}}],
  "courses":[{{"name":"","description":"20+ words"}}],
  "next_steps":[{{"action":"","details":"20+ words"}}],
  "confidence_score":{{
    "overall": 0,
    "breakdown": {{"input_detail_quality": 0, "skill_relevance": 0, "career_alignment": 0, "feasibility": 0}},
    "explanation": "20+ words"
  }},
  "skill_gap_analysis":{{"missing_skills":[]}},
  "keywords_found":[]
}}
Details: Interests: {interests}, Strengths: {strengths}, Subjects: {preferred_subjects}, Goal: {career_goal}
NLP Verbs: {', '.join(nlp_verbs) if nlp_verbs else 'None'}
NLP Nouns: {', '.join(nlp_nouns) if nlp_nouns else 'None'}
NLP Adjs: {', '.join(nlp_adjectives) if nlp_adjectives else 'None'}
Use NLP context for personalized pathway and identify missing skills.
"""
        # Call the configured Gemini model to generate content
        response = generate_with_retry(
            contents=prompt
        )

        # Update status tracking
        AI_STATUS["model_responded"] = True

        # Extract textual response safely
        text = response.text if hasattr(response, "text") else response.candidates[0].content.parts[0].text
        
        # Parse the JSON embedded in the markdown response
        raw = extract_json(text)

        # Mark as successful
        AI_STATUS["model_parsed"] = True
        AI_STATUS["last_error"] = None

        # Normalize the LLM output and append upskilling database context before returning to client
        return jsonify({"recommendation": normalize_output(raw, user_text, UPSKILL_DB)})

    except Exception as e:
        # In case of any AI failure (timeout, structure failure) or parsing error, 
        # log it and gracefully return a predefined static fallback response.
        print("❌ AI ERROR:", e)
        AI_STATUS["model_parsed"] = False
        AI_STATUS["last_error"] = str(e)

        fb = fallback_response()
        # Build the static upskilling section even when AI fails
        fb["upskill"] = build_upskill(user_text, UPSKILL_DB)

        return jsonify({"recommendation": fb}), 200


@app.route("/resume-analyze", methods=["POST"])
def resume_analyze():
    """
    Handles file uploads for resume analysis.
    Extracts text from PDFs/DOCXs, processes keywords via NLP, calculates ATS scores,
    and runs the content through Gemini to generate qualitative feedback.
    """
    
    # 1. Validate the presence of the file in the request
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['resume']
    
    # 2. Validate that the user actually selected a file
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # 3. Validate file extension against allowed types
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Only PDF and DOCX files are allowed."}), 400
    
    try:
        # Load the file into a byte stream for memory-efficient parsing
        file_stream = io.BytesIO(file.read())
        
        # Extract raw text from the parsed document
        resume_text = extract_resume_text(file_stream, file.filename)
        
        # Clean and normalize the text (remove messy whitespace, etc.)
        clean_text = preprocess_resume_text(resume_text)
        
        # Perform custom NLP scanning for technical and soft skills keywords
        keywords = analyze_resume_keywords(clean_text)
        
        # Calculate a deterministic Applicant Tracking System (ATS) score based on structural elements
        ats_data = calculate_ats_score(clean_text, keywords)
        ats_score = ats_data["total"]
        ats_breakdown = ats_data["breakdown"]
        
        # Perform deep NLP analysis for experience levels and education mapping
        nlp_analysis = extract_nlp_analysis(clean_text)
        
        # Send the first 2000 characters to Gemini for high-level qualitative analysis 
        prompt = RESUME_ANALYSIS_PROMPT.format(resume_text=clean_text[:2000])
        
        response = generate_with_retry(
            contents=prompt
        )
        
        # Safely extract text and parse the resulting JSON string
        text = response.text if hasattr(response, "text") else response.candidates[0].content.parts[0].text
        ai_analysis = extract_json(text)
        
        # Compile deterministic algorithms and generative AI outputs into one robust payload
        result = {
            "ats_score": ats_score,
            "ats_breakdown": ats_breakdown,
            "keywords_found": keywords,
            "analysis": ai_analysis,
            "nlp_analysis": nlp_analysis
        }
        
        return jsonify(result)
        
    except ValueError as e:
        # Handle custom validation errors thrown by the utility functions
        print("❌ Resume Validation Error:", e)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        # Handle systemic failures (e.g., API issues, critical parser crashes)
        print("❌ Resume Analysis Error:", e)
        # Check if we have partially computed data (ATS and NLP) to return as a fallback
        if 'ats_score' in locals() and 'nlp_analysis' in locals():
            print("⚠️ Returning fallback resume analysis due to AI failure")
            fallback_result = {
                "ats_score": ats_score,
                "ats_breakdown": ats_breakdown,
                "keywords_found": keywords,
                "analysis": {
                    "strengths": ["Core concepts identified", "Experience matches some keywords"],
                    "weaknesses": ["Could not perform deep AI analysis at this time"],
                    "missing_keywords": ["Review the ATS score details"],
                    "formatting_feedback": "Check standard ATS guidelines",
                    "action_items": [
                        {"priority": "high", "item": "Review skill matches below"}
                    ],
                    "overall_impression": "Basic ATS scan complete. AI feedback currently unavailable.",
                    "ai_comparison": {
                        "ats_score": ats_score,
                        "skills_match": "N/A",
                        "keyword_match": "N/A",
                        "final_recommendation": "Use ATS breakdown as your primary guide",
                        "reasoning": "AI generation failed, relying on deterministic ATS engine."
                    }
                },
                "nlp_analysis": nlp_analysis
            }
            return jsonify(fallback_result), 200
            
        return jsonify({"error": "Failed to analyze resume. Please try again."}), 500


# ==========================================
# APPLICATION ENTRY POINT
# ==========================================
if __name__ == "__main__":
    # Start the Flask development server on port 5050 with multithreading enabled
    print("Server running at http://127.0.0.1:5060")
    app.run(debug=True, port=5050, threaded=True)

