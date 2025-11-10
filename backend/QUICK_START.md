# AI Title Generation - Quick Start

## 1. Setup (60 seconds)

```bash
# Get API key at: https://openrouter.ai/
# Add to backend/.env:
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

## 2. Start Server

```bash
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload
```

## 3. Test

```bash
# Swagger UI
open http://localhost:8000/docs

# cURL
curl -X POST "http://localhost:8000/ai/generate-titles" \
  -H "Content-Type: application/json" \
  -d '{"transcript_text": "Your video text here", "num_variations": 5}'
```

## 4. Use in Code

```python
from src.ai.title_generator import generate_titles_for_clip

response = await generate_titles_for_clip(
    transcript="Your transcript...",
    platform="tiktok",
    num_variations=8
)

print(f"Best: {response.best_title.title}")
print(f"Score: {response.best_title.virality_score}")
```

## API Endpoints

- `POST /ai/generate-titles` - Generate titles
- `POST /ai/generate-titles/clip/{id}` - Generate for existing clip
- `POST /ai/generate-titles/batch` - Batch generate
- `GET /ai/title-styles` - Available styles
- `GET /ai/platforms` - Supported platforms

## Features

✅ 5 AI models (Claude, GPT-4, Gemini, Llama, Mistral)
✅ 5 platforms (TikTok, Instagram, YouTube, Twitter, LinkedIn)
✅ 8 title styles (Question, Shocking, How-To, etc.)
✅ Virality scoring (0.0-1.0)
✅ Target audience customization
✅ Batch processing

## Cost

~$0.0007 per request (8 variations)
~$0.70 per 1,000 requests

## Documentation

- **Complete Guide:** `AI_TITLE_GENERATION_DOCS.md`
- **Setup Guide:** `OPENROUTER_SETUP.md`
- **Quick Reference:** `AI_PROMPTS_AND_API_SUMMARY.md`
- **Examples:** `examples/test_title_generation.py`

## Support

- Logs: `backend/logs/backend.log`
- Swagger: http://localhost:8000/docs
- OpenRouter: https://openrouter.ai/activity
