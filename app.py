import os
import json
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import google.generativeai as genai
import requests

# ENVIRONMENT & AI CONFIGURATION
# Load variables from .env file
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


# UPSKILL DATABASE (STATIC FALLBACK CONTENT)

# This database is used even when AI fails
# It ensures the system always returns useful output
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
                "details": "Premium business courses by Harvard faculty.",
                "best_for": "Leadership & executive learning",
                "duration": "6–10 weeks",
                "learning_type": "Case studies + interactive learning",
                "certificate": "Yes"
            },
            {
                "name": "Google Digital Garage",
                "url": "https://learndigital.withgoogle.com/",
                "details": "Free digital business and marketing courses.",
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
                "details": "Computer science courses with certificates.",
                "best_for": "Academic + industry learning",
                "duration": "4–16 weeks",
                "learning_type": "Lectures + projects",
                "certificate": "Yes"
            },
            {
                "name": "edX",
                "url": "https://www.edx.org/learn/computer-science",
                "details": "University-backed CS courses.",
                "best_for": "Theoretical foundations",
                "duration": "6–12 weeks",
                "learning_type": "Academic learning",
                "certificate": "Yes"
            },
            {
                "name": "Udemy",
                "url": "https://www.udemy.com/topic/generative-ai/",
                "details": "Skill-based programming courses.",
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
                "explanation": "Introduction to cyber security concepts."
            },
            {
                "platform": "NetworkChuck",
                "url": "https://www.youtube.com/watch?v=qiQR5rTSshw",
                "thumbnail": "https://img.youtube.com/vi/qiQR5rTSshw/hqdefault.jpg",
                "explanation": "Networking and cyber fundamentals."
            },
            {
                "platform": "HackerSploit",
                "url": "https://www.youtube.com/watch?v=2_LbZ0PqQ_k",
                "thumbnail": "https://img.youtube.com/vi/2_LbZ0PqQ_k/hqdefault.jpg",
                "explanation": "Ethical hacking tools and methods."
            }
        ],
        "platforms": [
            {
                "name": "Coursera",
                "url": "https://www.coursera.org/browse/information-technology/security",
                "details": "Cyber security career certificates.",
                "best_for": "Structured security learning",
                "duration": "4–12 weeks",
                "learning_type": "Lectures + labs",
                "certificate": "Yes"
            },
            {
                "name": "Cisco Networking Academy",
                "url": "https://www.netacad.com/",
                "details": "Industry-standard networking training.",
                "best_for": "Networking careers",
                "duration": "Self-paced",
                "learning_type": "Labs + simulations",
                "certificate": "Yes"
            },
            {
                "name": "TryHackMe",
                "url": "https://tryhackme.com/",
                "details": "Hands-on cyber security practice.",
                "best_for": "Practical hacking skills",
                "duration": "Self-paced",
                "learning_type": "Hands-on labs",
                "certificate": "Yes"
            }
        ]
    },
    "agriculture": {
    "title": "Agriculture & Agri-Technology",
    "description": (
        "Focuses on modern farming techniques, crop management, "
        "agri-technology, sustainable agriculture, and agribusiness skills."
    ),
    "videos": [
        {
            "platform": "YouTube - Krishi Jagran",
            "url": "https://www.youtube.com/watch?v=Q9ZJYcY6ZrA",
            "thumbnail": "https://img.youtube.com/vi/Q9ZJYcY6ZrA/hqdefault.jpg",
            "explanation": "Introduction to modern agriculture and farming techniques."
        },
        {
            "platform": "YouTube - ICAR",
            "url": "https://www.youtube.com/watch?v=R9pPj5V1x1I",
            "thumbnail": "https://img.youtube.com/vi/R9pPj5V1x1I/hqdefault.jpg",
            "explanation": "Scientific crop production and soil management."
        },
        {
            "platform": "YouTube - Agritech",
            "url": "https://www.youtube.com/watch?v=Y5ZpQfW9k8g",
            "thumbnail": "https://img.youtube.com/vi/Y5ZpQfW9k8g/hqdefault.jpg",
            "explanation": "Use of technology and AI in agriculture."
        }
    ],
    "platforms": [
        {
            "name": "Coursera",
            "url": "https://www.coursera.org/browse/life-sciences/agriculture",
            "details": "Agriculture and food production courses by universities.",
            "best_for": "Agri fundamentals & certification",
            "duration": "4–10 weeks",
            "learning_type": "Online courses",
            "certificate": "Yes"
        },
        {
            "name": "SWAYAM (Govt of India)",
            "url": "https://swayam.gov.in/",
            "details": "Free government-certified agriculture courses.",
            "best_for": "Indian agriculture education",
            "duration": "Self-paced",
            "learning_type": "Video lectures",
            "certificate": "Yes"
        }
    ]
},
"medical": {
    "title": "Medical & Healthcare Careers",
    "description": (
        "Focuses on healthcare, medicine, diagnostics, patient care, "
        "medical technology, and allied health professions."
    ),
    "videos": [
        {
            "platform": "YouTube",
            "url": "https://www.youtube.com/watch?v=3UczbYv0p6Q",
            "thumbnail": "https://img.youtube.com/vi/3UczbYv0p6Q/hqdefault.jpg",
            "explanation": "Overview of medical and healthcare career options."
        },
        {
            "platform": "YouTube",
            "url": "https://www.youtube.com/watch?v=Z1w2vQ9SxRA",
            "thumbnail": "https://img.youtube.com/vi/Z1w2vQ9SxRA/hqdefault.jpg",
            "explanation": "Explains roles like doctor, nurse, pharmacist, and technician."
        },
        {
            "platform": "YouTube",
            "url": "https://www.youtube.com/watch?v=kF0ZqG7R7pA",
            "thumbnail": "https://img.youtube.com/vi/kF0ZqG7R7pA/hqdefault.jpg",
            "explanation": "Introduction to modern healthcare and medical technology."
        }
    ],
    "platforms": [
        {
            "name": "Coursera",
            "url": "https://www.coursera.org/browse/health",
            "details": "Medical and healthcare courses from universities.",
            "best_for": "Healthcare fundamentals",
            "duration": "4–12 weeks",
            "learning_type": "Video + assessments",
            "certificate": "Yes"
        },
        {
            "name": "WHO Open Learning",
            "url": "https://www.who.int/careers",
            "details": "Public health and medical awareness courses.",
            "best_for": "Public health & awareness",
            "duration": "Self-paced",
            "learning_type": "Short modules",
            "certificate": "Yes"
        },
        {
            "name": "Khan Academy Medicine",
            "url": "https://www.khanacademy.org/science/health-and-medicine",
            "details": "Free medical science explanations.",
            "best_for": "Medical basics",
            "duration": "Self-paced",
            "learning_type": "Concept videos",
            "certificate": "No"
        }
    ]
},
"ai_ml": {
    "title": "Artificial Intelligence & Machine Learning",
    "description": (
        "Focuses on AI concepts, machine learning algorithms, data handling, "
        "model building, and real-world AI applications."
    ),
    "videos": [
        {
            "platform": "freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=JMUxmLyrhSk",
            "thumbnail": "https://img.youtube.com/vi/JMUxmLyrhSk/hqdefault.jpg",
            "explanation": "Complete AI roadmap and fundamentals."
        },
        {
            "platform": "Simplilearn",
            "url": "https://www.youtube.com/watch?v=ukzFI9rgwfU",
            "thumbnail": "https://img.youtube.com/vi/ukzFI9rgwfU/hqdefault.jpg",
            "explanation": "Machine Learning explained with examples."
        },
        {
            "platform": "Krish Naik",
            "url": "https://www.youtube.com/watch?v=GwIo3gDZCVQ",
            "thumbnail": "https://img.youtube.com/vi/GwIo3gDZCVQ/hqdefault.jpg",
            "explanation": "AI/ML career roadmap for students."
        }
    ],
    "platforms": [
        {
            "name": "Coursera",
            "url": "https://www.coursera.org/browse/data-science/machine-learning",
            "details": "Industry-recognized AI/ML courses.",
            "best_for": "Strong AI foundation",
            "duration": "6–12 weeks",
            "learning_type": "Projects + theory",
            "certificate": "Yes"
        },
        {
            "name": "Google AI",
            "url": "https://ai.google/education/",
            "details": "Free AI learning by Google.",
            "best_for": "AI fundamentals",
            "duration": "Self-paced",
            "learning_type": "Short modules",
            "certificate": "Yes"
        }
    ]
},
"politics": {
    "title": "Political Science & Public Policy",
    "description": (
        "Covers political systems, governance, public administration, "
        "policy-making, international relations, and civic leadership."
    ),
    "videos": [
        {
            "platform": "YouTube - StudyIQ IAS",
            "url": "https://www.youtube.com/watch?v=CRP_o8aZmRw",
            "thumbnail": "https://img.youtube.com/vi/CRP_o8aZmRw/maxresdefault.jpg",
            "explanation": "Political Science as a Master Science || Aristotle || PSIR || Shubhra Ranjan."
        },
        {
            "platform": "YouTube - StudyIQ IAS:",
            "url": "https://www.youtube.com/watch?v=5HOiHKPFTGs",
            "thumbnail": "https://img.youtube.com/vi/5HOiHKPFTGs/maxresdefault.jpg",
            "explanation": "Complete Indian Polity for UPSC CSE 2025-26 | StudyIQ | Shashank Tyagi."
        },
        {
            "platform": "YouTube - CrashCourse",
            "url": "https://www.youtube.com/watch?v=qRdHKmj4-iE",
            "thumbnail": "https://img.youtube.com/vi/qRdHKmj4-iE/maxresdefault.jpg",
            "explanation": "Understanding Geopolitics and International Relations Roots."
        }
    ],
    "platforms": [
        {
            "name": "Coursera",
            "url": "https://www.coursera.org/browse/social-sciences/political-science",
            "details": "Political science and international relations courses.",
            "best_for": "Policy & governance studies",
            "duration": "4–12 weeks",
            "learning_type": "University courses",
            "certificate": "Yes"
        },
        {
            "name": "edX",
            "url": "https://www.edx.org/learn/political-science",
            "details": "Public policy and government programs from universities.",
            "best_for": "Academic political studies",
            "duration": "6–10 weeks",
            "learning_type": "Academic learning",
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
                "platform": "YouTube - Vishal Sharma",
                "url": "https://youtu.be/NTxBP4bFrBA?si=Z-KQNt_1SbzBnSOn",
                "thumbnail": "https://img.youtube.com/vi/NTxBP4bFrBA/maxresdefault.jpg",
                "explanation": "Essential professional skills overview."
            },
            {
                "platform": "TEDx",
                "url": "https://www.youtube.com/watch?v=5MgBikgcWnY",
                "thumbnail": "https://img.youtube.com/vi/5MgBikgcWnY/hqdefault.jpg",
                "explanation": "Career growth mindset."
            },
            {
                "platform": "YouTube - Skillopedia",
                "url": "https://www.youtube.com/watch?v=4-R1EHKmano",
                "thumbnail": "https://img.youtube.com/vi/4-R1EHKmano/maxresdefault.jpg",
                "explanation": "Job-ready professional skills."
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
                "name": "LinkedIn Learning",
                "url": "https://www.linkedin.com/learning/",
                "details": "Professional-focused courses",
                "best_for": "Career and Soft Skills",
                "duration": "Self-paced",
                "learning_type": "Short modules",
                "certificate": "Yes"
            },
            {
                "name": "Brilliant",
                "url": "https://www.brilliant.org/",
                "details": "Interactive problem-solving in math, logic, science",
                "best_for": "Practical learning",
                "duration": "1–3 weeks",
                "learning_type": "Hands-on practice",
                "certificate": "Yes"
            }
        ]
    }
}

