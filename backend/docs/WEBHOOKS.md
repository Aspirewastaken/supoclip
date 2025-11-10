# SupoClip Webhook System Documentation

## Overview

The SupoClip webhook system enables real-time notifications for task events. When a video processing task completes, fails, or generates clips, SupoClip can automatically send POST requests to your specified endpoints with event data.

## Features

- **Event-based notifications**: Subscribe to specific events (task completion, failures, clips ready)
- **HMAC signature validation**: Secure webhook payloads with SHA-256 signatures
- **Automatic retry logic**: Failed deliveries retry up to 3 times with exponential backoff
- **Delivery tracking**: Full audit trail of webhook attempts and responses
- **RESTful API**: Complete CRUD operations for webhook management

## Supported Events

| Event | Description | Triggered When |
|-------|-------------|----------------|
| `task.completed` | Task finished successfully | Video processing completes without errors |
| `task.failed` | Task encountered an error | Video processing fails for any reason |
| `clips.ready` | Clips are generated and available | All clips have been created and saved |

## Quick Start

### 1. Register a Webhook

```bash
curl -X POST "http://localhost:8000/webhooks" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: your-user-id" \
  -d '{
    "url": "https://your-domain.com/webhooks/supoclip",
    "events": ["task.completed", "clips.ready"]
  }'
```

**Response:**
```json
{
  "id": "webhook-123",
  "user_id": "your-user-id",
  "url": "https://your-domain.com/webhooks/supoclip",
  "events": ["task.completed", "clips.ready"],
  "secret": "vXQ8fK3mR9pL2nH6jC4wY1tE7sA0bD5gZ8",
  "active": true,
  "created_at": "2025-11-10T12:00:00Z",
  "updated_at": "2025-11-10T12:00:00Z"
}
```

**Important:** Store the `secret` securely - you'll need it to verify webhook signatures. It's only returned once at creation.

### 2. Receive Webhook Notifications

When an event occurs, SupoClip sends a POST request to your webhook URL:

```http
POST /webhooks/supoclip HTTP/1.1
Host: your-domain.com
Content-Type: application/json
X-Webhook-Signature: a1b2c3d4e5f6...
X-Webhook-Event: task.completed
User-Agent: SupoClip-Webhook/1.0

{
  "event": "task.completed",
  "timestamp": "2025-11-10T12:05:00Z",
  "data": {
    "task_id": "task-456",
    "user_id": "your-user-id",
    "task_status": "completed",
    "clips_generated": 5,
    "consensus_level": 0.85
  }
}
```

### 3. Verify Webhook Signatures

Always verify the `X-Webhook-Signature` header to ensure the request came from SupoClip:

#### Python Example

```python
import hmac
import hashlib
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

WEBHOOK_SECRET = "vXQ8fK3mR9pL2nH6jC4wY1tE7sA0bD5gZ8"  # From webhook registration

def verify_signature(payload, signature, secret):
    """Verify HMAC-SHA256 signature"""
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)

@app.route('/webhooks/supoclip', methods=['POST'])
def handle_webhook():
    # Get raw payload and signature
    payload = request.get_data(as_text=True)
    signature = request.headers.get('X-Webhook-Signature')
    event_type = request.headers.get('X-Webhook-Event')

    # Verify signature
    if not verify_signature(payload, signature, WEBHOOK_SECRET):
        return jsonify({"error": "Invalid signature"}), 401

    # Parse and process event
    data = json.loads(payload)

    if event_type == 'task.completed':
        print(f"Task {data['data']['task_id']} completed!")
        print(f"Generated {data['data'].get('clips_generated', 0)} clips")

    elif event_type == 'task.failed':
        print(f"Task {data['data']['task_id']} failed: {data['data'].get('error')}")

    elif event_type == 'clips.ready':
        print(f"Clips ready for task {data['data']['task_id']}")
        # Download clips, send notifications, etc.

    return jsonify({"status": "received"}), 200

if __name__ == '__main__':
    app.run(port=5000)
```

