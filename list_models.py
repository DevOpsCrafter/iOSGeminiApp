import google.generativeai as genai
import os

api_key = "AIzaSyDeB4QxXqF6wiX6NqgNygOhao1JNfE43HE"
genai.configure(api_key=api_key)

print("Available models:")
for model in genai.list_models():
    print(f"  - {model.name}")
