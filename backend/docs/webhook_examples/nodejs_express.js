/**
 * SupoClip Webhook Receiver - Express.js Example
 *
 * This example demonstrates how to receive and verify webhook notifications
 * from SupoClip using Express.js.
 *
 * Requirements:
 *   npm install express
 *
 * Usage:
 *   node nodejs_express.js
 */

const express = require('express');
const crypto = require('crypto');

const app = express();
const PORT = 5000;

// Replace with your webhook secret from registration response
const WEBHOOK_SECRET = 'your-webhook-secret-here';

// Middleware to capture raw body for signature verification
app.use(express.json({
  verify: (req, res, buf) => {
    req.rawBody = buf.toString('utf8');
  }
}));

/**
 * Verify HMAC-SHA256 signature for webhook payload
 *
 * @param {string} payload - Raw JSON string from request body
 * @param {string} signature - Signature from X-Webhook-Signature header
 * @param {string} secret - Your webhook secret
 * @returns {boolean} True if signature is valid, false otherwise
 */
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

/**
 * Handle incoming webhook from SupoClip
 */
app.post('/webhooks/supoclip', (req, res) => {
  // Get raw payload and headers
  const payload = req.rawBody;
  const signature = req.headers['x-webhook-signature'];
  const eventType = req.headers['x-webhook-event'];

  // Verify signature
  if (!signature) {
    return res.status(401).json({ error: 'Missing signature' });
  }

  if (!verifySignature(payload, signature, WEBHOOK_SECRET)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  // Parse event data
  const eventData = req.body;

  // Handle different event types
  switch (eventType) {
    case 'task.completed':
      handleTaskCompleted(eventData);
      break;

    case 'task.failed':
      handleTaskFailed(eventData);
      break;

    case 'clips.ready':
      handleClipsReady(eventData);
      break;

    default:
      console.log(`Unknown event type: ${eventType}`);
  }

  res.json({ status: 'received' });
});

/**
 * Handle task.completed event
 */
function handleTaskCompleted(eventData) {
  const { data } = eventData;
  const taskId = data.task_id;
  const clipsGenerated = data.clips_generated || 0;

  console.log(`✅ Task ${taskId} completed!`);
  console.log(`   Generated ${clipsGenerated} clips`);

  // Your business logic here:
  // - Send email notification
  // - Update database
  // - Trigger downstream workflows
  // - etc.
}

/**
 * Handle task.failed event
 */
function handleTaskFailed(eventData) {
  const { data } = eventData;
  const taskId = data.task_id;
  const error = data.error || 'Unknown error';

  console.log(`❌ Task ${taskId} failed!`);
  console.log(`   Error: ${error}`);

  // Your business logic here:
  // - Send alert notification
  // - Log error for debugging
  // - Retry with different settings
  // - etc.
}

/**
 * Handle clips.ready event
 */
function handleClipsReady(eventData) {
  const { data } = eventData;
  const taskId = data.task_id;
  const clips = data.clips || [];

  console.log(`📹 Clips ready for task ${taskId}`);
  console.log(`   Available clips: ${clips.length}`);

  clips.forEach(clip => {
    console.log(`   - ${clip.filename} (${clip.duration}s)`);
  });

  // Your business logic here:
  // - Download clips via API
  // - Upload to storage bucket
  // - Schedule social media posts
  // - etc.
}

/**
 * Health check endpoint
 */
app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

// Start server
app.listen(PORT, () => {
  console.log('🚀 SupoClip Webhook Receiver started');
  console.log(`📡 Listening on http://localhost:${PORT}/webhooks/supoclip`);
  console.log(`🔐 Using secret: ${WEBHOOK_SECRET.substring(0, 8)}...`);
});