#### Node.js Example

```javascript
const express = require('express');
const crypto = require('crypto');

const app = express();
const WEBHOOK_SECRET = 'vXQ8fK3mR9pL2nH6jC4wY1tE7sA0bD5gZ8';

app.use(express.json());

function verifySignature(payload, signature, secret) {
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(expectedSignature),
    Buffer.from(signature)
  );
}

app.post('/webhooks/supoclip', (req, res) => {
  const payload = JSON.stringify(req.body);
  const signature = req.headers['x-webhook-signature'];
  const eventType = req.headers['x-webhook-event'];

  // Verify signature
  if (!verifySignature(payload, signature, WEBHOOK_SECRET)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  // Process event
  const { event, timestamp, data } = req.body;

  switch (eventType) {
    case 'task.completed':
      console.log(`Task ${data.task_id} completed!`);
      console.log(`Generated ${data.clips_generated || 0} clips`);
      break;

    case 'task.failed':
      console.log(`Task ${data.task_id} failed: ${data.error}`);
      break;

    case 'clips.ready':
      console.log(`Clips ready for task ${data.task_id}`);
      // Download clips, send notifications, etc.
      break;
  }

  res.json({ status: 'received' });
});

app.listen(5000, () => {
  console.log('Webhook receiver running on port 5000');
});
```

## API Reference

### Create Webhook

**Endpoint:** `POST /webhooks`

**Headers:**
- `X-User-Id: <user-id>` (required)
- `Content-Type: application/json`

**Request Body:**
```json
{
  "url": "https://your-domain.com/webhook-endpoint",
  "events": ["task.completed", "clips.ready"],
  "secret": "optional-custom-secret"  // Auto-generated if omitted
}
```

**Response:** `201 Created`
```json
{
  "id": "webhook-123",
  "user_id": "user-456",
  "url": "https://your-domain.com/webhook-endpoint",
  "events": ["task.completed", "clips.ready"],
  "secret": "auto-generated-secret",
  "active": true,
  "created_at": "2025-11-10T12:00:00Z",
  "updated_at": "2025-11-10T12:00:00Z"
}
```

---

### List Webhooks

**Endpoint:** `GET /webhooks`

**Headers:**
- `X-User-Id: <user-id>` (required)

**Query Parameters:**
- `active_only` (boolean, default: `true`) - Only return active webhooks

**Response:** `200 OK`
```json
{
  "webhooks": [
    {
      "id": "webhook-123",
      "user_id": "user-456",
      "url": "https://your-domain.com/webhook-endpoint",
      "events": ["task.completed"],
      "secret": "secret-123",
      "active": true,
      "created_at": "2025-11-10T12:00:00Z",
      "updated_at": "2025-11-10T12:00:00Z"
    }
  ],
  "total": 1
}
```

---

### Get Webhook

**Endpoint:** `GET /webhooks/{webhook_id}`

**Headers:**
- `X-User-Id: <user-id>` (required)

**Response:** `200 OK`
```json
{
  "id": "webhook-123",
  "user_id": "user-456",
  "url": "https://your-domain.com/webhook-endpoint",
  "events": ["task.completed"],
  "secret": "secret-123",
  "active": true,
  "created_at": "2025-11-10T12:00:00Z",
  "updated_at": "2025-11-10T12:00:00Z"
}
```

---

### Update Webhook

**Endpoint:** `PATCH /webhooks/{webhook_id}`

**Headers:**
- `X-User-Id: <user-id>` (required)
- `Content-Type: application/json`

**Request Body** (all fields optional):
```json
{
  "url": "https://new-url.com/webhook",
  "events": ["task.completed", "task.failed", "clips.ready"],
  "active": false
}
```

