import os
import json
import io
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import google.generativeai as genai
import requests
from werkzeug.utils import secure_filename

from utils import (
    extract_json, 
    normalize_output, 
    fallback_response, 
    build_upskill, 
    load_upskill_db
)

from resume_utils import (
    extract_resume_text,
    preprocess_resume_text,
    analyze_resume_keywords,
    calculate_ats_score
)

# ENVIRONMENT & AI CONFIGURATION
load_dotenv()

# Fetch Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Track AI system health for frontend indicator
AI_STATUS = {
    "api_key_loaded": bool(GEMINI_API_KEY),
    "model_responded": False,
    "model_parsed": False,
    "last_error": None
}

# Configure Gemini only if API key is available
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Initialize Flask app
app = Flask(__name__, static_folder="static", static_url_path="")

# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Load the database once at startup
UPSKILL_DB = load_upskill_db()

# ROUTES
@app.route("/")
def index():
    return send_from_directory("static", "home.html")


@app.route("/guidefy")
def guidefy():
    return send_from_directory("static", "guidefy.html")


@app.route("/resume")
def resume():
    return send_from_directory("static", "resume.html")


@app.route("/api-status")
def api_status():
    return jsonify(AI_STATUS)


@app.route("/career", methods=["POST"])
def career():
    data = request.get_json(force=True)
    user_text = f"{data.get('interests', '')} {data.get('career_goal', '')}"

    try:
        prompt = f"""
You are a backend API.
Return ONLY raw JSON.
Give output in at least 20-30 words per field.
The confidence_score.overall must be a number between 0 and 100 (percentage).
Do Not use 1–5 or 1–10 scales.
{{
  "careers":[{{"name":"","justification":""}}],
  "courses":[{{"name":"","description":""}}],
  "next_steps":[{{"action":"","details":""}}],
  "confidence_score":{{"overall":0,"explanation":""}},
  "skill_gap_analysis":{{"missing_skills":[]}}
}}

User interests: {data.get('interests')}
Career goal: {data.get('career_goal')}
"""
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        response = model.generate_content(prompt)

        AI_STATUS["model_responded"] = True

        text = response.text if hasattr(response, "text") else response.candidates[0].content.parts[0].text
        raw = extract_json(text)

        AI_STATUS["model_parsed"] = True
        AI_STATUS["last_error"] = None

        return jsonify({"recommendation": normalize_output(raw, user_text, UPSKILL_DB)})

    except Exception as e:
        print("❌ AI ERROR:", e)
        AI_STATUS["model_parsed"] = False
        AI_STATUS["last_error"] = str(e)

        fb = fallback_response()
        fb["upskill"] = build_upskill(user_text, UPSKILL_DB)

        return jsonify({"recommendation": fb}), 200


@app.route("/resume-analyze", methods=["POST"])
def resume_analyze():
    """Analyze uploaded resume and provide detailed feedback."""
    
    # Check if file is present
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['resume']
    
    # Check if file is selected
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Check if file type is allowed
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Only PDF and DOCX files are allowed."}), 400
    
    try:
        # Extract text from resume
        file_stream = io.BytesIO(file.read())
        resume_text = extract_resume_text(file_stream, file.filename)
        
        # Preprocess text
        clean_text = preprocess_resume_text(resume_text)
        
        # Analyze keywords
        keywords = analyze_resume_keywords(clean_text)
        
        # Calculate ATS score
        ats_score = calculate_ats_score(clean_text, keywords)
        
        # Get AI analysis
        prompt = f"""
You are an expert resume reviewer and career coach.
Analyze the following resume and provide detailed feedback in JSON format.

Resume Content:
{clean_text[:3000]}  # Limit to first 3000 chars

Provide analysis in this EXACT JSON format:
{{
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "weaknesses": ["weakness 1", "weakness 2", "weakness 3"],
  "missing_keywords": ["keyword 1", "keyword 2", "keyword 3"],
  "formatting_feedback": "Brief feedback on structure and formatting",
  "action_items": [
    {{"priority": "high", "item": "specific action"}},
    {{"priority": "medium", "item": "specific action"}},
    {{"priority": "low", "item": "specific action"}}
  ],
  "overall_impression": "Brief overall assessment"
}}

Be specific, actionable, and constructive.
"""
        
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        response = model.generate_content(prompt)
        
        text = response.text if hasattr(response, "text") else response.candidates[0].content.parts[0].text
        ai_analysis = extract_json(text)
        
        # Combine all analysis
        result = {
            "ats_score": ats_score,
            "keywords_found": keywords,
            "analysis": ai_analysis
        }
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print("❌ Resume Analysis Error:", e)
        return jsonify({"error": "Failed to analyze resume. Please try again."}), 500

# APPLICATION ENTRY POINT
if __name__ == "__main__":
    print("Server running at http://127.0.0.1:5050")
    app.run(debug=True, port=5050, threaded=True)
