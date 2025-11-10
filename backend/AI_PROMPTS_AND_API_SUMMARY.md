# AI Title Generation - Prompts & API Summary

## Quick Reference

**Files Created:**
- `/home/user/supoclip/backend/src/ai/title_generator.py` - Main title generation module
- `/home/user/supoclip/backend/src/api/routes/ai_titles.py` - API endpoints
- `/home/user/supoclip/backend/src/ai/__init__.py` - Module initialization
- `/home/user/supoclip/backend/AI_TITLE_GENERATION_DOCS.md` - Complete documentation
- `/home/user/supoclip/backend/OPENROUTER_SETUP.md` - Setup guide

**Configuration Required:**
```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_REFERER=http://localhost:3000
```

---

## AI PROMPTS USED

### System Prompt (Dynamic Template)

The system adapts this prompt based on platform and audience:

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

### Platform-Specific Style Prompts

**TikTok:**
```
"casual, trendy, uses slang, creates FOMO, hooks in first 3 words"
Character limit: 150
Optimal length: 50-100 characters
```

**Instagram:**
```
"aesthetic, aspirational, uses emojis strategically, creates desire"
Character limit: 125
Optimal length: 40-90 characters
```

**YouTube:**
```
"search-optimized, clear value proposition, includes keywords"
Character limit: 100
Optimal length: 50-80 characters
```

**Twitter:**
```
"punchy, conversational, thread-starter potential"
Character limit: 280
Optimal length: 60-100 characters
```

**LinkedIn:**
```
"professional, thought-leadership, industry insights"
Character limit: 120
Optimal length: 40-90 characters
```

### User Prompt (Dynamic Template)

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

When a specific style is requested, one of these instructions is added:

| Style | Instruction |
|-------|-------------|
| **Question** | "Create a compelling question that makes viewers curious" |
| **Shocking** | "Use surprising or shocking elements to grab attention" |
| **How-To** | "Frame as educational/tutorial (how to, guide to, etc.)" |
| **Listicle** | "Use number-based format (X ways to, X things, etc.)" |
| **Story** | "Tell it as a narrative or story hook" |
| **Direct** | "Be direct and straightforward about the value" |
| **Curiosity** | "Create a curiosity gap without revealing everything" |
| **Emotional** | "Lead with emotional hook (excitement, inspiration, etc.)" |

---

## API ENDPOINTS

### Base URL
```
http://localhost:8000
```

### 1. Generate Titles

**Endpoint:** `POST /ai/generate-titles`

**Request:**
```json
{
  "transcript_text": "Your video transcript here...",
  "platform": "tiktok",
  "target_audience": "young entrepreneurs",
  "key_topics": ["business", "growth"],
  "duration_seconds": 32.5,
  "num_variations": 8,
  "include_styles": ["question", "shocking"]
}
```

**Response:**
```json
{
  "titles": [
    {
      "title": "The $1M Secret Nobody Tells You",
      "style": "curiosity",
      "virality_score": 0.87,
      "reasoning": "Creates information gap that drives clicks...",
      "character_count": 33,
      "model_used": "claude-3.5-sonnet"
    }
  ],
  "best_title": { /* ... */ },
  "platform": "tiktok",
  "total_generated": 8
}
```

### 2. Generate for Existing Clip

**Endpoint:** `POST /ai/generate-titles/clip/{clip_id}?platform=instagram&num_variations=5`

**Response:** Same as above

### 3. Batch Generation

**Endpoint:** `POST /ai/generate-titles/batch`

**Request:**
```json
{
  "clip_ids": ["clip-1", "clip-2", "clip-3"],
  "platform": "youtube",
  "num_variations": 5
}
```

**Response:**
```json
{
  "results": {
    "clip-1": { /* TitleGenerationResponse */ },
    "clip-2": { /* TitleGenerationResponse */ }
  },
  "total_clips": 3,
  "successful": 2,
  "failed": 1
}
```

### 4. Get Title Styles

**Endpoint:** `GET /ai/title-styles`