**Response:** `200 OK`
```json
{
  "id": "webhook-123",
  "user_id": "user-456",
  "url": "https://new-url.com/webhook",
  "events": ["task.completed", "task.failed", "clips.ready"],
  "secret": "secret-123",
  "active": false,
  "created_at": "2025-11-10T12:00:00Z",
  "updated_at": "2025-11-10T13:00:00Z"
}
```

---

### Delete Webhook

**Endpoint:** `DELETE /webhooks/{webhook_id}`

**Headers:**
- `X-User-Id: <user-id>` (required)

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Webhook webhook-123 deleted successfully"
}
```

---

### Get Supported Events

**Endpoint:** `GET /webhooks/events/supported`

**Response:** `200 OK`
```json
{
  "events": [
    "task.completed",
    "task.failed",
    "clips.ready"
  ],
  "descriptions": {
    "task.completed": "Triggered when a video processing task completes successfully",
    "task.failed": "Triggered when a video processing task fails",
    "clips.ready": "Triggered when clips are generated and ready for download"
  }
}
```

## Webhook Payloads

### task.completed

```json
{
  "event": "task.completed",
  "timestamp": "2025-11-10T12:05:00Z",
  "data": {
    "task_id": "task-456",
    "user_id": "user-123",
    "task_status": "completed",
    "clips_generated": 5,
    "target_clips": 5,
    "consensus_level": 0.85,
    "clips": [
      {
        "id": "clip-1",
        "filename": "clip_1_00-15_00-45.mp4",
        "start_time": "00:15",
        "end_time": "00:45",
        "duration": 30.0,
        "relevance_score": 0.92
      }
    ]
  }
}
```

### task.failed

```json
{
  "event": "task.failed",
  "timestamp": "2025-11-10T12:05:00Z",
  "data": {
    "task_id": "task-456",
    "user_id": "user-123",
    "task_status": "error",
    "error": "Video transcription failed: Invalid video format"
  }
}
```

### clips.ready

```json
{
  "event": "clips.ready",
  "timestamp": "2025-11-10T12:05:00Z",
  "data": {
    "task_id": "task-456",
    "user_id": "user-123",
    "task_status": "completed",
    "clips_count": 5,
    "clips": [
      {
        "id": "clip-1",
        "filename": "clip_1_00-15_00-45.mp4",
        "start_time": "00:15",
        "end_time": "00:45",
        "duration": 30.0,
        "relevance_score": 0.92
      }
    ]
  }
}
```

## Retry Logic

SupoClip automatically retries failed webhook deliveries:

- **Max attempts:** 3
- **Retry schedule:**
  - 1st retry: 1 minute after failure
  - 2nd retry: 5 minutes after 1st retry
  - 3rd retry: 15 minutes after 2nd retry

A delivery is considered **successful** if your endpoint returns HTTP status 200-299.

A delivery is considered **failed** if:
- HTTP status is 4xx or 5xx
- Request times out (30 seconds)
- Network error occurs

## Best Practices

### 1. Validate Signatures

Always verify the `X-Webhook-Signature` header to prevent unauthorized requests:

```python
def verify_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### 2. Return 200 Quickly

Process webhooks asynchronously to avoid timeouts:

```python
@app.route('/webhooks/supoclip', methods=['POST'])
def handle_webhook():
    # Verify signature
    if not verify_signature(...):
        return jsonify({"error": "Invalid signature"}), 401

    # Queue for async processing
    celery_task.delay(request.get_json())

    # Return immediately
    return jsonify({"status": "received"}), 200
```

### 3. Handle Idempotency

You may receive duplicate webhooks (due to retries). Use the `task_id` to deduplicate:

```python
processed_tasks = set()

@app.route('/webhooks/supoclip', methods=['POST'])
def handle_webhook():
    data = request.get_json()
    task_id = data['data']['task_id']

    if task_id in processed_tasks:
        return jsonify({"status": "already processed"}), 200

    # Process webhook
    process_event(data)
    processed_tasks.add(task_id)

    return jsonify({"status": "received"}), 200
```

### 4. Use HTTPS

Always use HTTPS webhook URLs in production to ensure payload security:

