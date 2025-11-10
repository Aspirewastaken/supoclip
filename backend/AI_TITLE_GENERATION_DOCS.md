# AI-Powered Title Generation System

## Overview

The AI Title Generation System uses OpenRouter to access multiple Large Language Models (LLMs) for generating viral, platform-optimized titles for video clips. The system generates 5-10+ title variations per clip, each scored by virality potential and tailored to specific platforms and target audiences.

## Architecture

### Core Components

1. **TitleGenerator** (`/home/user/supoclip/backend/src/ai/title_generator.py`)
   - Main title generation engine
   - Manages multi-LLM orchestration via OpenRouter
   - Implements virality scoring algorithm
   - Platform-specific optimization

2. **API Routes** (`/home/user/supoclip/backend/src/api/routes/ai_titles.py`)
   - RESTful endpoints for title generation
   - Single and batch processing
   - Database integration for clip-based generation

3. **Models & Schemas**
   - Pydantic models for request/response validation
   - Type-safe enum definitions for platforms and styles

## AI Models Used

The system cycles through multiple state-of-the-art models via OpenRouter:

1. **Claude 3.5 Sonnet** (Anthropic) - Creative, nuanced language
2. **GPT-4 Turbo** (OpenAI) - High-quality, versatile
3. **Gemini 2.0 Flash** (Google) - Fast, efficient
4. **Llama 3.1 70B** (Meta) - Open-source, strong performance
5. **Mistral Large** (Mistral AI) - European perspective, multilingual

### Why Multiple Models?

- **Diversity**: Each model has unique creative tendencies
- **Robustness**: Failover if one model is unavailable
- **Quality**: More variations = higher chance of viral hits
- **Innovation**: Different models catch different trends

## AI Prompts

### System Prompt Template

The system prompt is dynamically constructed based on platform and audience:

```
You are an expert social media content strategist specializing in viral {PLATFORM} titles.

Your goal is to create highly engaging, click-worthy titles that maximize views and engagement.

PLATFORM: {PLATFORM_NAME}
CHARACTER LIMIT: {CHAR_LIMIT} characters
TARGET AUDIENCE: {AUDIENCE} (if provided)

PLATFORM STYLE GUIDELINES:
{PLATFORM_SPECIFIC_STYLE}

TITLE CREATION PRINCIPLES:

1. HOOK PSYCHOLOGY:
   - Create curiosity gaps (make them want to know more)
   - Use pattern interrupts (unexpected angles)
   - Trigger emotional responses (surprise, excitement, validation)
   - Promise value (what they'll learn or gain)

2. VIRALITY FACTORS:
   - Strong opening (first 3 words are critical)
   - Relatable pain points or desires
   - Surprising or counterintuitive angles
   - Social proof implications ("everyone is talking about...")
   - Urgency or timeliness

3. FORMATTING BEST PRACTICES:
   - Use powerful action verbs
   - Include specific numbers when relevant
   - Ask compelling questions
   - Create before/after contrasts
   - Use "you" and "your" for direct connection

4. AVOID:
   - Clickbait that doesn't deliver
   - Generic or boring descriptions
   - Overly complex language
   - Misleading information
   - Excessive emojis or special characters

Your titles should be authentic, deliver on their promise, and make viewers genuinely excited to watch.
```

### Platform-Specific Style Guidelines

**TikTok:**
```
"casual, trendy, uses slang, creates FOMO, hooks in first 3 words"
```

**Instagram:**
```
"aesthetic, aspirational, uses emojis strategically, creates desire"
```

**YouTube:**
```
"search-optimized, clear value proposition, includes keywords"
```

**Twitter:**
```
"punchy, conversational, thread-starter potential"
```

**LinkedIn:**
```
"professional, thought-leadership, industry insights"
```

### User Prompt Template

```
Generate a viral title for this video clip.

CLIP TRANSCRIPT:
{transcript_text}

KEY TOPICS: {topics} (if provided)
CLIP DURATION: {duration} seconds (if provided)

STYLE REQUIREMENT: {style_specific_instruction} (if style specified)

Generate ONE highly engaging title that:
1. Accurately represents the content
2. Maximizes click-through potential
3. Fits the character limit
4. Follows the platform style guidelines
5. Creates genuine excitement to watch

Respond with ONLY the title text, nothing else.
```

### Style-Specific Instructions

When a specific style is requested, the system adds targeted instructions:

