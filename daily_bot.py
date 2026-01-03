import os
import time
import requests
import google.generativeai as genai
import random
import urllib.parse

# Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN")
IG_USER_ID = os.environ.get("IG_USER_ID")

def generate_astro_content():
    """Generates a prompt and caption using Gemini."""
    print("✨ Connecting to Gemini...")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = """
    You are 'Astroboli', a mystical AI astrologer. 
    1. Generate a visually descriptive image prompt for today's daily horoscope or cosmic energy. It should be mystical, ethereal, and artistic. 
    2. Write an engaging Instagram caption for this image.
    3. Provide 30 relevant hashtags.
    
    Output format:
    IMAGE_PROMPT: [The image prompt]
    CAPTION: [The caption]
    HASHTAGS: [The hashtags]
    """
    
    response = model.generate_content(prompt)
    text = response.text
    
    # Simple parsing
    image_prompt = text.split("IMAGE_PROMPT:")[1].split("CAPTION:")[0].strip()
    caption_part = text.split("CAPTION:")[1].split("HASHTAGS:")[0].strip()
    hashtags = text.split("HASHTAGS:")[1].strip()
    
    full_caption = f"{caption_part}\n\n{hashtags}"
    
    return image_prompt, full_caption

def get_image_url(prompt):
    """Generates an image URL from Pollinations.ai."""
    print(f"🎨 Generating image for: {prompt[:50]}...")
    encoded_prompt = urllib.parse.quote(prompt)
    # Pollinations URL (Seed ensures consistency if we need to retry, but random is fine)
    seed = random.randint(1, 1000000)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&seed={seed}&nologo=true&model=flux"
    return image_url

def post_to_instagram(image_url, caption):
    """Posts the image to Instagram via Graph API."""
    print("🚀 Posting to Instagram...")
    
    # 1. Create Media Container
    url_container = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }
    
    r = requests.post(url_container, data=payload)
    print(f"Container Response: {r.text}")
    
    if r.status_code != 200:
        raise Exception("Failed to create media container")
        
    creation_id = r.json().get("id")
    
    # Wait for processing
    print("⏳ Waiting for Instagram to process the image...")
    time.sleep(10)
    
    # 2. Publish Media
    url_publish = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/media_publish"
    payload_publish = {
        "creation_id": creation_id,
        "access_token": IG_ACCESS_TOKEN
    }
    
    r_pub = requests.post(url_publish, data=payload_publish)
    print(f"Publish Response: {r_pub.text}")
    
    if r_pub.status_code == 200:
        print("✅ Successfully posted to Instagram!")
    else:
        raise Exception("Failed to publish media")

def main():
    if not all([GEMINI_API_KEY, IG_ACCESS_TOKEN, IG_USER_ID]):
        print("❌ Error: Missing Environment Variables (GEMINI_API_KEY, IG_ACCESS_TOKEN, IG_USER_ID)")
        exit(1)

    try:
        # 1. Generate Content
        prompt, caption = generate_astro_content()
        print(f"📝 Prompt: {prompt}")
        
        # 2. Get Image URL
        image_url = get_image_url(prompt)
        print(f"🖼️ Image URL: {image_url}")
        
        # 3. Post
        post_to_instagram(image_url, caption)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
