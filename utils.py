import os
import json
import requests

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
                "url": f"https://www.youtube.com/watch?{video_id}",
                "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                "explanation": "Recommended based on your interest and beginner relevance."
            })

        return videos

    except Exception as e:
        print("❌ YouTube API Error:", e)
        return []

def extract_json(text):
    """
    Extracts and parses JSON from AI response text.
    Handles cases where AI adds extra text or code blocks.
    """
    # Clean up markdown code blocks if present
    text = text.strip()
    if text.startswith("```json"):
        text = text[len("```json"):]
    if text.endswith("```"):
        text = text[:-len("```")]
    text = text.strip()

    start = text.find("{")
    end = text.rfind("}") + 1

    if start == -1 or end == -1:
        raise ValueError("No JSON object found")

    return json.loads(text[start:end])

def detect_field(text):
    """
    Detects the career field based on keywords in the provided text.
    """
    t = text.lower()

    # Field mapping for easier maintenance
    field_keywords = {
        "ai_ml": ["artificial intelligence", "ai", "machine learning", "ml", "deep learning", "neural network"],
        "technology": ["information technology", "computer science", "software", "programming", "developer", "coding", "data science"],
        "cyber": ["cyber security", "network security", "hacking"],
        "medical": ["medical", "medicine", "healthcare", "doctor", "nurse", "mbbs", "pharmacy", "hospital"],
        "politics": ["politics", "political science", "public policy", "governance", "civil services", "upsc", "law"],
        "business": ["business", "management", "commerce", "mba", "entrepreneur"],
        "agriculture": ["agriculture", "farming", "crop", "soil", "agribusiness"]
    }

    for field, keywords in field_keywords.items():
        if any(k in t for k in keywords):
            return field

    return "generic"

def load_upskill_db():
    """
    Loads the upskill database from the JSON file.
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, "data", "upskill_db.json")
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading UPSKILL_DB: {e}")
        return {}

def build_upskill(user_text, db=None):
    """
    Builds the upskill section of the response by selecting the appropriate field
    from the database and optionally fetching YouTube videos.
    """
    if db is None:
        db = load_upskill_db()
        
    field = detect_field(user_text)
    base = db.get(field, db.get("generic", {})).copy()

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

    # Fetch LIMITED YouTube videos
    yt_videos = fetch_youtube_videos(yt_query, max_results=3)

    # Use YouTube ONLY if valid videos exist
    if yt_videos:
        base["videos"] = yt_videos
    else:
        # Safety: keep static curated videos from DB (already in 'base')
        base["videos"] = base.get("videos", [])[:3]

    return base

def normalize_output(raw, user_text, db=None):
    """
    Ensures consistent API response format.
    """
    return {
        "careers": raw.get("careers", []),
        "courses": raw.get("courses", []),
        "next_steps": raw.get("next_steps", []),
        "confidence_score": raw.get("confidence_score", {}),
        "skill_gap_analysis": raw.get("skill_gap_analysis", {}),
        "upskill": build_upskill(user_text, db)
    }

def fallback_response():
    """
    Used when AI fails. Guarantees meaningful output.
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
