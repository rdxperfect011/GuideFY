import os, json
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials

# Load .env variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SHEET_NAME = os.getenv("SHEET_NAME", "CareerGuidanceDB")
GOOGLE_CREDS_PATH = "credentials/google-credentials.json"

if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY")

# Setup Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Flask app
app = Flask(__name__, static_folder="static", static_url_path="")

# Google Sheets (optional)
sheet = None
if os.path.exists(GOOGLE_CREDS_PATH):
    try:
        creds = Credentials.from_service_account_file(
            GOOGLE_CREDS_PATH,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        sheet = gspread.authorize(creds).open(SHEET_NAME).sheet1
    except Exception as e:
        print("⚠️ Google Sheets setup failed:", e)

# Routes
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/career", methods=["POST"])
def career():
    data = request.get_json()
    name = data.get("name", "Student")

    prompt = f"""
    You are a career guidance expert. A student named {name} provided:
    Interests: {data.get('interests')}
    Strengths: {data.get('strengths')}
    Subjects: {data.get('preferred_subjects')}
    Career goal: {data.get('career_goal')}
    
    Suggest 3 career paths (with justification), 3–5 recommended courses, and 3 next steps.
    Format output as JSON with keys: careers, courses, next_steps.
    Each item should include: name/justification, name/description, and action/details respectively.
    """

    try:
        model = genai.GenerativeModel("models/gemini-2.5-pro")
        res = model.generate_content(prompt).text.strip()
        if "```" in res:
            res = res.split("```")[1].strip("json\n")
        result = normalize_output(json.loads(res))
    except Exception as e:
        return jsonify({"error": "Gemini API failed", "details": str(e)}), 500

    # Save to Google Sheet
    if sheet:
        try:
            sheet.append_row([
                name, data.get("email", ""),
                data.get("interests"), data.get("strengths"),
                data.get("preferred_subjects"), data.get("career_goal"),
                json.dumps(result)
            ])
        except Exception as e:
            print("⚠️ Google Sheet write failed:", e)

    return jsonify({"recommendation": result})

# Format Gemini output
def normalize_output(raw):
    def clean(t): return t.strip().capitalize() if isinstance(t, str) and t.strip() else "Not specified"
    def get(v, *k): return next((v[i] for i in k if isinstance(v, dict) and v.get(i)), None)

    return {
        "careers": [{"name": clean(get(c, "name", "title")), "justification": clean(c.get("justification"))} for c in raw.get("careers", [])],
        "courses": [{"name": clean(get(c, "name", "title")), "description": clean(c.get("description"))} for c in raw.get("courses", [])],
        "next_steps": [{"action": clean(get(s, "action", "step")), "details": clean(s.get("details", ""))} for s in raw.get("next_steps", [])]
    }

if __name__ == "__main__":
    print("🚀 Server running at http://127.0.0.1:5050")
    app.run(host="0.0.0.0", port=5050, debug=True)
