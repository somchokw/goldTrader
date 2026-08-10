import os
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

try:
    models = client.models.list()
    for model in models:
        print(f"Model: {model.name}")
except Exception as e:
    print(f"Error listing models: {e}")
