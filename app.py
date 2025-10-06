import os
import json
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.message import EmailMessage

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_CREDS_PATH = os.path.join(os.path.dirname(__file__), 'credentials/google-credentials.json')
SHEET_NAME = os.getenv('SHEET_NAME', 'CareerGuidanceDB')
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_SMTP_HOST = os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')
EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', 587))

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in environment variables.")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__, static_folder='static', static_url_path='')

# Google Sheets setup (optional)
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
if os.path.exists(GOOGLE_CREDS_PATH):
    creds = Credentials.from_service_account_file(GOOGLE_CREDS_PATH, scopes=scope)
    gclient = gspread.authorize(creds)
    try:
        sheet = gclient.open(SHEET_NAME).sheet1
    except Exception:
        spreadsheet = gclient.create(SHEET_NAME)
        sheet = spreadsheet.sheet1
else:
    sheet = None
    print("Warning: Google credentials not found. Sheets integration disabled.")

# Routes
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/career', methods=['POST'])
def career():
    data = request.get_json()
    name = data.get('name', 'Student')
    email = data.get('email', '')
    interests = data.get('interests', '')
    strengths = data.get('strengths', '')
    subjects = data.get('preferred_subjects', '')
    goal = data.get('career_goal', '')

    prompt = (
        f"You are a career guidance assistant. A diploma computer engineering student named {name} provided the following:\n"
        f"Interests: {interests}\nStrengths: {strengths}\nSubjects: {subjects}\nCareer goal: {goal}\n"
        "Provide 3 career paths with short justification, 3-5 recommended courses, and 3 practical next steps. "
        "Format your response *only* as a raw JSON object with keys: careers, courses, next_steps. Do not include any other text or markdown formatting."
    )

    # Gemini API call (Corrected)
    try:
        model = genai.GenerativeModel("models/gemini-2.5-pro")  # Use a supported model name from your list
        response = model.generate_content(prompt)
        text = response.text

        # Clean the response before parsing JSON
        if '```' in text:
            text = text.split('```')[1].strip('json\n')

        try:
            recommendation = json.loads(text)
        except json.JSONDecodeError:
            print(f"Failed to decode JSON from Gemini response: {text}")
            recommendation = {"error": "Could not parse the recommendation.", "raw_response": text}
    
    except Exception as e:
        print("Gemini API call failed:", e)
        return jsonify({
            'error': 'Gemini request failed. See server logs for details.',
            'details': str(e)
        }), 500

    # Save to Google Sheets
    try:
        if sheet:
            row = [name, email, interests, strengths, subjects, goal, json.dumps(recommendation)]
            sheet.append_row(row)
    except Exception as e:
        print("Google Sheets append failed:", e)

    # Send email
    if EMAIL_ADDRESS and EMAIL_PASSWORD and email:
        try:
            msg = EmailMessage()
            msg['Subject'] = 'Your Career Recommendations'
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = email
            
            # Format the body to be more readable in an email
            body_text = f"Hello {name},\n\nHere are your personalized career guidance recommendations:\n\n"
            if "careers" in recommendation:
                for career_item in recommendation.get("careers", []):
                    body_text += f"Career Path: {career_item.get('path', 'N/A')}\n"
                    body_text += f"Justification: {career_item.get('justification', 'N/A')}\n\n"
            
            if "courses" in recommendation:
                body_text += "Recommended Courses:\n"
                for course in recommendation.get("courses", []):
                    body_text += f"- {course}\n"
                body_text += "\n"

            if "next_steps" in recommendation:
                body_text += "Practical Next Steps:\n"
                for step in recommendation.get("next_steps", []):
                    body_text += f"- {step}\n"
            
            body_text += "\nBest of luck!"
            msg.set_content(body_text)

            with smtplib.SMTP(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT) as smtp:
                smtp.starttls()
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                smtp.send_message(msg)
        except Exception as e:
            print("Email sending failed:", e)

    return jsonify({'recommendation': recommendation})
if __name__ == '__main__':
    print("Server starting on http://127.0.0.1:5050 ...")
    app.run(host='0.0.0.0', port=5050, debug=True)