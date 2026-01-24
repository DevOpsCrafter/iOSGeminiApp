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
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO

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
    print("✨ Connecting to Gemini...")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    # Randomize branding for variety
    brand_variations = [
        "Astro Boli",
        "AstroBoli AI", 
        "Astro AI",
        "AstroBoli",
        "Astro Boli AI"
    ]
    brand_name = random.choice(brand_variations)
    brand_hashtag = brand_name.replace(" ", "")  # Remove spaces for hashtag

    prompt = f"""
    You are '{brand_name}' — a world-class digital artist and mystic astrologer creating MUSEUM-QUALITY cosmic art for astroboli.com.

    Generate a JSON object for today's horoscope with these keys:

    - "image_prompt": Create a MASTERPIECE-LEVEL prompt for Flux AI image generator. This must rival professional art. Include ALL of these elements:
    
      **MANDATORY QUALITY BOOSTERS (include at end of every prompt):**
      masterpiece, best quality, ultra high resolution, 8K UHD, HDR, professional photography, award-winning, trending on ArtStation, hyperdetailed, photorealistic lighting, cinematic color grading, octane render, unreal engine 5, ray tracing, subsurface scattering
      
      **ART STYLE (pick one per day and commit fully):**
      - "digital painting by Greg Rutkowski and Alphonse Mucha"
      - "ethereal fantasy art by Peter Mohrbacher"
      - "cosmic surrealism by Android Jones"
      - "luminous art nouveau with gold leaf accents"
      - "hyper-detailed concept art for AAA video game"
      - "cinematic matte painting, ILM VFX quality"
      - "mystical realism by Kinuko Y. Craft"
      
      **COLOR MASTERY:**
      - Rich color harmony: deep cosmic purples (#2D1B4E), celestial golds (#D4AF37), ethereal teals (#4ECDC4)
      - Dynamic color contrast and complementary palettes
      - Iridescent and holographic shimmer effects
      - Bioluminescent glowing accents
      
      **LIGHTING EXCELLENCE:**
      - Volumetric god rays piercing through cosmic clouds
      - Rim lighting with ethereal glow halos
      - Caustic light patterns from crystalline elements  
      - Dramatic chiaroscuro with soft ambient fill
      - Golden hour warmth with cool shadow undertones
      
      **COMPOSITION RULES:**
      - Strong focal point with depth of field (f/1.4 bokeh)
      - Rule of thirds with dynamic negative space
      - Leading lines drawing eye to center
      - Layered foreground/midground/background elements
      
      **COSMIC ELEMENTS (mix 3-4):**
      - Luminous celestial bodies with visible atmospheres
      - Intricate sacred geometry patterns (Flower of Life, Metatron's Cube)
      - Zodiac constellation overlays with connected stars
      - Flowing nebula clouds with particle dust
      - Crystal formations with internal light refraction
      - Ethereal spirit silhouettes or energy beings
      - Mystical portals with swirling energy
      
      **TECHNICAL REQUIREMENTS:**
      square format, aspect ratio 1:1, 1080x1080, no text, no watermarks, no logos, clean composition, centered subject, Instagram-optimized
      
      **AVOID:** blurry, low quality, text, watermarks, signatures, deformed, ugly, amateur, oversaturated, muddy colors

    - "caption": Engaging Instagram caption (≤280 chars):
      * Weave {brand_name} naturally into mystical insight
      * Include actionable cosmic guidance for today
      * End with "✨ Visit astroboli.com for your reading"
      * Use 2-3 emojis: 🌙 ✨ 🔮 ⭐ 🌟 💫 ♈♉♊♋♌♍♎♏♐♑♒♓
      
    - "hashtags": Array of exactly 5 hashtags:
      * First: #{brand_hashtag}
      * Include mix of: #Astrology #CosmicEnergy #ZodiacSigns #Spirituality #Universe #Manifestation #DailyHoroscope #MysticArt
      
    - "alt_text": Vivid 1-2 sentence description for accessibility.

    Return ONLY valid JSON. No markdown, no explanation.

    Example:
    {{
      "image_prompt": "Ethereal cosmic queen emerging from a luminous nebula, flowing hair made of stardust and aurora colors, sacred geometry halo behind her head, bioluminescent crystal crown, volumetric god rays piercing purple cosmic clouds, floating zodiac symbols around her, art by Peter Mohrbacher and Alphonse Mucha, deep purple and gold color palette, mystical and powerful mood, hyperdetailed, 8K UHD, masterpiece, best quality, trending on ArtStation, cinematic lighting, octane render, square format 1:1, no text, no watermarks",
      "caption": "The cosmos crowns you with infinite potential today. {brand_name} channels pure celestial energy for your transformation. ✨ Visit astroboli.com for your reading 🌙👑",
      "hashtags": ["#{brand_hashtag}", "#Astrology", "#CosmicEnergy", "#Spirituality", "#ZodiacSigns"],
      "alt_text": "A majestic cosmic queen with stardust hair emerging from purple nebula clouds, wearing a glowing crystal crown."
    }}
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

def process_for_instagram(image_bytes):
    """Process image for Instagram - ensure exact 1:1 ratio (1080x1080), NO text overlay."""
    print("Processing image for Instagram...")
    
    # Open image
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    original_w, original_h = img.size
    print(f"Original image: {original_w}x{original_h}")
    
    # Instagram square post: 1080x1080 pixels (1:1 ratio)
    INSTAGRAM_SIZE = 1080
    
    # Step 1: Center crop to perfect square
    if original_w != original_h:
        min_dim = min(original_w, original_h)
        left = (original_w - min_dim) // 2
        top = (original_h - min_dim) // 2
        right = left + min_dim
        bottom = top + min_dim
        img = img.crop((left, top, right, bottom))
        print(f"Center cropped to: {img.size[0]}x{img.size[1]}")
    
    # Step 2: Resize to exactly 1080x1080
    img = img.resize((INSTAGRAM_SIZE, INSTAGRAM_SIZE), Image.Resampling.LANCZOS)
    print(f"Resized to: {img.size[0]}x{img.size[1]}")
    
    # Step 3: Verify and save
    final_w, final_h = img.size
    
    if final_w != INSTAGRAM_SIZE or final_h != INSTAGRAM_SIZE:
        print(f"ERROR: Expected {INSTAGRAM_SIZE}x{INSTAGRAM_SIZE}, got {final_w}x{final_h}")
        # Force create correct size
        perfect = Image.new("RGB", (INSTAGRAM_SIZE, INSTAGRAM_SIZE), (0, 0, 0))
        perfect.paste(img, (0, 0))
        img = perfect
    
    # Save as high-quality JPEG
    output = BytesIO()
    img.save(output, format="JPEG", quality=98, optimize=True)
    output.seek(0)
    
    print(f"Final output: {INSTAGRAM_SIZE}x{INSTAGRAM_SIZE} (1:1 ratio) - ready for Instagram")
    
    return output.getvalue()

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
        
        # 4. Process image for Instagram (1:1 ratio, NO text overlay)
        processed_image = process_for_instagram(image_data)
        
        # 5. Send Email
        send_email(processed_image, caption)
        
        print("\n✨ Done! Check your email for today's post.")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
