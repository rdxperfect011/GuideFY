import os
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore", message="You are using a Python version 3.9 past its end of life")

from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Skipping verification as GEMINI_API_KEY is not set.")
    exit(0)

try:
    client = genai.Client(api_key=api_key)
    print("Client initialized successfully.")
except Exception as e:
    print(f"Failed to initialize client: {e}")
    exit(1)
