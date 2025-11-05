import os, json, smtplib
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
from email.message import EmailMessage

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
SHEET_NAME = os.getenv('SHEET_NAME', 'CareerGuidanceDB')
GOOGLE_CREDS_PATH = 'credentials/google-credentials.json'

# Safety checks
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing in environment variables")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Flask
app = Flask(__name__, static_folder='static', static_url_path='')

# Google Sheets setup (optional)
sheet = None
try:
    if os.path.exists(GOOGLE_CREDS_PATH):
        creds = Credentials.from_service_account_file(
            GOOGLE_CREDS_PATH,
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        )
        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).sheet1
    else:
        print("⚠️ Google credentials not found — skipping Sheets integration.")
except Exception as e:
    print("Google Sheets setup failed:", e)

# Normalize Gemini response 
def normalize_output(raw):
    """Ensures Gemini output uses consistent keys and fills missing fields cleanly."""
    def get(v, *keys):
        for k in keys:
            if isinstance(v, dict) and v.get(k):
                return v[k]
        return None

    def clean_text(text):
        return text.strip().capitalize() if isinstance(text, str) and text.strip() else "Not specified"

    return {
        "careers": [
            {
                "name": clean_text(get(c, "name", "title")),
                "justification": clean_text(c.get("justification"))
            } for c in raw.get("careers", [])
        ],
        "courses": [
            {
                "name": clean_text(get(c, "name", "title")),
                "description": clean_text(c.get("description"))
            } for c in raw.get("courses", [])
        ],
        "next_steps": [
            {
                "action": clean_text(get(s, "action", "step")),
                "details": clean_text(s.get("details"))
            } if isinstance(s, dict)
            else {"action": clean_text(s), "details": ""}
            for s in raw.get("next_steps", [])
        ]
    }

# Routes 
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/career', methods=['POST'])
def career():
    data = request.get_json()
    name = data.get('name', 'Student')
    email = data.get('email', '')
    prompt = (
    f"You are a career guidance expert. A student named {name} provided:\n"
    f"Interests: {data.get('interests')}\nStrengths: {data.get('strengths')}\n"
    f"Subjects: {data.get('preferred_subjects')}\nCareer goal: {data.get('career_goal')}\n\n"
    "Suggest 3 career paths (with justification), 3–5 recommended courses, and 3 next steps.\n"
    "Each career must have keys: 'name' and 'justification'.\n"
    "Each course must have keys: 'name' and 'description'.\n"
    "Each next step must have keys: 'action' and 'details'.\n"
    "Return output as pure JSON with keys: careers, courses, next_steps — no markdown, no explanations.\n"
    "If any field has no value, include it as an empty string rather than omitting it."
)

    try:
        model = genai.GenerativeModel("models/gemini-2.5-pro")
        response = model.generate_content(prompt)
        text = response.text.strip()
        if '```' in text: text = text.split('```')[1].strip('json\n')
        recommendation = normalize_output(json.loads(text))
    except Exception as e:
        print("Gemini API call failed:", e)
        return jsonify({'error': 'Gemini API error', 'details': str(e)}), 500

    # Save to Google Sheet
    try:
        if sheet:
            sheet.append_row([
                name, email,
                data.get('interests'), data.get('strengths'),
                data.get('preferred_subjects'), data.get('career_goal'),
                json.dumps(recommendation)
            ])
    except Exception as e:
        print("Google Sheets append failed:", e)
    return jsonify({'recommendation': recommendation})

if __name__ == '__main__':
    print("Server running → http://127.0.0.1:5050")
    app.run(host='0.0.0.0', port=5050, debug=True)