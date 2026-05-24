from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv(
    "GROQ_API_KEY"
)

print(
    "API KEY FOUND:",
    bool(api_key)
)

client = Groq(
    api_key=api_key
)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": "What is Spotify?"
        }
    ]
)

print("\n===== GROQ RESPONSE =====\n")

print(
    response.choices[0].message.content
)