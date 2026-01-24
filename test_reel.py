"""Local test for upgraded reel generation with AI video and better voice."""
import asyncio
import os
import tempfile
import urllib.parse
import random
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Test 1: Upgraded voice
async def test_voiceover():
    """Test edge-tts with upgraded MultilingualNeural voice."""
    print("\n" + "="*50)
    print("TEST 1: AI VOICEOVER (AvaMultilingualNeural)")
    print("="*50)
    
    try:
        import edge_tts
        
        text = "Welcome to AstroBoli. The stars reveal a powerful transformation awaits you today. Embrace the cosmic energy and trust the journey. Visit astroboli dot com for your complete reading."
        voice = "en-US-AvaMultilingualNeural"  # Best natural voice
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            audio_path = f.name
        
        communicate = edge_tts.Communicate(
            text, 
            voice,
            rate="-5%",  # Slightly slower for mystical effect
            pitch="+0Hz"
        )
        await communicate.save(audio_path)
        
        size = os.path.getsize(audio_path)
        print(f"✅ Voiceover generated with {voice}")
        print(f"   File: {audio_path}")
        print(f"   Size: {size} bytes")
        
        return audio_path
    except Exception as e:
        print(f"❌ Voiceover failed: {e}")
        import traceback
        traceback.print_exc()
        return None

# Test 2: AI Video from Pollinations
def test_ai_video():
    """Test Pollinations.ai video generation."""
    print("\n" + "="*50)
    print("TEST 2: AI VIDEO (Pollinations.ai)")
    print("="*50)
    
    try:
        video_prompt = "Mystical cosmic astrology scene, swirling galaxies, zodiac constellations, ethereal purple and gold colors, glowing stars"
        encoded_prompt = urllib.parse.quote(video_prompt)
        seed = random.randint(1, 1000000)
        
        video_url = f"https://video.pollinations.ai/text-to-video/{encoded_prompt}?model=seedance&duration=6&seed={seed}"
        
        print(f"Video prompt: {video_prompt[:50]}...")
        print(f"Requesting video... (this may take 1-3 minutes)")
        
        response = requests.get(video_url, timeout=180)
        
        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
                f.write(response.content)
                video_path = f.name
            
            size = os.path.getsize(video_path)
            print(f"✅ AI video downloaded!")
            print(f"   File: {video_path}")
            print(f"   Size: {size//1024} KB")
            return video_path
        else:
            print(f"⚠️ Video API returned status: {response.status_code}")
            print(f"   Response: {response.text[:200] if response.text else 'No response'}")
            return None
            
    except requests.exceptions.Timeout:
        print("⚠️ Video generation timed out (>3 min)")
        return None
    except Exception as e:
        print(f"❌ Video generation error: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    print("="*60)
    print("  UPGRADED REEL GENERATION TEST")
    print("  Testing: AvaMultilingualNeural voice + Pollinations AI video")
    print("="*60)
    
    # Test voiceover
    audio_path = await test_voiceover()
    
    # Test AI video
    video_path = test_ai_video()
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    if audio_path:
        print(f"✅ Voice: {audio_path}")
        print("   Play this file to hear the upgraded natural voice!")
    else:
        print("❌ Voice: Failed")
    
    if video_path:
        print(f"✅ Video: {video_path}")
        print("   Play this file to see AI-generated cosmic video!")
    else:
        print("⚠️ Video: Not available (may need API key or network issues)")
        print("   The system will fall back to animated image.")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(main())
