import os
import json
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import google.generativeai as genai
import requests

from utils import (
    extract_json, 
    normalize_output, 
    fallback_response, 
    build_upskill, 
    load_upskill_db
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

# Load the database once at startup
UPSKILL_DB = load_upskill_db()

# ROUTES
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


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

# APPLICATION ENTRY POINT
if __name__ == "__main__":
    print("Server running at http://127.0.0.1:5050")
    app.run(debug=True, port=5050, threaded=True)
