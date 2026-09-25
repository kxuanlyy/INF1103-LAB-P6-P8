import os
from google import genai
from dotenv import load_dotenv

load_dotenv("apikey.env")

api_key = os.getenv("GEMINI_API_KEY")

if api_key is None:
    print("ERROR: API key was not found.")
    exit()

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents="give me the opening sentnece to shrek movie"
    )

    print(response.text)
    print("Am i failing????")

except Exception as e:
    print("Gemini API returned an error:")
    print(e)