# HELPER FUNCTIONS

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def fetch_youtube_videos(query, max_results=3):
    """
    Fetches relevant YouTube videos using YouTube Data API.
    Returns clean, usable video data.
    """
    if not YOUTUBE_API_KEY:
        return []

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
        "videoDuration": "medium"
    }

    try:
        res = requests.get(url, params=params, timeout=5)
        data = res.json()

        videos = []
        for item in data.get("items", []):
            title = item["snippet"]["title"].lower()

            # simple filtering
            if any(x in title for x in ["shorts", "funny", "meme"]):
                continue

            video_id = item["id"]["videoId"]
            videos.append({
                "platform": "YouTube",
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                "explanation": "Recommended based on your interest and beginner relevance."
            })

        return videos

    except Exception as e:
        print("❌ YouTube API Error:", e)
        return []
    
# Purpose : Safely extract and parse JSON data from AI response text
def extract_json(text):
    """
    Extracts and parses JSON from AI response text.
    Handles cases where AI adds extra text or code blocks.
    """
    text = text.replace("```json", "").replace("```", "").strip()

    start = text.find("{")
    end = text.rfind("}") + 1

    if start == -1 or end == -1:
        raise ValueError("No JSON object found")

    return json.loads(text[start:end])

#Fallback field detection based on keywords
def detect_field(text):
    t = text.lower()

    # AI / ML SPECIALIZATION
    if any(k in t for k in [
        "artificial intelligence", "ai",
        "machine learning", "ml",
        "deep learning", "neural network"
    ]):
        return "ai_ml"
    
    # TECHNOLOGY
    if any(k in t for k in [
        "information technology", "computer science",
        "software", "programming", "developer", "coding",
        "ai", "machine learning", "ml", "data science"
    ]):
        return "technology"
        return "ai_ml"
    # CYBER SECURITY
    if any(k in t for k in [
        "cyber security", "network security", "hacking"
    ]):
        return "cyber"

    # MEDICAL / HEALTHCARE
    if any(k in t for k in [
        "medical", "medicine", "healthcare", "doctor",
        "nurse", "mbbs", "pharmacy", "hospital"
    ]):
        return "medical"

    # POLITICS / PUBLIC POLICY
    if any(k in t for k in [
        "politics", "political science", "public policy",
        "governance", "civil services", "upsc", "law"
    ]):
        return "politics"

    # BUSINESS
    if any(k in t for k in [
        "business", "management", "commerce", "mba", "entrepreneur"
    ]):
        return "business"

    # AGRICULTURE
    if any(k in t for k in [
        "agriculture", "farming", "crop", "soil", "agribusiness"
    ]):
        return "agriculture"

    return "generic"

