from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv(
    "GEMINI_API_KEY"
)

print(
    "API KEY FOUND:",
    bool(api_key)
)

client = genai.Client(
    api_key=api_key
)

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="What is Spotify?"
)

print("\n===== GEMINI RESPONSE =====\n")

print(response.text)