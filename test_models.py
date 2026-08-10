import os
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

for m in ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.5-flash", "gemini-flash-latest"]:
    try:
        response = client.models.generate_content(
            model=m,
            contents="Say hi",
        )
        print(f"Success with {m}: {response.text}")
        break
    except Exception as e:
        print(f"Failed {m}: {e}")