#YouTube Filtering and integration

def build_upskill(user_text):
    field = detect_field(user_text)
    base = UPSKILL_DB.get(field, UPSKILL_DB["generic"]).copy()

    # YouTube search queries
    query_map = {
        "ai_ml": "artificial intelligence machine learning career roadmap beginner",
        "technology": "information technology career roadmap beginner",
        "cyber": "cyber security career roadmap beginner",
        "medical": "medical healthcare careers for students",
        "politics": "political science public policy careers",
        "business": "business management career guide",
        "agriculture": "agriculture technology careers beginner",
        "generic": "career skills for students"
    }

    yt_query = query_map.get(field, "career guidance for students")

    # 🔒 Fetch LIMITED YouTube videos
    yt_videos = fetch_youtube_videos(yt_query, max_results=3)

    # ✅ Use YouTube ONLY if valid videos exist
    if yt_videos and len(yt_videos) >= 1:
        base["videos"] = yt_videos[:3]
    else:
        # Safety: keep static curated videos
        base["videos"] = base.get("videos", [])[:3]

    return base

def normalize_output(raw, user_text):
    """
    Ensures consistent API response format.
    """
    return {
        "careers": raw.get("careers", []),
        "courses": raw.get("courses", []),
        "next_steps": raw.get("next_steps", []),
        "confidence_score": raw.get("confidence_score", {}),
        "skill_gap_analysis": raw.get("skill_gap_analysis", {}),
        "upskill": build_upskill(user_text)
    }