**Response:**
```json
{
  "styles": {
    "question": {
      "name": "Question",
      "description": "Starts with a question to create curiosity",
      "example": "Why Are People Obsessed With This?"
    }
  },
  "total": 8
}
```

### 5. Get Platforms

**Endpoint:** `GET /ai/platforms`

**Response:**
```json
{
  "platforms": {
    "tiktok": {
      "name": "TikTok",
      "character_limit": 150,
      "style": "casual, trendy, uses slang...",
      "optimal_length": "50-100 characters"
    }
  },
  "total": 5
}
```

---

## VIRALITY SCORING ALGORITHM

### Components & Weights

1. **Length Optimization** (±0.15-0.20 points)
   - Within optimal range: +0.15
   - Exceeds character limit: -0.20

2. **Power Words** (+0.05 each, max +0.15)
   - secret, revealed, shocking, amazing, ultimate
   - proven, guaranteed, exclusive, breakthrough
   - you, your, why, how, what
   - best, worst, truth, exposed, warning

3. **Number Present** (+0.10)
   - Any specific number in title

4. **Question Format** (+0.10)
   - Contains '?'

5. **Strong First Word** (+0.08)
   - why, how, what, this, the, watch, stop, wait

6. **Emotional Words** (+0.07)
   - love, fear, dream, excited, amazing

7. **Style Bonuses** (+0.05-0.09)
   - Curiosity: +0.09
   - Shocking: +0.08
   - Listicle: +0.07
   - How-To: +0.06
   - Question: +0.05

### Score Interpretation

| Range | Interpretation |
|-------|----------------|
| 0.8-1.0 | High virality potential |
| 0.6-0.8 | Strong potential |
| 0.4-0.6 | Moderate potential |
| 0.0-0.4 | Needs optimization |

---

## MODELS USED

Via OpenRouter API - cycles through these 5 models:

1. **anthropic/claude-3.5-sonnet**
   - Creative, nuanced language
   - Cost: ~$0.003 per request

2. **openai/gpt-4-turbo**
   - High quality, versatile
   - Cost: ~$0.010 per request

3. **google/gemini-2.0-flash-001**
   - Fast, efficient
   - Cost: ~$0.0001 per request

4. **meta-llama/llama-3.1-70b-instruct**
   - Open source, strong performance
   - Cost: ~$0.0004 per request

5. **mistralai/mistral-large-2407**
   - European perspective, multilingual
   - Cost: ~$0.002 per request

**Average cost per request (8 variations):** ~$0.0007

---

## QUICK START

### 1. Setup

```bash
# Add to backend/.env
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Get key at: https://openrouter.ai/
```

### 2. Start Server

```bash
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload
```

### 3. Test

```bash
# Via Swagger UI
open http://localhost:8000/docs

# Via cURL
curl -X POST "http://localhost:8000/ai/generate-titles" \
  -H "Content-Type: application/json" \
  -d '{"transcript_text": "Your text here", "num_variations": 3}'

# Via Test Script
./backend/examples/test_api_endpoints.sh
```

### 4. Use in Code

```python
from src.ai.title_generator import generate_titles_for_clip

response = await generate_titles_for_clip(
    transcript="Your video transcript...",
    platform="tiktok",
    num_variations=8
)

print(f"Best: {response.best_title.title}")
print(f"Score: {response.best_title.virality_score}")
```

---

## EXAMPLE PROMPTS & RESPONSES

### Example 1: TikTok Business Content

**Input:**
```
Transcript: "In this video I reveal the secret strategy that helped me grow
my business from zero to one million dollars in just 18 months..."

Platform: tiktok
Variations: 5
```

**System sees:**
```
Platform: TIKTOK
Character Limit: 150
Style: casual, trendy, uses slang, creates FOMO, hooks in first 3 words
```

**Sample Outputs:**
1. [0.89] "The $1M Secret They Don't Want You to Know" (curiosity)
2. [0.85] "How I Grew From $0 to $1M in 18 Months" (how_to)
3. [0.83] "What Made Me $1 Million Nobody Talks About" (curiosity)
4. [0.81] "Why 99% of Businesses Fail at This" (question)
5. [0.78] "I Made $1M Doing This One Thing" (direct)

