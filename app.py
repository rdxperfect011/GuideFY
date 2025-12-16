import os
import json
import re
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import google.generativeai as genai

# ==========================
# ENV SETUP
# ==========================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

AI_STATUS = {
    "api_key_loaded": bool(GEMINI_API_KEY),
    "model_responded": False,
    "model_parsed": False,
    "last_error": None
}

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__, static_folder="static", static_url_path="")

# ==========================
# UPSKILL DATABASE
# ==========================
UPSKILL_DB = {
    "business": {
        "title": "Business & Management Essentials",
        "video": {
            "platform": "freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=9pJ7C6J6d-8",
            "thumbnail": "https://img.youtube.com/vi/9pJ7C6J6d-8/hqdefault.jpg"
        },
        "platforms": [
            ("Coursera", "https://www.coursera.org/browse/business"),
            ("Harvard Online", "https://online.hbs.edu/"),
            ("Google Digital Garage", "https://learndigital.withgoogle.com/")
        ],
        "description": "Covers core business principles including management, strategy, analytics, and entrepreneurship."
    },
    "technology": {
        "title": "Software & IT Fundamentals",
        "video": {
            "platform": "freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=rfscVS0vtbw",
            "thumbnail": "https://img.youtube.com/vi/rfscVS0vtbw/hqdefault.jpg"
        },
        "platforms": [
            ("Coursera", "https://www.coursera.org/browse/computer-science"),
            ("edX", "https://www.edx.org/learn/computer-science"),
            ("Udemy", "https://www.udemy.com/topic/programming/")
        ],
        "description": "Introduces programming concepts, software development, and IT foundations."
    },
    "ai": {
        "title": "AI & Data Science Foundations",
        "video": {
            "platform": "freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=GwIo3gDZCVQ",
            "thumbnail": "https://img.youtube.com/vi/GwIo3gDZCVQ/hqdefault.jpg"
        },
        "platforms": [
            ("Coursera", "https://www.coursera.org/browse/data-science"),
            ("Google AI", "https://ai.google/education/"),
            ("Kaggle", "https://www.kaggle.com/learn")
        ],
        "description": "Covers AI, machine learning, and data analytics fundamentals."
    },
    "cyber": {
        "title": "Cyber Security Basics",
        "video": {
            "platform": "Simplilearn",
            "url": "https://www.youtube.com/watch?v=U_P23SqJaDc",
            "thumbnail": "https://img.youtube.com/vi/U_P23SqJaDc/hqdefault.jpg"
        },
        "platforms": [
            ("Coursera", "https://www.coursera.org/browse/information-technology/security"),
            ("Cisco Networking Academy", "https://www.netacad.com/"),
            ("TryHackMe", "https://tryhackme.com/")
        ],
        "description": "Introduces cyber threats, network security, and ethical hacking basics."
    },
    "generic": {
        "title": "Career Skill Development",
        "video": {
            "platform": "freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=ZXsQAXx_ao0",
            "thumbnail": "https://img.youtube.com/vi/ZXsQAXx_ao0/hqdefault.jpg"
        },
        "platforms": [
            ("Coursera", "https://www.coursera.org/"),
            ("edX", "https://www.edx.org/"),
            ("Udemy", "https://www.udemy.com/")
        ],
        "description": "Builds transferable skills like communication, problem-solving, and digital literacy."
    }
}

# ==========================
# HELPERS
# ==========================
def extract_json(text):
    
    text = text.replace("```json", "").replace("```", "").strip()

    start = text.find("{")
    end = text.rfind("}") + 1

    if start == -1 or end == -1:
        raise ValueError("No JSON object found")

    return json.loads(text[start:end])

def detect_field(text):
    t = text.lower()
    if any(k in t for k in ["business", "management", "commerce", "mba", "entrepreneur"]):
        return "business"
    if any(k in t for k in ["software", "programming", "developer", "it", "computer"]):
        return "technology"
    if any(k in t for k in ["ai", "machine learning", "data"]):
        return "ai"
    if any(k in t for k in ["cyber", "security", "hacking"]):
        return "cyber"
    return "generic"

def build_upskill(user_text):
    return UPSKILL_DB[detect_field(user_text)]

def normalize_output(raw, user_text):
    return {
        "careers": raw.get("careers", []),
        "courses": raw.get("courses", []),
        "next_steps": raw.get("next_steps", []),
        "confidence_score": raw.get("confidence_score", {}),
        "skill_gap_analysis": raw.get("skill_gap_analysis", {}),
        "upskill": build_upskill(user_text)
    }

def fallback_response(user_text):
    return {
        "careers": [
            {
                "name": "Professional Specialist",
                "justification": "A flexible career path allowing specialization and continuous learning."
            }
        ],
        "courses": [
            {
                "name": "Foundational Skills Program",
                "description": "Covers essential professional and technical skills."
            }
        ],
        "next_steps": [
            {
                "action": "Choose a specialization",
                "details": "Select a domain and start structured learning."
            },
            {
                "action": "Practice regularly",
                "details": "Apply knowledge through projects and assignments."
            }
        ],
        "confidence_score": {
            "overall": 65,
            "explanation": "With focused learning, your career readiness can improve significantly."
        },
        "skill_gap_analysis": {
            "missing_skills": ["Practical experience", "Advanced tools", "Industry exposure"]
        },
        "upskill": build_upskill(user_text)
    }

# ==========================
# ROUTES
# ==========================
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api-status")
def api_status():
    return jsonify(AI_STATUS)

@app.route("/career", methods=["POST"])
def career():
    data = request.get_json(force=True)
    user_text = f"{data.get('interests','')} {data.get('career_goal','')}"

    try:
        prompt = f"""
You are a backend API.
Return ONLY raw JSON. No markdown, no explanations.

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

        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(prompt)
        AI_STATUS["model_responded"] = True

        # SAFE TEXT EXTRACTION
        if hasattr(response, "text") and response.text:
            text = response.text
        else:
            text = response.candidates[0].content.parts[0].text

        raw = extract_json(text)
        AI_STATUS["model_parsed"] = True
        AI_STATUS["last_error"] = None

        return jsonify({"recommendation": normalize_output(raw, user_text)})

    except Exception as e:
        print("❌ AI ERROR:", e)
        AI_STATUS["model_parsed"] = False
        AI_STATUS["last_error"] = str(e)
        return jsonify({"recommendation": fallback_response(user_text)}), 200

# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    print("🚀 Server running at http://127.0.0.1:5050")
    app.run(debug=True, port=5050)
