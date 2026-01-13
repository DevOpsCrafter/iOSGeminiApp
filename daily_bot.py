import os
import time
import requests
import google.generativeai as genai
import random
import urllib.parse
import json
import argparse
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

def _extract_json_from_text(text: str) -> dict | None:
    """Attempt to extract and parse a JSON object from free-form text.
    This handles cases where the model wraps JSON in markdown code fences (```json ... ```)
    or returns additional commentary around the JSON.
    Returns the parsed dict or None if parsing fails.
    """
    # Try a direct parse first
    try:
        return json.loads(text)
    except Exception:
        pass

    # Remove common markdown fences and try again
    import re
    # Find a JSON object inside text by locating the first '{' and last '}'
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end+1]
        try:
            return json.loads(candidate)
        except Exception:
            # Sometimes there are trailing or leading backticks to strip
            candidate = re.sub(r'```.*?```', '', text, flags=re.S).strip()
            start = candidate.find('{')
            end = candidate.rfind('}')
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(candidate[start:end+1])
                except Exception:
                    return None
    return None


def _clean_image_prompt(p: str) -> str:
    # Remove any accidental CTAs or Visit links from the image prompt
    import re
    p = re.sub(r'Visit\s+https?://\S+', '', p)
    p = p.replace('```json', '').replace('```', '')
    p = p.replace('\n', ' ').strip()
    # Collapse multiple spaces
    p = re.sub(r'\s+', ' ', p)
    # Limit length to a safe size for image API
    return p[:2000]


def generate_astro_content():
    """Generates a prompt and caption using Gemini."""
    print("Connecting to Gemini...")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')


    prompt = """
    You are 'Astroboli AI' — a creative branding studio and mystic astrologer for astroboli.com.

    For today's daily horoscope or cosmic energy, produce a single JSON object with the following keys:
    - "image_prompt": a highly-detailed image prompt to feed into an image generator. Include necessary style tokens, composition, color palette, mood, lighting, texture, and technical notes (important: `aspect_ratio:1:1`, `resolution:1080x1080`, `no readable text`, `no watermark`). Include a subtle area for a brand badge (no readable logo text on the image). Use style words: ethereal, cosmic, glowing, voluminous fog, gold & indigo palette, intricate star textures.
    - "caption": an Instagram-ready caption (<=300 chars). It must mention **Astroboli AI** at least once and include a short CTA such as "Visit astroboli.com" or "Read more on astroboli.com" and 1-2 emojis.
    - "hashtags": an **array of exactly 5** highly relevant hashtags (include `#AstroboliAI` and order from most to least relevant).
    - "alt_text": a short accessible image description (1-2 sentences) suitable for Instagram alt text.

    Requirements:
    - Return *only* valid JSON (no markdown, no explanation, no extra text).
    - Hashtags must be an array of length exactly 5; include `#AstroboliAI` as one of them.
    - Keep tone mystical, shareable, and concise.

    Example output:
    {
      "image_prompt": "...",
      "caption": "...",
      "hashtags": ["#AstroboliAI","#astrology","#numerology","#horoscope","#zodiac"],
      "alt_text": "..."
    }
    """

    response = model.generate_content(prompt)
    text = response.text

    # Prefer JSON output from the model; fall back to original heuristics if needed
    try:
        data = _extract_json_from_text(text) or {}
        if not data:
            raise ValueError("No JSON found in model output")
        image_prompt = data.get("image_prompt") or data.get("IMAGE_PROMPT") or ""
        caption_part = data.get("caption") or data.get("CAPTION") or ""
        hashtags_list = data.get("hashtags") or data.get("HASHTAGS") or []
        # Normalize hashtags
        if isinstance(hashtags_list, str):
            hashtags_list = [h.strip() for h in hashtags_list.replace(',', ' ').split() if h.strip()]
        normalized = []
        for h in hashtags_list:
            h = h.strip()
            if not h:
                continue
            if not h.startswith('#'):
                h = f"#{h}"
            normalized.append(h)
        # Take top 5. If fewer than 5, pad with related tags; ensure #AstroboliAI is present.
        top5 = normalized[:5]
        if '#astroboliai' in [t.lower() for t in top5]:
            pass
        else:
            top5 = ['#AstroboliAI'] + [t for t in top5 if t.lower() != '#astroboliai']
            top5 = top5[:5]
        defaults = ['#astrology', '#numerology', '#horoscope', '#zodiac']
        i = 0
        while len(top5) < 5 and i < len(defaults):
            cand = defaults[i]
            if cand not in top5:
                top5.append(cand)
            i += 1
        hashtags_str = " ".join(top5)
        # Clean image prompt from CTA / code fences
        image_prompt = _clean_image_prompt(image_prompt)
        # Ensure brand CTA in caption
        if "astroboli" not in caption_part.lower():
            caption_part = f"{caption_part.strip()} — Visit https://astroboli.com"
        full_caption = f"{caption_part}\n\n{hashtags_str}".strip()
        return image_prompt, full_caption, {'hashtags': top5}
    except Exception:
        # Fallback to older parsing for non-JSON responses
        try:
            # Try to extract a possible JSON inside text even if not pure JSON
            data = _extract_json_from_text(text)
            if data:
                return generate_astro_content_from_data(data)
            image_prompt = text.split("IMAGE_PROMPT:")[1].split("CAPTION:")[0].strip()
            caption_part = text.split("CAPTION:")[1].split("HASHTAGS:")[0].strip()
            hashtags = text.split("HASHTAGS:")[1].strip()
            # Normalize hashtags into list
            tags = [h.strip() for h in hashtags.replace(',', ' ').split() if h.strip()]
            normalized = []
            for h in tags:
                if not h.startswith('#'):
                    h = f"#{h}"
                normalized.append(h)
            top5 = normalized[:5]
            if '#AstroboliAI' not in [t for t in top5]:
                top5 = ['#AstroboliAI'] + [t for t in top5 if t.lower() != '#astroboliai']
                top5 = top5[:5]
            defaults = ['#astrology', '#numerology', '#horoscope', '#zodiac']
            i = 0
            while len(top5) < 5 and i < len(defaults):
                cand = defaults[i]
                if cand not in top5:
                    top5.append(cand)
                i += 1
            # Ensure brand CTA
            if "astroboli" not in caption_part.lower():
                caption_part = f"{caption_part}\n\nVisit https://astroboli.com"
            full_caption = f"{caption_part}\n\n{' '.join(top5)}"
            image_prompt = _clean_image_prompt(image_prompt)
            return image_prompt, full_caption, top5
        except Exception:
            print("Gemini output format unexpected. Using raw text.")
            raw = text.strip()
            # Make a brief caption + default hashtag
            short_caption = (raw[:240] + "...") if len(raw) > 240 else raw
            if "astroboli" not in short_caption.lower():
                short_caption = f"{short_caption}\n\nVisit https://astroboli.com"
            defaults = ['#AstroboliAI', '#astrology', '#numerology', '#horoscope', '#zodiac']
            return short_caption[:800], f"{short_caption}\n\n{' '.join(defaults)}", defaults