- **Question**: "Create a compelling question that makes viewers curious"
- **Shocking**: "Use surprising or shocking elements to grab attention"
- **How-To**: "Frame as educational/tutorial (how to, guide to, etc.)"
- **Listicle**: "Use number-based format (X ways to, X things, etc.)"
- **Story**: "Tell it as a narrative or story hook"
- **Direct**: "Be direct and straightforward about the value"
- **Curiosity**: "Create a curiosity gap without revealing everything"
- **Emotional**: "Lead with emotional hook (excitement, inspiration, etc.)"

## API Endpoints

### Base URL
```
http://localhost:8000
```

### 1. Generate Titles

**Endpoint:** `POST /ai/generate-titles`

**Description:** Generate viral titles for a video clip using multiple AI models.

**Request Body:**
```json
{
  "transcript_text": "In this video, I share the secret technique that helped me grow my business from zero to $1M in just 18 months. Nobody talks about this, but it's the most important factor in success...",
  "platform": "tiktok",
  "target_audience": "young entrepreneurs",
  "key_topics": ["business growth", "entrepreneurship", "success"],
  "duration_seconds": 32.5,
  "num_variations": 10,
  "include_styles": ["question", "shocking", "curiosity"]
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `transcript_text` | string | Yes | The transcript text of the clip |
| `platform` | enum | No | Target platform: `tiktok`, `instagram`, `youtube`, `twitter`, `linkedin` (default: `tiktok`) |
| `target_audience` | string | No | Description of target audience |
| `key_topics` | array[string] | No | Key topics/themes from the video |
| `duration_seconds` | float | No | Clip duration in seconds |
| `num_variations` | integer | No | Number of titles (3-15, default: 8) |
| `include_styles` | array[enum] | No | Specific styles to use |

**Response:**
```json
{
  "titles": [
    {
      "title": "The $1M Secret Nobody Tells You About Business Growth",
      "style": "curiosity",
      "virality_score": 0.87,
      "reasoning": "Creates information gap that drives clicks. Uses direct address to create personal connection. Includes specific number for credibility. Optimized length for tiktok (55/150 chars). High virality potential based on engagement factors.",
      "character_count": 55,
      "model_used": "claude-3.5-sonnet"
    },
    {
      "title": "Why Do 99% of Entrepreneurs Fail at This One Thing?",
      "style": "question",
      "virality_score": 0.84,
      "reasoning": "Creates curiosity by posing a question viewers want answered. Uses direct address to create personal connection. Includes specific number for credibility. Strong engagement potential with proven elements.",
      "character_count": 53,
      "model_used": "gpt-4-turbo"
    }
    // ... more titles
  ],
  "best_title": {
    "title": "The $1M Secret Nobody Tells You About Business Growth",
    "style": "curiosity",
    "virality_score": 0.87,
    "reasoning": "Creates information gap that drives clicks. Uses direct address to create personal connection...",
    "character_count": 55,
    "model_used": "claude-3.5-sonnet"
  },
  "platform": "tiktok",
  "total_generated": 10
}
```

### 2. Generate Titles for Existing Clip

**Endpoint:** `POST /ai/generate-titles/clip/{clip_id}`

**Description:** Generate titles for a clip that already exists in the database.

**Path Parameters:**
- `clip_id` (string): The UUID of the clip

**Query Parameters:**
- `platform` (string, default: "tiktok"): Target platform
- `target_audience` (string, optional): Target audience description
- `num_variations` (integer, default: 8): Number of variations

**Example:**
```
POST /ai/generate-titles/clip/123e4567-e89b-12d3-a456-426614174000?platform=instagram&num_variations=10
```

**Response:** Same as Generate Titles endpoint

### 3. Batch Generate Titles

**Endpoint:** `POST /ai/generate-titles/batch`

**Description:** Generate titles for multiple clips in a single request.

**Request Body:**
```json
{
  "clip_ids": [
    "clip-uuid-1",
    "clip-uuid-2",
    "clip-uuid-3"
  ],
  "platform": "youtube",
  "target_audience": "fitness enthusiasts",
  "num_variations": 5
}
```

**Response:**
```json
{
  "results": {
    "clip-uuid-1": {
      "titles": [...],
      "best_title": {...},
      "platform": "youtube",
      "total_generated": 5
    },
    "clip-uuid-2": {
      "titles": [...],
      "best_title": {...},
      "platform": "youtube",
      "total_generated": 5
    }
  },
  "total_clips": 3,
  "successful": 2,
  "failed": 1
}
```

### 4. Get Title Styles

**Endpoint:** `GET /ai/title-styles`

**Description:** Get all available title styles with descriptions and examples.

**Response:**
```json
{
  "styles": {
    "question": {
      "name": "Question",
      "description": "Starts with a question to create curiosity",
      "example": "Why Are People Obsessed With This Simple Trick?"
    },
    "shocking": {
      "name": "Shocking",
      "description": "Uses shocking or surprising elements",
      "example": "This One Mistake Cost Me Everything"
    }
    // ... more styles
  },
  "total": 8
}
```

### 5. Get Supported Platforms

**Endpoint:** `GET /ai/platforms`

**Description:** Get information about all supported platforms.

**Response:**
```json
{
  "platforms": {
    "tiktok": {
      "name": "TikTok",
      "character_limit": 150,
      "style": "casual, trendy, uses slang, creates FOMO, hooks in first 3 words",
      "optimal_length": "50-100 characters"
    },
    "instagram": {
      "name": "Instagram",
      "character_limit": 125,
      "style": "aesthetic, aspirational, uses emojis strategically, creates desire",
      "optimal_length": "40-90 characters"
    }
    // ... more platforms
  },
  "total": 5
}
```

## Virality Scoring Algorithm

The system calculates a virality score (0.0-1.0) based on multiple factors:

### Scoring Components

1. **Length Optimization** (±0.15-0.20 points)
   - Platform-specific optimal ranges
   - TikTok: 50-100 chars ideal
   - YouTube: 50-80 chars ideal
   - Others: 40-90 chars ideal
   - Penalty for exceeding character limit

2. **Power Words** (+0.05 per word, max +0.15)
   - Engagement drivers: secret, revealed, shocking, amazing, ultimate
   - Action words: proven, guaranteed, exclusive, breakthrough
   - Personal: you, your, why, how, what
   - Impact: best, worst, truth, exposed, warning

3. **Numbers Present** (+0.10)
   - Specific numbers increase credibility
   - Examples: "5 ways", "$1M", "30 days"

4. **Question Format** (+0.10)
   - Questions drive engagement
   - Creates curiosity

5. **Strong First Word** (+0.08)
   - Critical hook words: why, how, what, this, the
   - Action starters: watch, stop, wait

6. **Emotional Words** (+0.07)
   - Emotion drives shares
   - Examples: love, fear, dream, excited, amazing

7. **Style Bonuses** (+0.05-0.09)
   - Question: +0.05
   - Shocking: +0.08
   - How-To: +0.06
   - Listicle: +0.07
   - Curiosity: +0.09

### Score Interpretation

- **0.8-1.0**: High virality potential - exceptional engagement factors
- **0.6-0.8**: Strong potential - proven engagement elements
- **0.4-0.6**: Moderate potential - solid but could be improved
- **0.0-0.4**: Low potential - needs optimization

## Platform-Specific Optimizations

### TikTok
- **Character Limit:** 150
- **Optimal Length:** 50-100 characters
- **Style:** Casual, trendy, creates FOMO
- **Hook:** First 3 words are critical
- **Best Styles:** Curiosity, Shocking, Question

### Instagram
- **Character Limit:** 125
- **Optimal Length:** 40-90 characters
- **Style:** Aesthetic, aspirational
- **Hook:** Visual appeal + desire creation
- **Best Styles:** Emotional, Story, Direct

### YouTube
- **Character Limit:** 100
- **Optimal Length:** 50-80 characters
- **Style:** Search-optimized, keyword-rich
- **Hook:** Clear value proposition
- **Best Styles:** How-To, Listicle, Question

### Twitter
- **Character Limit:** 280
- **Optimal Length:** 60-100 characters
- **Style:** Punchy, conversational
- **Hook:** Thread-starter potential
- **Best Styles:** Question, Direct, Shocking

### LinkedIn
- **Character Limit:** 120
- **Optimal Length:** 40-90 characters
- **Style:** Professional, thought-leadership
- **Hook:** Industry insights
- **Best Styles:** Direct, How-To, Question

## Configuration

### Environment Variables

Required in `backend/.env`:

```env
# OpenRouter Configuration (Required)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_REFERER=http://localhost:3000

