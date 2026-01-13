import google.generativeai as genai
import os

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("GEMINI_API_KEY is not set. Set it in your environment or add it to a local .env file (do NOT commit).")

genai.configure(api_key=api_key)

print("Available models:")
for model in genai.list_models():
    print(f"  - {model.name}")
