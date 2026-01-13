#!/usr/bin/env python3
"""Test the JSON extraction helper with a code-fenced JSON response."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import daily_bot as db

sample = '''```json
{
  "image_prompt": "An ethereal, cosmic scene with gold & indigo, soft fog, 1:1 aspect",
  "caption": "Astroboli AI - Today...",
  "hashtags": ["#AstroboliAI","#astrology","#numerology","#horoscope","#zodiac"],
  "alt_text": "A glowing cosmic vortex"
}
```'''

data = db._extract_json_from_text(sample)
print('Extracted:', data)
if not data or data.get('image_prompt') is None:
    print('FAIL')
    sys.exit(2)
print('PASS')
sys.exit(0)
