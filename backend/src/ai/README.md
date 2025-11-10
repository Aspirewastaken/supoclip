# AI Module

This module contains AI-powered functionality for SupoClip.

## Components

### Title Generator (`title_generator.py`)

AI-powered title generation system using OpenRouter to access multiple LLMs.

**Features:**
- Multi-LLM generation (Claude, GPT-4, Gemini, Llama, Mistral)
- Platform optimization (TikTok, Instagram, YouTube, Twitter, LinkedIn)
- Virality scoring algorithm
- 8 different title styles (Question, Shocking, How-To, etc.)
- Character limit enforcement
- Target audience customization

**Quick Usage:**

```python
from .title_generator import generate_titles_for_clip

# Generate titles
response = await generate_titles_for_clip(
    transcript="Your video transcript here...",
    platform="tiktok",
    num_variations=8
)

print(f"Best title: {response.best_title.title}")
print(f"Score: {response.best_title.virality_score}")
```

**Configuration:**

Requires `OPENROUTER_API_KEY` in environment variables.

See `/home/user/supoclip/backend/OPENROUTER_SETUP.md` for setup instructions.

## API Endpoints

All AI endpoints are available under `/ai/` prefix:

- `POST /ai/generate-titles` - Generate titles from transcript
- `POST /ai/generate-titles/clip/{clip_id}` - Generate titles for existing clip
- `POST /ai/generate-titles/batch` - Batch generate for multiple clips
- `GET /ai/title-styles` - Get available title styles
- `GET /ai/platforms` - Get supported platforms

See `/home/user/supoclip/backend/AI_TITLE_GENERATION_DOCS.md` for complete API documentation.

## Models Used

Via OpenRouter API:

1. **Claude 3.5 Sonnet** (Anthropic) - Creative, nuanced
2. **GPT-4 Turbo** (OpenAI) - High quality, versatile
3. **Gemini 2.0 Flash** (Google) - Fast, efficient
4. **Llama 3.1 70B** (Meta) - Open source, strong
5. **Mistral Large** (Mistral AI) - European perspective

## Development

### Adding New Title Styles

1. Add to `TitleStyle` enum in `title_generator.py`
2. Add detection logic in `_detect_title_style()`
3. Add style-specific instruction in `_build_user_prompt()`
4. Update API documentation

### Adding New Platforms

1. Add to `Platform` enum
2. Add character limit to `PLATFORM_LIMITS`
3. Add style guidelines to `PLATFORM_STYLES`
4. Update API documentation

### Tuning Virality Algorithm

Edit `_calculate_virality_score()` method to adjust scoring factors.

## Testing

```bash
# Run tests
pytest tests/ai/test_title_generator.py -v

# Test API endpoint
curl -X POST "http://localhost:8000/ai/generate-titles" \
  -H "Content-Type: application/json" \
  -d '{"transcript_text": "test", "num_variations": 3}'
```

## Cost Estimation

~$0.0007 per title generation request (8 variations)
~$0.70 per 1,000 requests

## Documentation

- **API Documentation**: `/home/user/supoclip/backend/AI_TITLE_GENERATION_DOCS.md`
- **Setup Guide**: `/home/user/supoclip/backend/OPENROUTER_SETUP.md`
- **Swagger UI**: http://localhost:8000/docs (when running)