# Database (Required for clip-based endpoints)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/supoclip
```

### Getting OpenRouter API Key

1. Sign up at https://openrouter.ai/
2. Navigate to API Keys section
3. Create a new API key
4. Add credits to your account
5. Set the key in your `.env` file

### Model Pricing (OpenRouter)

Approximate costs per 1,000 titles generated:

- Claude 3.5 Sonnet: ~$0.15
- GPT-4 Turbo: ~$0.30
- Gemini 2.0 Flash: ~$0.05
- Llama 3.1 70B: ~$0.08
- Mistral Large: ~$0.12

**Total:** ~$0.70 per 1,000 titles (cycling through all models)

## Usage Examples

### Python Client Example

```python
import aiohttp
import asyncio

async def generate_titles():
    url = "http://localhost:8000/ai/generate-titles"

    payload = {
        "transcript_text": "Your video transcript here...",
        "platform": "tiktok",
        "target_audience": "young creators",
        "num_variations": 10
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()

            print(f"Generated {result['total_generated']} titles")
            print(f"\nBest title (score: {result['best_title']['virality_score']}):")
            print(result['best_title']['title'])

            print("\nAll titles:")
            for title in result['titles']:
                print(f"[{title['virality_score']:.2f}] {title['title']}")

asyncio.run(generate_titles())
```

### JavaScript/TypeScript Example

```typescript
const generateTitles = async () => {
  const response = await fetch('http://localhost:8000/ai/generate-titles', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      transcript_text: 'Your video transcript here...',
      platform: 'instagram',
      num_variations: 8
    })
  });

  const result = await response.json();

  console.log(`Best title: ${result.best_title.title}`);
  console.log(`Score: ${result.best_title.virality_score}`);

  return result;
};
```

### cURL Example

```bash
curl -X POST "http://localhost:8000/ai/generate-titles" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "In this video I reveal...",
    "platform": "youtube",
    "num_variations": 5
  }'
