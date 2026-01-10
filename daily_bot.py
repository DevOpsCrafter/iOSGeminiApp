import os
import time
import requests
import google.generativeai as genai
import random
import urllib.parse
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# Load secrets from .env file if present (Local dev)
load_dotenv()

# Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
YOUR_EMAIL = os.environ.get("YOUR_EMAIL")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")  # Gmail App Password

def generate_astro_content():
    """Generates a prompt and caption using Gemini."""
    print("✨ Connecting to Gemini...")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')


    prompt = """
    You are 'Astroboli', a mystical AI astrologer. 
    1. Generate a visually descriptive image prompt for today's daily horoscope or cosmic energy. It should be mystical, ethereal, and artistic. 
    2. Write an engaging Instagram caption for this image.
    3. Provide 5 relevant hashtags.
    
    Output format:
    IMAGE_PROMPT: [The image prompt]
    CAPTION: [The caption]
    HASHTAGS: [The hashtags]
    """
    
    response = model.generate_content(prompt)
    text = response.text
    
    # Simple parsing
    try:
        image_prompt = text.split("IMAGE_PROMPT:")[1].split("CAPTION:")[0].strip()
        caption_part = text.split("CAPTION:")[1].split("HASHTAGS:")[0].strip()
        hashtags = text.split("HASHTAGS:")[1].strip()
        full_caption = f"{caption_part}\n\n{hashtags}"
        return image_prompt, full_caption
    except IndexError:
        print("⚠️ Gemini output format unexpected. Using raw text.")
        return text[:200], text

def get_image_url(prompt):
    """Generates an image URL from Pollinations.ai."""
    print(f"🎨 Generating image for: {prompt[:50]}...")
    encoded_prompt = urllib.parse.quote(prompt)
    seed = random.randint(1, 1000000)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&seed={seed}&nologo=true&model=flux"
    return image_url

def download_image(url):
    """Download image from URL and return bytes."""
    print(f"⬇️ Downloading image...")
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to download image: {response.status_code}")

def send_email(image_data, caption):
    """Sends email with image and caption."""
    print("📧 Sending email...")
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = YOUR_EMAIL
    msg['To'] = YOUR_EMAIL
    msg['Subject'] = '🌟 Your Daily Astroboli Post is Ready!'
    
    # Email body
    body = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #4A5568;">✨ Daily Astroboli Post Ready!</h2>
    
    <p>Your mystical content for today has been generated and is ready to share on Instagram.</p>
    
    <div style="background: #F7FAFC; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="color: #2D3748; margin-top: 0;">Caption & Hashtags:</h3>
        <p style="white-space: pre-wrap; color: #4A5568;">{caption}</p>
    </div>
    
    <div style="background: #EDF2F7; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h3 style="color: #2D3748; margin-top: 0;">📱 How to Post (30 seconds):</h3>
        <ol style="color: #4A5568;">
            <li>Open Instagram app on your phone</li>
            <li>Tap the <strong>+</strong> button</li>
            <li>Select the attached image from "Recent"</li>
            <li>Tap Next → Next</li>
            <li>Paste the caption (copy from above)</li>
            <li>Tap <strong>Share</strong></li>
        </ol>
    </div>
    
    <p style="color: #718096; font-size: 14px;">The image is attached to this email. Download it to your phone if needed.</p>
</body>
</html>
"""
    
    msg.attach(MIMEText(body, 'html'))
    
    # Attach image
    image = MIMEImage(image_data, name='astroboli_post.jpg')
    msg.attach(image)
    
    # Send via Gmail SMTP
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(YOUR_EMAIL, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("✅ Email sent successfully!")
    except Exception as e:
        raise Exception(f"Failed to send email: {e}")

def main():
    if not all([GEMINI_API_KEY, YOUR_EMAIL, EMAIL_PASSWORD]):
        print("❌ Error: Missing credentials.")
        print("Please fill out the '.env' file with your keys.")
        print("Required: GEMINI_API_KEY, YOUR_EMAIL, EMAIL_PASSWORD")
        exit(1)

    try:
        # 1. Generate Content
        prompt, caption = generate_astro_content()
        print(f"📝 Prompt: {prompt}")
        
        # 2. Get Image URL
        image_url = get_image_url(prompt)
        print(f"🖼️ Image URL: {image_url}")
        
        # 3. Download Image
        image_data = download_image(image_url)
        
        # 4. Send Email
        send_email(image_data, caption)
        
        print("\n✨ Done! Check your email for today's post.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
