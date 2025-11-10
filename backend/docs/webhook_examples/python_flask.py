"""
SupoClip Webhook Receiver - Flask Example

This example demonstrates how to receive and verify webhook notifications
from SupoClip using Flask.

Requirements:
    pip install flask

Usage:
    python python_flask.py
"""

import hmac
import hashlib
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# Replace with your webhook secret from registration response
WEBHOOK_SECRET = "your-webhook-secret-here"


def verify_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Verify HMAC-SHA256 signature for webhook payload.

    Args:
        payload: Raw JSON string from request body
        signature: Signature from X-Webhook-Signature header
        secret: Your webhook secret

    Returns:
        True if signature is valid, False otherwise
    """
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)


@app.route('/webhooks/supoclip', methods=['POST'])
def handle_webhook():
    """Handle incoming webhook from SupoClip"""

    # Get raw payload and headers
    payload = request.get_data(as_text=True)
    signature = request.headers.get('X-Webhook-Signature')
    event_type = request.headers.get('X-Webhook-Event')

    # Verify signature
    if not signature:
        return jsonify({"error": "Missing signature"}), 401

    if not verify_signature(payload, signature, WEBHOOK_SECRET):
        return jsonify({"error": "Invalid signature"}), 401

    # Parse event data
    try:
        event_data = json.loads(payload)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON"}), 400

    # Handle different event types
    if event_type == 'task.completed':
        handle_task_completed(event_data)
    elif event_type == 'task.failed':
        handle_task_failed(event_data)
    elif event_type == 'clips.ready':
        handle_clips_ready(event_data)
    else:
        print(f"Unknown event type: {event_type}")

    return jsonify({"status": "received"}), 200


def handle_task_completed(event_data: dict):
    """Handle task.completed event"""
    data = event_data['data']
    task_id = data['task_id']
    clips_generated = data.get('clips_generated', 0)

    print(f"✅ Task {task_id} completed!")
    print(f"   Generated {clips_generated} clips")

    # Your business logic here:
    # - Send email notification
    # - Update database
    # - Trigger downstream workflows
    # - etc.


def handle_task_failed(event_data: dict):
    """Handle task.failed event"""
    data = event_data['data']
    task_id = data['task_id']
    error = data.get('error', 'Unknown error')

    print(f"❌ Task {task_id} failed!")
    print(f"   Error: {error}")

    # Your business logic here:
    # - Send alert notification
    # - Log error for debugging
    # - Retry with different settings
    # - etc.


def handle_clips_ready(event_data: dict):
    """Handle clips.ready event"""
    data = event_data['data']
    task_id = data['task_id']
    clips = data.get('clips', [])

    print(f"📹 Clips ready for task {task_id}")
    print(f"   Available clips: {len(clips)}")

    for clip in clips:
        print(f"   - {clip['filename']} ({clip['duration']}s)")

    # Your business logic here:
    # - Download clips via API
    # - Upload to storage bucket
    # - Schedule social media posts
    # - etc.


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


if __name__ == '__main__':
    print("🚀 SupoClip Webhook Receiver started")
    print(f"📡 Listening on http://localhost:5000/webhooks/supoclip")
    print(f"🔐 Using secret: {WEBHOOK_SECRET[:8]}...")
    app.run(host='0.0.0.0', port=5000, debug=True)
