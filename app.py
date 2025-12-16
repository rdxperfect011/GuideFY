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
        "description": (
            "Covers core business principles including management, strategy, analytics, "
            "entrepreneurship, and leadership skills required in modern organizations."
        ),

        "videos": [
            {
                "platform": "freeCodeCamp",
                "url": "https://www.youtube.com/watch?v=9pJ7C6J6d-8",
                "thumbnail": "https://img.youtube.com/vi/9pJ7C6J6d-8/hqdefault.jpg",
                "explanation": "Comprehensive introduction to business fundamentals and management concepts."
            },
            {
                "platform": "Simplilearn",
                "url": "https://www.youtube.com/watch?v=7Jc5EytwKzo",
                "thumbnail": "https://img.youtube.com/vi/7Jc5EytwKzo/hqdefault.jpg",
                "explanation": "Explains business strategy, planning, and organizational structure."
            },
            {
                "platform": "TEDx",
                "url": "https://www.youtube.com/watch?v=3xq8diw6k4A",
                "thumbnail": "https://img.youtube.com/vi/3xq8diw6k4A/hqdefault.jpg",
                "explanation": "Real-world insights into entrepreneurship and leadership mindset."
            }
        ],

        "platforms": [
            {
                "name": "Coursera",
                "url": "https://www.coursera.org/browse/business",
                "details": "University-level business courses from top institutions and companies.",
                "best_for": "Structured learning & certifications",
                "duration": "4–12 weeks",
                "learning_type": "Video lectures + assignments",
                "certificate": "Yes"
            },
            {
                "name": "Harvard Online",
                "url": "https://online.hbs.edu/",
                "details": "Premium business courses designed by Harvard Business School faculty.",
                "best_for": "Leadership & executive learning",
                "duration": "6–10 weeks",
                "learning_type": "Case studies + interactive learning",
                "certificate": "Yes"
            },
            {
                "name": "Google Digital Garage",
                "url": "https://learndigital.withgoogle.com/",
                "details": "Free courses focused on digital marketing, business growth, and productivity.",
                "best_for": "Digital business skills",
                "duration": "Self-paced",
                "learning_type": "Short modules",
                "certificate": "Yes"
            }
        ]
    },

    "technology": {
        "title": "Software & IT Fundamentals",
        "description": (
            "Introduces programming concepts, software development life cycle, "
            "IT systems, and problem-solving skills."
        ),

        "videos": [
            {
                "platform": "freeCodeCamp",
                "url": "https://www.youtube.com/watch?v=rfscVS0vtbw",
                "thumbnail": "https://img.youtube.com/vi/rfscVS0vtbw/hqdefault.jpg",
                "explanation": "Beginner-friendly Python programming tutorial."
            },
            {
                "platform": "Edureka",
                "url": "https://www.youtube.com/watch?v=WGJJIrtnfpk",
                "thumbnail": "https://img.youtube.com/vi/WGJJIrtnfpk/hqdefault.jpg",
                "explanation": "Explains software engineering roles and required skills."
            },
            {
                "platform": "Simplilearn",
                "url": "https://www.youtube.com/watch?v=ZxKM3DCV2kE",
                "thumbnail": "https://img.youtube.com/vi/ZxKM3DCV2kE/hqdefault.jpg",
                "explanation": "Overview of IT industry tools and technologies."
            }
        ],

        "platforms": [
            {
                "name": "Coursera",
                "url": "https://www.coursera.org/browse/computer-science",
                "details": "Computer science courses with professional certificates.",
                "best_for": "Academic + industry learning",
                "duration": "4–16 weeks",
                "learning_type": "Lectures + projects",
                "certificate": "Yes"
            },
            {
                "name": "edX",
                "url": "https://www.edx.org/learn/computer-science",
                "details": "University-backed computer science courses.",
                "best_for": "Theoretical foundations",
                "duration": "6–12 weeks",
                "learning_type": "Academic learning",
                "certificate": "Yes"
            },
            {
                "name": "Udemy",
                "url": "https://www.udemy.com/topic/programming/",
                "details": "Practical programming courses focused on skills.",
                "best_for": "Hands-on development",
                "duration": "Self-paced",
                "learning_type": "Video tutorials",
                "certificate": "Yes"
            }
        ]
    },

    "cyber": {
        "title": "Cyber Security Basics",
        "description": (
            "Introduces cyber threats, ethical hacking, network security, "
            "and defensive security practices."
        ),

        "videos": [
            {
                "platform": "Simplilearn",
                "url": "https://www.youtube.com/watch?v=U_P23SqJaDc",
                "thumbnail": "https://img.youtube.com/vi/U_P23SqJaDc/hqdefault.jpg",
                "explanation": "Introduction to cyber security concepts and threats."
            },
            {
                "platform": "NetworkChuck",
                "url": "https://www.youtube.com/watch?v=qiQR5rTSshw",
                "thumbnail": "https://img.youtube.com/vi/qiQR5rTSshw/hqdefault.jpg",
                "explanation": "Explains networking and cyber security fundamentals."
            },
            {
                "platform": "HackerSploit",
                "url": "https://www.youtube.com/watch?v=2_LbZ0PqQ_k",
                "thumbnail": "https://img.youtube.com/vi/2_LbZ0PqQ_k/hqdefault.jpg",
                "explanation": "Covers ethical hacking tools and methodologies."
            }
        ],

        "platforms": [
            {
                "name": "Coursera",
                "url": "https://www.coursera.org/browse/information-technology/security",
                "details": "Cyber security certifications and career paths.",
                "best_for": "Structured security learning",
                "duration": "4–12 weeks",
                "learning_type": "Lectures + labs",
                "certificate": "Yes"
            },
            {
                "name": "Cisco Networking Academy",
                "url": "https://www.netacad.com/",
                "details": "Industry-standard networking and security training.",
                "best_for": "Networking & cyber careers",
                "duration": "Self-paced",
                "learning_type": "Labs + simulations",
                "certificate": "Yes"
            },
            {
                "name": "TryHackMe",
                "url": "https://tryhackme.com/",
                "details": "Hands-on cyber security practice platform.",
                "best_for": "Practical hacking skills",
                "duration": "Self-paced",
                "learning_type": "Hands-on labs",
                "certificate": "Yes"
            }
        ]
    },

    "generic": {
        "title": "Career Skill Development",
        "description": (
            "Builds transferable skills like communication, problem-solving, "
            "critical thinking, and workplace readiness."
        ),

        "videos": [
            {
                "platform": "freeCodeCamp",
                "url": "https://www.youtube.com/watch?v=ZXsQAXx_ao0",
                "thumbnail": "https://img.youtube.com/vi/ZXsQAXx_ao0/hqdefault.jpg",
                "explanation": "Overview of essential professional and career skills."
            },
            {
                "platform": "TEDx",
                "url": "https://www.youtube.com/watch?v=5MgBikgcWnY",
                "thumbnail": "https://img.youtube.com/vi/5MgBikgcWnY/hqdefault.jpg",
                "explanation": "Motivational insights on career growth and mindset."
            },
            {
                "platform": "Simplilearn",
                "url": "https://www.youtube.com/watch?v=8JJ101D3knE",
                "thumbnail": "https://img.youtube.com/vi/8JJ101D3knE/hqdefault.jpg",
                "explanation": "Introduces job-ready professional skills."
            }
        ],

        "platforms": [
            {
                "name": "Coursera",
                "url": "https://www.coursera.org/",
                "details": "Wide range of career-oriented courses.",
                "best_for": "General upskilling",
                "duration": "4–8 weeks",
                "learning_type": "Online courses",
                "certificate": "Yes"
            },
            {
                "name": "Google AI",
                "url": "https://ai.google/education/",
                "details": "Free AI and digital skill resources.",
                "best_for": "AI awareness & fundamentals",
                "duration": "Self-paced",
                "learning_type": "Short modules",
                "certificate": "Yes"
            },
            {
                "name": "Kaggle",
                "url": "https://www.kaggle.com/learn",
                "details": "Hands-on learning using datasets and notebooks.",
                "best_for": "Practical learning",
                "duration": "1–3 weeks",
                "learning_type": "Hands-on practice",
                "certificate": "Yes"
            }
        ]
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

    if any(k in t for k in ["ai", "machine learning", "data", "ml"]):
        return "technology"  # 🔁 MAP AI → technology

    if any(k in t for k in ["cyber", "security", "hacking"]):
        return "cyber"

    return "generic"

def build_upskill(user_text):
    field = detect_field(user_text)

    # SAFETY FALLBACK
    if field not in UPSKILL_DB:
        field = "generic"

    return UPSKILL_DB[field]

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
                "justification": (
                    "A flexible career path that allows specialization in a chosen domain such as "
                    "technology, business, cyber security, or data analysis. This role emphasizes "
                    "continuous learning, adaptability, and skill enhancement, making it suitable "
                    "for students who are still exploring their strengths."
                )
            },
            {
                "name": "Junior Analyst / Associate",
                "justification": (
                    "An entry-level role focused on analyzing data, processes, or systems to support "
                    "decision-making. This role helps build analytical thinking, domain knowledge, "
                    "and real-world industry exposure."
                )
            },
            {
                "name": "Technical Support / Operations Executive",
                "justification": (
                    "Involves supporting systems, tools, or business operations. This role is ideal "
                    "for developing problem-solving skills, understanding workflows, and gaining "
                    "hands-on experience in a professional environment."
                )
            }
        ],

        "courses": [
            {
                "name": "Foundational Skills Program",
                "description": (
                    "Covers essential technical and professional skills such as basic programming, "
                    "communication, logical thinking, and digital literacy. This program helps "
                    "students build a strong base applicable across multiple career paths."
                )
            },
            {
                "name": "Introduction to Technology & Systems",
                "description": (
                    "Provides an overview of how modern software systems, networks, and applications "
                    "work together. Useful for students entering IT, analytics, or technical roles."
                )
            },
            {
                "name": "Professional Communication & Workplace Skills",
                "description": (
                    "Focuses on communication, teamwork, presentation skills, and workplace ethics, "
                    "which are critical for career growth in any industry."
                )
            }
        ],

        "next_steps": [
            {
                "action": "Identify your core interest",
                "details": (
                    "Choose one primary domain such as software, data, business, or cyber security "
                    "based on your interest and aptitude."
                )
            },
            {
                "action": "Build strong fundamentals",
                "details": (
                    "Start with beginner-level courses and focus on understanding core concepts "
                    "before moving to advanced topics."
                )
            },
            {
                "action": "Apply learning practically",
                "details": (
                    "Work on mini-projects, case studies, or hands-on labs to convert theoretical "
                    "knowledge into practical skills."
                )
            },
            {
                "action": "Track progress and improve",
                "details": (
                    "Regularly evaluate your learning progress, identify skill gaps, and refine "
                    "your learning strategy accordingly."
                )
            }
        ],

        "confidence_score": {
            "overall": 68,
            "explanation": (
                "Your inputs indicate good potential across multiple domains. With focused learning, "
                "hands-on practice, and consistent effort, your career readiness can improve "
                "significantly over time."
            )
        },

        "skill_gap_analysis": {
            "missing_skills": [
                "Practical hands-on experience",
                "Advanced domain-specific tools",
                "Industry exposure",
                "Project-based learning"
            ]
        }
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

    fb = fallback_response(user_text)
    fb["upskill"] = build_upskill(user_text)

    return jsonify({"recommendation": fb}), 200


# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    print("🚀 Server running at http://127.0.0.1:5050")
    app.run(debug=True, port=5050)
