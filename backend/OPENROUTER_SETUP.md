# OpenRouter Setup Guide for AI Title Generation

## Quick Start

### 1. Get OpenRouter API Key

1. Visit https://openrouter.ai/
2. Sign up or log in
3. Navigate to "Keys" in the dashboard
4. Click "Create Key"
5. Copy your API key

### 2. Add to Environment

Add to your `backend/.env` file:

```env
# OpenRouter Configuration for AI Title Generation
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxx
OPENROUTER_REFERER=http://localhost:3000
```

### 3. Add Credits

OpenRouter requires credits for API usage:

1. Go to https://openrouter.ai/credits
2. Add credits ($5-10 is sufficient for testing)
3. Pricing: ~$0.70 per 1,000 titles generated

### 4. Test the System

Start the backend:

```bash
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload
```

Visit the API docs: http://localhost:8000/docs

Navigate to "AI Title Generation" section and test the endpoint.

## Environment Variables

### Required

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

Your OpenRouter API key for accessing multiple LLMs.

### Optional

```env
OPENROUTER_REFERER=http://localhost:3000
```

Your application URL (for OpenRouter tracking/analytics).
Default: http://localhost:3000

## Models Used

The system automatically uses these standardized 5-model council via OpenRouter:

1. **anthropic/claude-sonnet-4-20250514** (Claude Sonnet 4.5) - $3/1M input tokens
2. **anthropic/claude-opus-4-20250514** (Claude Opus 4.1) - $15/1M input tokens
3. **openai/gpt-4-turbo-preview** (GPT-4 Turbo) - $10/1M input tokens
4. **google/gemini-pro-1.5** (Gemini 2.5 Pro) - $1.25/1M input tokens
5. **deepseek/deepseek-chat** (DeepSeek Chat) - $0.14/1M input tokens

Average cost per title generation: **~$0.0058**

## Testing

### Quick API Test

```bash
curl -X POST "http://localhost:8000/ai/generate-titles" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "Today I am going to show you the secret to growing your social media presence from zero to 100k followers in just 90 days. Most people dont know this but the algorithm actually favors...",
    "platform": "tiktok",
    "num_variations": 5
  }'
```

Expected response: JSON with 5 title variations and scores.

### Python Test

```python
import requests

response = requests.post(
    "http://localhost:8000/ai/generate-titles",
    json={
        "transcript_text": "Your video transcript here...",
        "platform": "instagram",
        "num_variations": 3
    }
)

print(response.json())
```

## Troubleshooting

### "OpenRouter API key not configured"

**Solution:** Set `OPENROUTER_API_KEY` in `.env` and restart server.

### "Insufficient credits"

**Solution:** Add credits at https://openrouter.ai/credits

### "Rate limit exceeded"

**Solution:** OpenRouter has rate limits. Wait a few seconds and retry.

### "All models failed to generate"

**Possible causes:**
- No credits remaining
- Network connectivity issue
- OpenRouter service outage
- Invalid API key

**Solution:** Check OpenRouter dashboard and verify service status.

## Cost Management

### Estimating Usage

- **Per title request:** ~$0.0007 (8 variations)
- **Per 100 requests:** ~$0.07
- **Per 1,000 requests:** ~$0.70
- **Per 10,000 requests:** ~$7.00

### Optimization Tips

1. **Reduce variations:** Use `num_variations: 3-5` instead of 8-10
2. **Cache results:** Cache titles for repeated transcripts
3. **Batch processing:** Use batch endpoint for multiple clips
4. **Use cheaper models:** Gemini Flash is 40x cheaper than GPT-4

### Setting Up Budgets

OpenRouter allows setting monthly budgets:

1. Go to https://openrouter.ai/settings
2. Set monthly spending limit
3. Get alerts when approaching limit

## Production Deployment

### Security

**DO NOT** commit `.env` file with API key!

Use environment variables in production:

```bash
export OPENROUTER_API_KEY="your-key"
export OPENROUTER_REFERER="https://yourdomain.com"
```

### Docker

Add to `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - OPENROUTER_REFERER=${OPENROUTER_REFERER}
```

### Rate Limiting

Implement rate limiting in production:

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@router.post("/generate-titles", dependencies=[Depends(RateLimiter(times=10, minutes=1))])
async def generate_titles(request: TitleGenerationRequest):
    ...
```

## API Key Management

### Rotation

Rotate keys regularly for security:

1. Create new key in OpenRouter dashboard
2. Update `.env` with new key
3. Restart service
4. Delete old key after verification

### Multiple Keys

For high-volume applications, use multiple keys:

```env
OPENROUTER_API_KEY_1=sk-or-v1-key1
OPENROUTER_API_KEY_2=sk-or-v1-key2
OPENROUTER_API_KEY_3=sk-or-v1-key3
```

Implement round-robin or load balancing in code.

## Monitoring

### OpenRouter Dashboard

Monitor usage at: https://openrouter.ai/activity

View:
- Request count
- Token usage
- Cost breakdown
- Error rates
- Model distribution

### Application Logging

Logs are written to: `backend/logs/backend.log`

```bash
# Monitor logs
tail -f backend/logs/backend.log | grep "title"
```

## Support

### OpenRouter Support

- Discord: https://discord.gg/openrouter
- Email: support@openrouter.ai
- Docs: https://openrouter.ai/docs

### SupoClip Support

For issues with the title generation system:

1. Check logs: `backend/logs/backend.log`
2. Verify OpenRouter dashboard for errors
3. Test with simple request first
4. Check GitHub issues

## Advanced Configuration

### Custom Model Selection

The system uses a standardized 5-model council. To view the configuration, see `/home/user/supoclip/backend/src/ai/title_generator.py`:

```python
OPENROUTER_MODELS = [
    "anthropic/claude-sonnet-4-20250514",
    "anthropic/claude-opus-4-20250514",
    "openai/gpt-4-turbo-preview",
    "google/gemini-pro-1.5",
    "deepseek/deepseek-chat",
]
```

**Note**: These models match the council deliberation system for consistency across the application.

### Temperature Tuning

Adjust creativity vs consistency:

```python
# In title_generator.py, _call_openrouter method
temperature = 0.9  # Higher = more creative (0.0-2.0)
```

### Timeout Configuration

Adjust API timeout:

```python
timeout = aiohttp.ClientTimeout(total=30)  # seconds
```

## Best Practices

1. **Start Small**: Test with 3-5 variations first
2. **Monitor Costs**: Check OpenRouter dashboard regularly
3. **Cache Results**: Avoid regenerating identical requests
4. **Set Budgets**: Use OpenRouter's budget limits
5. **Error Handling**: Implement proper error handling and retries
6. **Rate Limiting**: Implement rate limiting in production
7. **Key Security**: Never expose API keys in client-side code

## FAQ

**Q: Do I need all 5 models?**
A: No, the system cycles through available models. If one fails, it continues with others.

**Q: Can I use my own API keys (OpenAI, Anthropic, etc.)?**
A: OpenRouter is recommended for simplicity, but you can modify the code to use direct API calls.

**Q: How many requests can I make?**
A: OpenRouter has generous rate limits. For most users, the limit is your budget, not rate limits.

**Q: Can I use free models?**
A: Yes! Change to free models like `meta-llama/llama-3-8b-instruct` in the model list.

**Q: Is my data private?**
A: OpenRouter processes requests but doesn't train on your data. See their privacy policy for details.

---

**Last Updated:** 2025-11-10
