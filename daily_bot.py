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
from email.mime.base import MIMEBase
from email import encoders
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import tempfile
import numpy as np
import asyncio

# Load secrets from .env file if present (Local dev)
load_dotenv()

# Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
YOUR_EMAIL = os.environ.get("YOUR_EMAIL")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")  # Gmail App Password

# AI Video API Keys (optional - register for free tiers)
FAL_KEY = os.environ.get("FAL_KEY")  # https://fal.ai
LUMA_API_KEY = os.environ.get("LUMA_API_KEY")  # https://lumalabs.ai
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")  # https://replicate.com

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

async def generate_voiceover(text, output_path):
    """Generate highly natural AI voiceover using edge-tts with best voices."""
    try:
        import edge_tts
        
        # Use the most natural-sounding Microsoft MultilingualNeural voices (2024)
        # These have more human-like qualities with natural pauses and intonation
        voice = "en-US-AvaMultilingualNeural"  # Bright, engaging, very natural
        
        # Alternative great voices:
        # "en-US-EmmaMultilingualNeural" - Friendly, light-hearted
        # "en-US-JennyNeural" - Warm, mature
        # "en-GB-SoniaNeural" - British, sophisticated
        
        # Create the communicate object with natural speech rate
        # Slightly slower for mystical/calming effect
        communicate = edge_tts.Communicate(
            text, 
            voice,
            rate="-5%",  # Slightly slower for dramatic effect
            pitch="+0Hz"  # Natural pitch
        )
        await communicate.save(output_path)
        
        print(f"✨ Voiceover generated with {voice}")
        return True
    except Exception as e:
        print(f"Error generating voiceover: {e}")
        return False

def download_ai_video(prompt, duration=8):
    """
    Download AI-generated video from multiple providers.
    Prioritizes high-quality authenticated APIs (Fal.ai, Luma, Replicate).
    Falls back to free unauthenticated options if API keys not configured.
    """
    print(f"🎥 Generating AI video: {prompt[:60]}...")
    
    # Prioritize authenticated high-quality APIs
    providers = []
    
    if FAL_KEY:
        providers.append(_try_fal_video)
    if LUMA_API_KEY:
        providers.append(_try_luma_api_video)
    if REPLICATE_API_TOKEN:
        providers.append(_try_replicate_video)
    
    # Add free fallbacks
    providers.extend([
        _try_huggingface_video,
        _try_modelslab_video,
    ])
    
    print(f"  Available providers: {len(providers)}")
    
    for provider in providers:
        try:
            result = provider(prompt, duration)
            if result and _is_valid_video(result):
                return result
        except Exception as e:
            print(f"  Provider failed: {e}")
            continue
    
    print("❌ All video providers failed")
    return None