```

## Error Handling

### Common Errors

**400 Bad Request**
- Invalid platform value
- num_variations out of range (must be 3-15)
- Missing required field (transcript_text)

**404 Not Found**
- Clip ID doesn't exist (for clip-based endpoints)

**500 Internal Server Error**
- OpenRouter API failure
- All models failed to generate
- Network connectivity issues

### Error Response Format

```json
{
  "detail": "Error description here"
}
```

## Best Practices

### For Optimal Results

1. **Provide Context**: Include target_audience and key_topics for better targeting
2. **Test Multiple Platforms**: Same content performs differently on each platform
3. **Generate Variations**: Request 8-10 variations for best selection
4. **A/B Test**: Use multiple titles and test performance
5. **Iterate**: Use feedback to refine transcript summaries

### Performance Tips

1. **Batch Processing**: Use batch endpoint for multiple clips
2. **Caching**: Cache results for identical transcripts
3. **Async Processing**: All endpoints are async-ready
4. **Rate Limiting**: OpenRouter has rate limits, implement backoff

### Quality Guidelines

1. **Authentic Transcripts**: Better transcripts = better titles
2. **Length Matters**: 20-60 second clips work best
3. **Clear Topics**: Well-defined topics improve relevance
4. **Audience Specificity**: Narrow audiences get more targeted titles

## Testing

### Unit Tests

```bash
cd backend
pytest tests/ai/test_title_generator.py -v
```

### Integration Tests

```bash
pytest tests/api/test_ai_titles.py -v
```

### Manual Testing via Swagger

1. Start backend: `uvicorn src.main:app --reload`
2. Open: http://localhost:8000/docs
3. Navigate to "AI Title Generation" section
4. Try "POST /ai/generate-titles" endpoint
5. Use "Try it out" button

## Future Enhancements

### Planned Features

1. **Multi-Language Support**: Generate titles in multiple languages
2. **Trending Analysis**: Incorporate real-time trending topics
3. **Performance Tracking**: Track which titles perform best
4. **Custom Models**: Train custom models on your successful titles
5. **A/B Testing Integration**: Built-in A/B testing framework
6. **Sentiment Analysis**: Match title sentiment to video content
7. **Competitor Analysis**: Learn from competitor's successful titles
8. **SEO Optimization**: YouTube-specific SEO scoring

### Experimental Features

- **Voice/Tone Customization**: Match brand voice
- **Emoji Recommendations**: Platform-specific emoji suggestions
- **Hashtag Generation**: Automatic hashtag recommendations
- **Thumbnail Text Sync**: Coordinate with thumbnail text
- **Time-of-Day Optimization**: Best titles for posting times

## Support & Troubleshooting

### Common Issues

**"OpenRouter API key not configured"**
- Set `OPENROUTER_API_KEY` in `.env`
- Restart backend server

**"Failed to generate any titles"**
- Check OpenRouter account balance
- Verify API key is valid
- Check network connectivity

**"All models returned empty responses"**
- Transcript may be too short/empty
- Try different transcript content
- Check OpenRouter service status

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check logs at: `backend/logs/backend.log`

## License

Part of SupoClip - MIT License

## Contributing

Contributions welcome! Areas for improvement:
- Additional title styles
- New platform optimizations
- Enhanced virality scoring
- Better prompt engineering

---

**Documentation Version:** 1.0.0
**Last Updated:** 2025-11-10
**System:** SupoClip AI Title Generation