def get_image_url(prompt):
    """Generates an image URL from Pollinations.ai."""
    print(f"Generating image for: {prompt[:50]}...")
    encoded_prompt = urllib.parse.quote(prompt)
    seed = random.randint(1, 1000000)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&seed={seed}&nologo=true&model=flux"
    return image_url

def download_image(url):
    """Download image from URL and return bytes."""
    print("Downloading image...")
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to download image: {response.status_code}")

def send_email(image_data, caption):
    """Sends email with image and caption."""
    print("Sending email...")
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = YOUR_EMAIL
    msg['To'] = YOUR_EMAIL
    msg['Subject'] = 'Your Daily Astroboli Post is Ready!'
    
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
        print("Email sent successfully!")
    except Exception as e:
        raise Exception(f"Failed to send email: {e}")

def main():
    parser = argparse.ArgumentParser(description='Astroboli daily bot')
    parser.add_argument('--dry-run', action='store_true', help='Only generate content and validate hashtags (do not download image or send email)')
    parser.add_argument('--mock', action='store_true', help='Use a mock response instead of calling Gemini (for testing without API key)')
    args = parser.parse_args()

    # If not mocking, ensure credentials are set
    if not args.mock:
        if not all([GEMINI_API_KEY, YOUR_EMAIL, EMAIL_PASSWORD]):
            print("ERROR: Missing credentials.")
            print("Please fill out the '.env' file with your keys.")
            print("Required: GEMINI_API_KEY, YOUR_EMAIL, EMAIL_PASSWORD")
            exit(1)

    try:
        # 1. Generate Content
        if args.mock:
            # Use deterministic mock data for reliable tests
            def generate_mock_content():
                image_prompt = "Ethereal cosmic scene, gold and indigo palette, glowing stars, soft volumetric fog, intricate star textures, 1:1 aspect, 1080x1080, no watermark"
                caption = "Astroboli AI - Today's cosmic energy: embrace small shifts. — Visit https://astroboli.com\n\n#AstroboliAI #astrology #numerology #horoscope #zodiac"
                hashtags = ['#AstroboliAI', '#astrology', '#numerology', '#horoscope', '#zodiac']
                return image_prompt, caption, {'hashtags': hashtags}
            prompt, caption, meta = generate_mock_content()
        else:
            prompt, caption, meta = generate_astro_content()
        print(f"Prompt: {prompt}")
        print(f"Caption:\n{caption}")

        # If dry-run, validate hashtags and exit
        if args.dry_run:
            tags = meta.get('hashtags') if isinstance(meta, dict) else []
            print(f"Hashtags generated: {tags}")
            if not isinstance(tags, list) or len(tags) != 5:
                print("Validation failed: hashtags must be a list of exactly 5 items.")
                exit(2)
            if not any(t.lower() == '#astroboliai' for t in tags):
                print("Validation failed: #AstroboliAI must be present in hashtags.")
                exit(3)
            print("Dry-run validation passed: 5 hashtags (including #AstroboliAI) found.")
            exit(0)

        # 2. Get Image URL
        image_url = get_image_url(prompt)
        print(f"🖼️ Image URL: {image_url}")
        
        # 3. Download Image
        image_data = download_image(image_url)
        
        # 4. Send Email
        send_email(image_data, caption)
        
        print("\nDone! Check your email for today's post.")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