### Example 2: Instagram Lifestyle Content

**Input:**
```
Transcript: "Today I'm sharing my morning routine that completely
transformed my productivity and energy levels..."

Platform: instagram
Audience: young professionals
Variations: 3
```

**System sees:**
```
Platform: INSTAGRAM
Character Limit: 125
Style: aesthetic, aspirational, uses emojis strategically, creates desire
Target Audience: young professionals
```

**Sample Outputs:**
1. [0.87] "The Morning Routine That Changed Everything" (direct)
2. [0.84] "Why I Wake Up at 5 AM Every Day" (question)
3. [0.81] "Transform Your Life With This Simple Routine" (emotional)

### Example 3: YouTube Educational Content

**Input:**
```
Transcript: "Let me show you the psychology behind viral content
and why certain videos get millions of views..."

Platform: youtube
Topics: ["viral content", "video marketing"]
Variations: 3
```

**System sees:**
```
Platform: YOUTUBE
Character Limit: 100
Style: search-optimized, clear value proposition, includes keywords
Topics: viral content, video marketing
```

**Sample Outputs:**
1. [0.88] "The Psychology Behind Viral Videos Explained" (how_to)
2. [0.85] "Why Your Videos Aren't Going Viral" (question)
3. [0.82] "Viral Content Formula: 3 Key Principles" (listicle)

---

## TESTING

### Unit Test
```bash
pytest backend/tests/ai/test_title_generator.py -v
```

### API Test
```bash
cd backend/examples
./test_api_endpoints.sh
```

### Manual Test (Python)
```bash
cd backend
python examples/test_title_generation.py
```

---

## COST ESTIMATION

| Usage | Cost |
|-------|------|
| Single request (8 variations) | $0.0007 |
| 100 requests | $0.07 |
| 1,000 requests | $0.70 |
| 10,000 requests | $7.00 |

---

## ERROR HANDLING

### Common Errors

**"OpenRouter API key not configured"**
```
Solution: Set OPENROUTER_API_KEY in .env
```

**"Failed to generate any titles"**
```
Possible causes:
- Insufficient OpenRouter credits
- Invalid API key
- Network issue
- OpenRouter service down
```

**"Validation error"**
```
Causes:
- Invalid platform value
- num_variations out of range (3-15)
- Missing transcript_text
```

---

## DOCUMENTATION FILES

1. **AI_TITLE_GENERATION_DOCS.md** - Complete documentation (19KB)
   - Full API reference
   - Detailed prompts
   - Configuration guide
   - Examples

2. **OPENROUTER_SETUP.md** - Setup guide (7KB)
   - Quick start instructions
   - Cost management
   - Production deployment
   - Troubleshooting

3. **src/ai/README.md** - Module overview
   - Quick usage
   - Development guide
   - Testing instructions

4. **examples/test_title_generation.py** - Python examples
   - 6 different usage patterns
   - Error handling demos

5. **examples/test_api_endpoints.sh** - API tests
   - Automated endpoint testing
   - Response validation

---

## SWAGGER UI

Interactive API documentation available at:
```
http://localhost:8000/docs
```

Navigate to **"AI Title Generation"** section to:
- Try endpoints interactively
- See request/response schemas
- Test with sample data
- View all parameters

---

## SUPPORT

**Repository:** `/home/user/supoclip/backend`

**Key Files:**
- Implementation: `src/ai/title_generator.py`
- API Routes: `src/api/routes/ai_titles.py`
- Main App: `src/main.py` (line 35, 68)

**Logs:**
- Application: `backend/logs/backend.log`
- Search for "title" to see generation logs

**OpenRouter:**
- Dashboard: https://openrouter.ai/activity
- Docs: https://openrouter.ai/docs
- Support: https://discord.gg/openrouter

---

**Version:** 1.0.0
**Created:** 2025-11-10
**System:** SupoClip AI Title Generation