def _try_fal_video(prompt, duration):
    """Try Fal.ai for high-quality video generation (Kling 2.5 model)."""
    print("  Trying: Fal.ai (Kling 2.5)...")
    
    if not FAL_KEY:
        print("    ⚠️ FAL_KEY not configured")
        return None
    
    try:
        import fal_client
        
        # Use Kling 2.5 Turbo for fast, high-quality generation
        result = fal_client.subscribe(
            "fal-ai/kling-video/v1.5/standard/text-to-video",
            arguments={
                "prompt": prompt,
                "duration": "5",  # 5 or 10 seconds
                "aspect_ratio": "9:16",  # Instagram Reels format
            },
            with_logs=False,
        )
        
        if result and result.get("video") and result["video"].get("url"):
            video_url = result["video"]["url"]
            video_response = requests.get(video_url, timeout=120)
            
            if video_response.status_code == 200:
                print(f"    ✅ Fal.ai Kling video: {len(video_response.content)//1024}KB")
                return video_response.content
                
    except ImportError:
        print("    ⚠️ fal-client not installed, using REST API...")
        # Fallback to REST API
        try:
            headers = {"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"}
            payload = {
                "prompt": prompt,
                "duration": "5",
                "aspect_ratio": "9:16",
            }
            
            # Submit request
            response = requests.post(
                "https://queue.fal.run/fal-ai/kling-video/v1.5/standard/text-to-video",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                request_id = data.get("request_id")
                
                if request_id:
                    # Poll for result
                    for _ in range(60):  # Wait up to 5 minutes
                        time.sleep(5)
                        status_resp = requests.get(
                            f"https://queue.fal.run/fal-ai/kling-video/v1.5/standard/text-to-video/requests/{request_id}/status",
                            headers=headers,
                            timeout=30
                        )
                        if status_resp.status_code == 200:
                            status_data = status_resp.json()
                            if status_data.get("status") == "COMPLETED":
                                result_resp = requests.get(
                                    f"https://queue.fal.run/fal-ai/kling-video/v1.5/standard/text-to-video/requests/{request_id}",
                                    headers=headers,
                                    timeout=30
                                )
                                if result_resp.status_code == 200:
                                    result_data = result_resp.json()
                                    if result_data.get("video", {}).get("url"):
                                        video_url = result_data["video"]["url"]
                                        video_resp = requests.get(video_url, timeout=120)
                                        if video_resp.status_code == 200:
                                            print(f"    ✅ Fal.ai video: {len(video_resp.content)//1024}KB")
                                            return video_resp.content
                                break
                            elif status_data.get("status") == "FAILED":
                                print(f"    ❌ Fal.ai failed: {status_data.get('error')}")
                                break
                                
        except Exception as e:
            print(f"    Fal.ai REST error: {e}")
    except Exception as e:
        print(f"    Fal.ai error: {e}")
    
    return None

def _try_luma_api_video(prompt, duration):
    """Try Luma AI official API for video generation."""
    print("  Trying: Luma AI API...")
    
    if not LUMA_API_KEY:
        print("    ⚠️ LUMA_API_KEY not configured")
        return None
    
    try:
        headers = {
            "Authorization": f"Bearer {LUMA_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Create generation request
        payload = {
            "prompt": prompt,
            "aspect_ratio": "9:16",
            "loop": False,
        }
        
        response = requests.post(
            "https://api.lumalabs.ai/dream-machine/v1/generations",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            generation_id = data.get("id")
            
            if generation_id:
                # Poll for completion
                for _ in range(60):  # Wait up to 5 minutes
                    time.sleep(5)
                    status_resp = requests.get(
                        f"https://api.lumalabs.ai/dream-machine/v1/generations/{generation_id}",
                        headers=headers,
                        timeout=30
                    )
                    
                    if status_resp.status_code == 200:
                        status_data = status_resp.json()
                        state = status_data.get("state")
                        
                        if state == "completed":
                            video_url = status_data.get("assets", {}).get("video")
                            if video_url:
                                video_resp = requests.get(video_url, timeout=120)
                                if video_resp.status_code == 200:
                                    print(f"    ✅ Luma AI video: {len(video_resp.content)//1024}KB")
                                    return video_resp.content
                            break
                        elif state == "failed":
                            print(f"    ❌ Luma failed: {status_data.get('failure_reason')}")
                            break
        else:
            print(f"    Luma API returned: {response.status_code}")
            
    except Exception as e:
        print(f"    Luma API error: {e}")
    
    return None

def _try_replicate_video(prompt, duration):
    """Try Replicate API for video generation (CogVideoX)."""
    print("  Trying: Replicate (CogVideoX)...")
    
    if not REPLICATE_API_TOKEN:
        print("    ⚠️ REPLICATE_API_TOKEN not configured")
        return None
    
    try:
        headers = {
            "Authorization": f"Token {REPLICATE_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Use CogVideoX-5B for text-to-video
        payload = {
            "version": "2b89ece6d64f7deccae55c54a3a2ca8d2bea04e3c0d3b5c6f7a1e8e5e5c5e5e5",
            "input": {
                "prompt": prompt,
                "num_frames": 49,  # ~6 seconds at 8fps
                "fps": 8,
            }
        }
        
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            prediction_id = data.get("id")
            
            if prediction_id:
                # Poll for completion
                for _ in range(60):
                    time.sleep(5)
                    status_resp = requests.get(
                        f"https://api.replicate.com/v1/predictions/{prediction_id}",
                        headers=headers,
                        timeout=30
                    )
                    
                    if status_resp.status_code == 200:
                        status_data = status_resp.json()
                        status = status_data.get("status")
                        
                        if status == "succeeded":
                            output = status_data.get("output")
                            video_url = output[0] if isinstance(output, list) else output
                            if video_url:
                                video_resp = requests.get(video_url, timeout=120)
                                if video_resp.status_code == 200:
                                    print(f"    ✅ Replicate video: {len(video_resp.content)//1024}KB")
                                    return video_resp.content
                            break
                        elif status == "failed":
                            print(f"    ❌ Replicate failed: {status_data.get('error')}")
                            break
        else:
            print(f"    Replicate returned: {response.status_code}")
            
    except Exception as e:
        print(f"    Replicate error: {e}")
    
    return None

def _try_luma_video(prompt, duration):
    """Try Luma AI Dream Machine via Hugging Face Space (fallback)."""
    print("  Trying: Luma AI HuggingFace Space...")
    
    try:
        from gradio_client import Client
        
        # Luma AI Dream Machine Hugging Face Spaces
        spaces_to_try = [
            "multimodalart/Luma-Dream-Machine",
            "hysts/Luma-Dream-Machine",
        ]
        
        for space in spaces_to_try:
            try:
                print(f"    Connecting to {space}...")
                client = Client(space, verbose=False)
                
                # Luma spaces typically use text prompt input
                result = client.predict(
                    prompt,
                    api_name="/generate"
                )
                
                if result:
                    # Result might be a file path or tuple
                    video_path = result[0] if isinstance(result, (list, tuple)) else result
                    
                    if video_path and os.path.exists(str(video_path)):
                        with open(video_path, 'rb') as f:
                            video_data = f.read()
                        
                        if _is_valid_video(video_data):
                            print(f"    ✅ Luma AI video: {len(video_data)//1024}KB")
                            return video_data
                    
            except Exception as e:
                print(f"    {space}: {str(e)[:60]}")
                continue
                
    except ImportError:
        print("    gradio_client not installed")
    
    return None

def _try_huggingface_video(prompt, duration):
    """Try Hugging Face Spaces Gradio API for video generation."""
    print("  Trying: Hugging Face Gradio...")
    
    try:
        from gradio_client import Client
        
        # Try CogVideoX on Hugging Face Spaces
        spaces_to_try = [
            "THUDM/CogVideoX-5B-Space",
            "Kyky/CogVideoX-Fun-V1-1-5B-Pose",
        ]
        
        for space in spaces_to_try:
            try:
                print(f"    Connecting to {space}...")
                client = Client(space, verbose=False)
                
                # Most video spaces use predict() with prompt and other params
                result = client.predict(
                    prompt=prompt,
                    api_name="/generate"
                )
                
                if result and os.path.exists(result):
                    with open(result, 'rb') as f:
                        video_data = f.read()
                    print(f"    ✅ HuggingFace video: {len(video_data)//1024}KB")
                    return video_data
                    
            except Exception as e:
                print(f"    {space}: {str(e)[:50]}")
                continue
                
    except ImportError:
        print("    gradio_client not installed")
    
    return None

def _try_modelslab_video(prompt, duration):
    """Try ModelsLab free tier for video generation."""
    print("  Trying: ModelsLab API...")
    
    try:
        # ModelsLab offers free tier - no API key for limited use
        api_url = "https://modelslab.com/api/v6/video/text2video"
        
        payload = {
            "key": "",  # Empty for free tier
            "prompt": prompt,
            "negative_prompt": "low quality, blurry, distorted",
            "model_id": "cogvideox",
            "height": 480,
            "width": 720,
            "num_frames": 16,
            "fps": 8,
        }
        
        response = requests.post(api_url, json=payload, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success" and data.get("output"):
                video_url = data["output"][0] if isinstance(data["output"], list) else data["output"]
                video_response = requests.get(video_url, timeout=60)
                if video_response.status_code == 200:
                    print(f"    ✅ ModelsLab video: {len(video_response.content)//1024}KB")
                    return video_response.content
        
        print(f"    ModelsLab returned: {response.status_code}")
        
    except Exception as e:
        print(f"    ModelsLab error: {e}")
    
    return None

def _is_valid_video(content):
    """Check if content is actually a video file (not an image)."""
    if not content or len(content) < 1000:
        return False
    
    # Check video magic bytes
    # MP4/MOV: starts with ftyp after 4 bytes
    # WebM: starts with 0x1A45DFA3
    # AVI: starts with RIFF...AVI
    header = content[:12]
    
    # MP4/MOV check
    if len(header) >= 8 and header[4:8] == b'ftyp':
        return True
    # WebM check  
    if header[:4] == b'\x1a\x45\xdf\xa3':
        return True
    # AVI check
    if header[:4] == b'RIFF' and len(header) >= 12 and header[8:12] == b'AVI ':
        return True
    # OGG video check
    if header[:4] == b'OggS':
        return True
        
    # Reject common image formats
    # JPEG
    if header[:2] == b'\xff\xd8':
        print("    ❌ Rejected: received JPEG image instead of video")
        return False
    # PNG
    if header[:4] == b'\x89PNG':
        print("    ❌ Rejected: received PNG image instead of video")
        return False
    # GIF
    if header[:3] == b'GIF':
        print("    ❌ Rejected: received GIF instead of video")
        return False
    # WebP
    if header[:4] == b'RIFF' and len(header) >= 12 and header[8:12] == b'WEBP':
        print("    ❌ Rejected: received WebP image instead of video")
        return False
    
    # Unknown format but large enough to potentially be video
    return len(content) > 500000  # 500KB minimum for unknown format

def _try_pollinations_video(prompt, duration):
    """Try Pollinations.ai for video generation."""
    print("  Trying: Pollinations.ai...")
    
    # Skip Pollinations for now - currently returns images, not videos
    print("    ⚠️ Pollinations video API currently unavailable")
    return None

def generate_reel(image_bytes, caption_text, brand_name):
    """Generate a professional Instagram Reel with AI voiceover and video effects."""
    print("🎬 Generating Professional Instagram Reel...")
    
    try:
        from moviepy.video.VideoClip import VideoClip
        from moviepy.audio.io.AudioFileClip import AudioFileClip
        from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
    except ImportError:
        print("WARNING: moviepy not available, skipping reel generation")
        return None
    
    try:
        # Instagram Reels specs: 9:16 aspect ratio, 1080x1920
        REEL_WIDTH = 1080
        REEL_HEIGHT = 1920
        FPS = 24
        
        # Extract a short, punchy script from caption for voiceover
        # Remove hashtags and website links for cleaner voiceover
        script_lines = caption_text.split('\n')
        script = script_lines[0] if script_lines else "Embrace the cosmic energy today"
        script = script.split('#')[0].strip()
        script = script.replace('https://astroboli.com', '').replace('astroboli.com', '')
        script = script.replace('Visit', '').strip()
        
        # Add brand intro for professionalism
        full_script = f"Welcome to {brand_name}. {script}. Visit astroboli dot com for your complete reading."
        
        print(f"Script: {full_script[:80]}...")
        
        # Generate voiceover
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as audio_tmp:
            audio_path = audio_tmp.name
        
        # Run async voiceover generation
        voiceover_success = asyncio.run(generate_voiceover(full_script, audio_path))
        
        if not voiceover_success or not os.path.exists(audio_path):
            print("Voiceover generation failed, continuing without audio")
            audio_path = None
        
        # Get audio duration to match video length
        if audio_path:
            audio_clip = AudioFileClip(audio_path)
            DURATION = audio_clip.duration + 1  # Add 1 second buffer
            audio_clip.close()
        else:
            DURATION = 10
        
        print(f"Reel duration target: {DURATION:.1f}s")
        
        # ===== TRY AI VIDEO GENERATION FIRST =====
        # Create a cosmic video prompt for Pollinations.ai
        video_prompt = f"Mystical cosmic astrology scene, swirling galaxies, zodiac constellations, ethereal purple and gold colors, glowing stars, nebula clouds, magical celestial energy, cinematic, 4K quality, slow motion particles, dreamy atmosphere"
        
        # Try to download AI-generated video from Pollinations.ai
        ai_video_data = download_ai_video(video_prompt, duration=min(10, int(DURATION)))
        
        use_ai_video = ai_video_data is not None
        
        if use_ai_video:
            print("✅ Using AI-generated video from Pollinations.ai")
            # Save AI video to temp file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as vid_tmp:
                vid_tmp.write(ai_video_data)
                ai_video_path = vid_tmp.name
            
            # Load AI video as clip
            from moviepy.video.io.VideoFileClip import VideoFileClip
            video_clip = VideoFileClip(ai_video_path)
            
            # Resize to Instagram Reels dimensions (9:16)
            video_clip = video_clip.resized((REEL_WIDTH, REEL_HEIGHT))
            
            # Loop or trim to match audio duration
            if video_clip.duration < DURATION:
                # Loop the video
                loops_needed = int(DURATION / video_clip.duration) + 1
                from moviepy.video.fx.loop import loop
                video_clip = loop(video_clip, n=loops_needed).with_duration(DURATION)
            else:
                video_clip = video_clip.subclipped(0, DURATION)
                
        else:
            # NO FALLBACK - User requested real AI video only
            print("❌ AI video generation failed - no reel will be created")
            print("💡 All providers returned errors. Real AI video required - no fallback to animated images.")
            return None
        
        # ===== ADD AUDIO AND RENDER =====
        if audio_path:
            audio_clip = AudioFileClip(audio_path)
            video_clip = video_clip.with_audio(audio_clip)
            print("Audio attached to video")
        
        # Write final video
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            output_path = tmp.name
        
        print(f"Rendering reel to: {output_path}")
        video_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac' if audio_path else None,
            fps=FPS,
            preset='medium'
        )
        
        # Read the final video
        with open(output_path, 'rb') as f:
            video_data = f.read()
        
        # Cleanup
        video_clip.close()
        os.unlink(output_path)
        if audio_path and os.path.exists(audio_path):
            os.unlink(audio_path)
        
        print(f"✅ Professional reel generated: {REEL_WIDTH}x{REEL_HEIGHT}, {DURATION:.1f}s, size: {len(video_data)//1024}KB")
        
        return video_data
        
    except Exception as e:
        print(f"ERROR generating reel: {e}")
        import traceback
        traceback.print_exc()
        return None

def send_email(image_data, caption, reel_data=None):
    """Sends email with image, caption, and optional reel."""
    print("Sending email...")
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = YOUR_EMAIL
    msg['To'] = YOUR_EMAIL
    
    has_reel = reel_data is not None
    msg['Subject'] = 'Your Daily Astroboli Post & Reel are Ready!' if has_reel else 'Your Daily Astroboli Post is Ready!'
    
    # Email body
    reel_section = """
    <div style="background: #E6FFFA; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #38B2AC;">
        <h3 style="color: #234E52; margin-top: 0;">🎬 Instagram Reel Attached!</h3>
        <p style="color: #285E61;">A 10-second animated reel is also attached. Upload it as a Reel for maximum engagement!</p>
    </div>
    """ if has_reel else ""
    
    body = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #4A5568;">✨ Daily Astroboli Content Ready!</h2>
    
    <p>Your mystical content for today has been generated and is ready to share on Instagram.</p>
    
    {reel_section}
    
    <div style="background: #F7FAFC; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="color: #2D3748; margin-top: 0;">Caption & Hashtags:</h3>
        <p style="white-space: pre-wrap; color: #4A5568;">{caption}</p>
    </div>
    
    <div style="background: #EDF2F7; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h3 style="color: #2D3748; margin-top: 0;">📱 How to Post (30 seconds):</h3>
        <ol style="color: #4A5568;">
            <li>Open Instagram app on your phone</li>
            <li>Tap the <strong>+</strong> button</li>
            <li>Select the attached image/reel from "Recent"</li>
            <li>Tap Next → Next</li>
            <li>Paste the caption (copy from above)</li>
            <li>Tap <strong>Share</strong></li>
        </ol>
    </div>
    
    <p style="color: #718096; font-size: 14px;">Attachments: Post image (1080x1080){' + Reel video (1080x1920)' if has_reel else ''}</p>
</body>
</html>
"""
    
    msg.attach(MIMEText(body, 'html'))
    
    # Attach image
    image = MIMEImage(image_data, name='astroboli_post.jpg')
    msg.attach(image)
    
    # Attach reel if available
    if reel_data:
        reel = MIMEBase('video', 'mp4')
        reel.set_payload(reel_data)
        encoders.encode_base64(reel)
        reel.add_header('Content-Disposition', 'attachment', filename='astroboli_reel.mp4')
        msg.attach(reel)
        print("Reel attached to email")
    
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
        
        # 4. Process image for Instagram (1:1 ratio, 1080x1080)
        processed_image = process_for_instagram(image_data)
        
        # 5. Generate Instagram Reel (animated video from image)
        brand_variations = ["Astro Boli", "AstroBoli AI", "Astro AI", "AstroBoli", "Astro Boli AI"]
        brand_name = random.choice(brand_variations)
        reel_data = generate_reel(image_data, caption, brand_name)
        
        # 6. Send Email with post image and reel
        send_email(processed_image, caption, reel_data)
        
        print("\n✨ Done! Check your email for today's post and reel.")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