```bash
# Good
"url": "https://your-domain.com/webhooks/supoclip"

# Bad (development only)
"url": "http://your-domain.com/webhooks/supoclip"
```

### 5. Monitor Webhook Health

Check webhook delivery status in your database:

```sql
-- View recent webhook deliveries
SELECT
    webhook_id,
    event_type,
    status,
    attempts,
    response_code,
    created_at,
    delivered_at
FROM webhook_deliveries
WHERE webhook_id = 'webhook-123'
ORDER BY created_at DESC
LIMIT 10;
```

## Testing Webhooks

### Using webhook.site

1. Go to https://webhook.site
2. Copy your unique URL
3. Register webhook:

```bash
curl -X POST "http://localhost:8000/webhooks" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test-user" \
  -d '{
    "url": "https://webhook.site/your-unique-id",
    "events": ["task.completed", "task.failed", "clips.ready"]
  }'
```

4. Process a video and watch requests appear on webhook.site

### Using ngrok (Local Testing)

1. Start ngrok:
```bash
ngrok http 5000
```

2. Register webhook with ngrok URL:
```bash
curl -X POST "http://localhost:8000/webhooks" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: test-user" \
  -d '{
    "url": "https://your-ngrok-url.ngrok.io/webhooks/supoclip",
    "events": ["task.completed"]
  }'
```

3. Run your local webhook receiver on port 5000

## Troubleshooting

### Webhook Not Receiving Events

**Check 1:** Verify webhook is active
```bash
curl -X GET "http://localhost:8000/webhooks" \
  -H "X-User-Id: your-user-id"
```

**Check 2:** Verify subscribed events
```bash
# Make sure your webhook includes the event you're expecting
{
  "events": ["task.completed", "clips.ready"]
}
```

**Check 3:** Check delivery logs
```sql
SELECT * FROM webhook_deliveries
WHERE webhook_id = 'your-webhook-id'
ORDER BY created_at DESC;
```

### Signature Validation Failing

**Issue:** Getting 401 errors when verifying signatures

**Solution:** Ensure you're using the exact payload body:

```python
# CORRECT - Use raw payload
payload = request.get_data(as_text=True)
signature = request.headers.get('X-Webhook-Signature')
verify_signature(payload, signature, secret)

# WRONG - Don't re-serialize JSON
payload = json.dumps(request.get_json())  # This will fail!
```

### Webhook Timing Out

**Issue:** Deliveries failing with timeout errors

**Solution:** Ensure your endpoint responds within 30 seconds:

```python
@app.route('/webhooks/supoclip', methods=['POST'])
def handle_webhook():
    # Queue for background processing
    background_task.delay(request.get_json())

    # Return immediately (< 30s)
    return jsonify({"status": "received"}), 200
```

## Security Considerations

1. **Always verify signatures** - Never trust webhook payloads without signature verification
2. **Use HTTPS** - Encrypt webhook traffic in production
3. **Store secrets securely** - Use environment variables or secret managers
4. **Rate limit** - Protect your webhook endpoint from abuse
5. **Validate input** - Sanitize webhook data before processing
6. **Monitor failures** - Alert on repeated delivery failures

## Database Schema

### webhooks table

```sql
CREATE TABLE webhooks (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    url VARCHAR(1000) NOT NULL,
    events TEXT[] NOT NULL DEFAULT '{}',
    secret VARCHAR(255) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### webhook_deliveries table

```sql
CREATE TABLE webhook_deliveries (
    id VARCHAR(36) PRIMARY KEY,
    webhook_id VARCHAR(36) NOT NULL REFERENCES webhooks(id),
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'success', 'failed')),
    response_code INTEGER,
    response_body TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP WITH TIME ZONE
);
```

## Support

For webhook-related issues:
- GitHub Issues: https://github.com/yourusername/supoclip/issues
- Documentation: https://supoclip.com/docs/webhooks
- Email: support@supoclip.com