def fallback_response(user_text):
    """
    Used when AI fails.
    Guarantees meaningful output.
    """
    return {
        "careers": [
            {
                "name": "Professional Specialist",
                "justification": "Flexible role allowing specialization with continuous learning."
            },
            {
                "name": "Junior Analyst / Associate",
                "justification": "Entry-level analytical role building real-world exposure."
            },
            {
                "name": "Technical Support / Operations Executive",
                "justification": "Hands-on operational role developing problem-solving skills."
            }
        ],
        "courses": [
            {
                "name": "Foundational Skills Program",
                "description": "Builds technical and professional fundamentals."
            },
            {
                "name": "Introduction to Technology & Systems",
                "description": "Explains how modern IT systems work."
            },
            {
                "name": "Professional Communication Skills",
                "description": "Improves workplace and teamwork skills."
            }
        ],
        "next_steps": [
            {"action": "Choose a domain", "details": "Identify your strongest interest area."},
            {"action": "Learn fundamentals", "details": "Start with beginner-friendly courses."},
            {"action": "Practice", "details": "Apply learning using projects."}
        ],
        "confidence_score": {
            "overall": 68,
            "explanation": "Good potential with scope for improvement."
        },
        "skill_gap_analysis": {
            "missing_skills": [
                "Hands-on experience",
                "Advanced tools",
                "Industry exposure"
            ]
        }
    }

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
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(prompt)

        AI_STATUS["model_responded"] = True

        text = response.text if hasattr(response, "text") else response.candidates[0].content.parts[0].text
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

# APPLICATION ENTRY POINT
if __name__ == "__main__":
    print("Server running at http://127.0.0.1:5050")
    app.run(debug=True, port=5050, threaded=True)
