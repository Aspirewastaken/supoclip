# SupoClip Webhook Examples

This directory contains example webhook receivers in different programming languages.

## Available Examples

### Python (Flask)
- **File:** `python_flask.py`
- **Requirements:** `pip install flask`
- **Usage:** `python python_flask.py`

### Node.js (Express)
- **File:** `nodejs_express.js`
- **Requirements:** `npm install express`
- **Usage:** `node nodejs_express.js`

## Quick Start

1. **Register a webhook** with SupoClip:

```bash
curl -X POST "http://localhost:8000/webhooks" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: your-user-id" \
  -d '{
    "url": "http://your-server:5000/webhooks/supoclip",
    "events": ["task.completed", "task.failed", "clips.ready"]
  }'
```

2. **Save the secret** from the response

3. **Update the example** with your webhook secret:
   - Python: Set `WEBHOOK_SECRET = "your-secret-here"`
   - Node.js: Set `const WEBHOOK_SECRET = 'your-secret-here'`

4. **Run the example** and start processing videos!

## Testing Locally

### Using ngrok

If you're developing locally, use ngrok to expose your webhook receiver:

```bash
# Start ngrok
ngrok http 5000

# Use the ngrok URL when registering your webhook
# Example: https://abc123.ngrok.io/webhooks/supoclip
```

### Using webhook.site

For quick testing without running code:

1. Visit https://webhook.site
2. Copy your unique URL
3. Register a webhook with that URL
4. Watch requests appear in real-time

## Security Notes

- **Always verify signatures** before processing webhooks
- **Use HTTPS** in production (required for security)
- **Store secrets securely** (environment variables, not code)
- **Respond quickly** (< 30 seconds to avoid timeouts)
- **Handle retries** (webhooks may be sent multiple times)

## See Also

- [Full Webhook Documentation](../WEBHOOKS.md)
- [API Reference](../WEBHOOKS.md#api-reference)
- [Troubleshooting Guide](../WEBHOOKS.md#troubleshooting)
