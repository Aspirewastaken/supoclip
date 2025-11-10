"""
Webhook Manager - Handles webhook registration, delivery, retry logic, and signature validation
"""

import asyncio
import hmac
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import httpx
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Webhook, WebhookDelivery, Task, GeneratedClip
from ..database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class WebhookManager:
    """Manages webhook lifecycle: registration, delivery, retries, and validation"""

    # Supported webhook events
    SUPPORTED_EVENTS = [
        "task.completed",
        "task.failed",
        "clips.ready"
    ]

    # Retry configuration
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAYS = [60, 300, 900]  # Retry after 1min, 5min, 15min

    # HTTP timeout for webhook delivery
    DELIVERY_TIMEOUT = 30.0  # 30 seconds

    def __init__(self, db: AsyncSession = None):
        """Initialize webhook manager with optional database session"""
        self.db = db

    @staticmethod
    def generate_secret() -> str:
        """Generate a secure random secret for HMAC signing"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def compute_signature(payload: str, secret: str) -> str:
        """
        Compute HMAC-SHA256 signature for webhook payload

        Args:
            payload: JSON string of the webhook payload
            secret: Webhook secret key

        Returns:
            Hex digest of the HMAC signature
        """
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        )
        return signature.hexdigest()

    @staticmethod
    def verify_signature(payload: str, signature: str, secret: str) -> bool:
        """
        Verify HMAC signature for incoming webhook validation

        Args:
            payload: JSON string of the webhook payload
            signature: Provided signature to verify
            secret: Webhook secret key

        Returns:
            True if signature is valid, False otherwise
        """
        expected_signature = WebhookManager.compute_signature(payload, secret)
        return hmac.compare_digest(expected_signature, signature)

    async def register_webhook(
        self,
        user_id: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None
    ) -> Webhook:
        """
        Register a new webhook for a user

        Args:
            user_id: User ID who owns the webhook
            url: Webhook URL to POST notifications to
            events: List of event types to subscribe to
            secret: Optional custom secret (auto-generated if not provided)

        Returns:
            Created Webhook instance

        Raises:
            ValueError: If events contain unsupported event types
        """
        # Validate events
        invalid_events = set(events) - set(self.SUPPORTED_EVENTS)
        if invalid_events:
            raise ValueError(f"Unsupported events: {invalid_events}")

        # Generate secret if not provided
        if not secret:
            secret = self.generate_secret()

        # Create webhook
        webhook = Webhook(
            user_id=user_id,
            url=url,
            events=events,
            secret=secret,
            active=True
        )

        if self.db:
            self.db.add(webhook)
            await self.db.commit()
            await self.db.refresh(webhook)

        logger.info(f"📌 Registered webhook {webhook.id} for user {user_id}")
        return webhook

    async def get_user_webhooks(
        self,
        user_id: str,
        active_only: bool = True
    ) -> List[Webhook]:
        """
        Get all webhooks for a user

        Args:
            user_id: User ID
            active_only: If True, only return active webhooks

        Returns:
            List of Webhook instances
        """
        if not self.db:
            return []

        query = select(Webhook).where(Webhook.user_id == user_id)
        if active_only:
            query = query.where(Webhook.active == True)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """Get a specific webhook by ID"""
        if not self.db:
            return None

        result = await self.db.execute(
            select(Webhook).where(Webhook.id == webhook_id)
        )
        return result.scalar_one_or_none()

    async def delete_webhook(self, webhook_id: str, user_id: str) -> bool:
        """
        Delete a webhook (only if owned by user)

        Args:
            webhook_id: Webhook ID to delete
            user_id: User ID for ownership verification

        Returns:
            True if deleted, False if not found or not owned by user
        """
        if not self.db:
            return False

        webhook = await self.get_webhook(webhook_id)
        if not webhook or webhook.user_id != user_id:
            return False

        await self.db.delete(webhook)
        await self.db.commit()

        logger.info(f"🗑️ Deleted webhook {webhook_id}")
        return True

    async def update_webhook(
        self,
        webhook_id: str,
        user_id: str,
        url: Optional[str] = None,
        events: Optional[List[str]] = None,
        active: Optional[bool] = None
    ) -> Optional[Webhook]:
        """
        Update webhook configuration

        Args:
            webhook_id: Webhook ID to update
            user_id: User ID for ownership verification
            url: New URL (optional)
            events: New events list (optional)
            active: New active status (optional)

        Returns:
            Updated Webhook instance or None if not found/not owned
        """
        if not self.db:
            return None

        webhook = await self.get_webhook(webhook_id)
        if not webhook or webhook.user_id != user_id:
            return None

        if url is not None:
            webhook.url = url

        if events is not None:
            # Validate events
            invalid_events = set(events) - set(self.SUPPORTED_EVENTS)
            if invalid_events:
                raise ValueError(f"Unsupported events: {invalid_events}")
            webhook.events = events

        if active is not None:
            webhook.active = active

        await self.db.commit()
        await self.db.refresh(webhook)

        logger.info(f"✏️ Updated webhook {webhook_id}")
        return webhook

    async def send_webhook(
        self,
        webhook_id: str,
        event_type: str,
        payload: Dict[str, Any]
    ) -> bool:
        """
        Send webhook notification immediately

        Args:
            webhook_id: Webhook ID to send to
            event_type: Event type (e.g., 'task.completed')
            payload: Payload data to send

        Returns:
            True if delivery successful, False otherwise
        """
        if not self.db:
            return False

        webhook = await self.get_webhook(webhook_id)
        if not webhook or not webhook.active:
            logger.warning(f"⚠️ Webhook {webhook_id} not found or inactive")
            return False

        # Check if webhook is subscribed to this event
        if event_type not in webhook.events:
            logger.debug(f"Webhook {webhook_id} not subscribed to {event_type}")
            return False

        # Create delivery record
        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event_type=event_type,
            payload=payload,
            status="pending",
            attempts=0,
            max_attempts=self.MAX_RETRY_ATTEMPTS
        )

        self.db.add(delivery)
        await self.db.commit()
        await self.db.refresh(delivery)

        # Attempt delivery
        success = await self._deliver_webhook(webhook, delivery, payload)

        return success

    async def _deliver_webhook(
        self,
        webhook: Webhook,
        delivery: WebhookDelivery,
        payload: Dict[str, Any]
    ) -> bool:
        """
        Internal method to deliver webhook with retry logic

        Args:
            webhook: Webhook configuration
            delivery: WebhookDelivery record
            payload: Payload to send

        Returns:
            True if delivery successful, False otherwise
        """
        import json

        # Prepare payload with metadata
        full_payload = {
            "event": delivery.event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": payload
        }

        payload_json = json.dumps(full_payload, default=str)
        signature = self.compute_signature(payload_json, webhook.secret)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": delivery.event_type,
            "User-Agent": "SupoClip-Webhook/1.0"
        }

        try:
            async with httpx.AsyncClient(timeout=self.DELIVERY_TIMEOUT) as client:
                response = await client.post(
                    webhook.url,
                    content=payload_json,
                    headers=headers
                )

                delivery.attempts += 1
                delivery.response_code = response.status_code
                delivery.response_body = response.text[:1000]  # Limit response storage

                if 200 <= response.status_code < 300:
                    delivery.status = "success"
                    delivery.delivered_at = datetime.utcnow()
                    await self.db.commit()

                    logger.info(f"✅ Webhook delivered: {webhook.id} -> {delivery.event_type}")
                    return True
                else:
                    logger.warning(
                        f"⚠️ Webhook delivery failed: {webhook.id} -> "
                        f"{delivery.event_type} (HTTP {response.status_code})"
                    )

                    # Schedule retry if attempts remaining
                    if delivery.attempts < delivery.max_attempts:
                        delay_seconds = self.RETRY_DELAYS[delivery.attempts - 1]
                        delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
                        delivery.status = "pending"
                        logger.info(f"🔄 Retry scheduled in {delay_seconds}s for delivery {delivery.id}")
                    else:
                        delivery.status = "failed"
                        logger.error(f"❌ Webhook delivery failed permanently: {delivery.id}")

                    await self.db.commit()
                    return False

        except Exception as e:
            logger.error(f"❌ Webhook delivery error: {webhook.id} -> {str(e)}")

            delivery.attempts += 1
            delivery.response_body = str(e)[:1000]

            # Schedule retry if attempts remaining
            if delivery.attempts < delivery.max_attempts:
                delay_seconds = self.RETRY_DELAYS[delivery.attempts - 1]
                delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
                delivery.status = "pending"
            else:
                delivery.status = "failed"

            await self.db.commit()
            return False

    async def process_pending_deliveries(self):
        """
        Process all pending webhook deliveries that are ready for retry
        This should be called periodically by a background worker
        """
        if not self.db:
            return

        now = datetime.utcnow()

        # Find all pending deliveries ready for retry
        query = select(WebhookDelivery).where(
            and_(
                WebhookDelivery.status == "pending",
                WebhookDelivery.next_retry_at <= now
            )
        )

        result = await self.db.execute(query)
        pending_deliveries = result.scalars().all()

        logger.info(f"🔄 Processing {len(pending_deliveries)} pending webhook deliveries")

        for delivery in pending_deliveries:
            webhook = await self.get_webhook(delivery.webhook_id)
            if webhook and webhook.active:
                await self._deliver_webhook(webhook, delivery, delivery.payload)

    async def notify_task_event(
        self,
        user_id: str,
        task_id: str,
        event_type: str,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """
        Send webhook notifications for task events

        Args:
            user_id: User ID who owns the task
            task_id: Task ID
            event_type: Event type ('task.completed', 'task.failed', 'clips.ready')
            additional_data: Additional data to include in payload
        """
        if not self.db:
            return

        # Get all active webhooks for this user subscribed to this event
        webhooks = await self.get_user_webhooks(user_id, active_only=True)
        webhooks = [w for w in webhooks if event_type in w.events]

        if not webhooks:
            logger.debug(f"No webhooks registered for {user_id} / {event_type}")
            return

        # Build payload
        payload = {
            "task_id": task_id,
            "user_id": user_id,
        }

        if additional_data:
            payload.update(additional_data)

        # Get task details
        task_result = await self.db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = task_result.scalar_one_or_none()

        if task:
            payload["task_status"] = task.status

            # Include clip information if available
            if event_type == "clips.ready" and task.generated_clips_ids:
                clips_result = await self.db.execute(
                    select(GeneratedClip).where(
                        GeneratedClip.task_id == task_id
                    )
                )
                clips = clips_result.scalars().all()

                payload["clips"] = [
                    {
                        "id": clip.id,
                        "filename": clip.filename,
                        "start_time": clip.start_time,
                        "end_time": clip.end_time,
                        "duration": clip.duration,
                        "relevance_score": clip.relevance_score
                    }
                    for clip in clips
                ]

        # Send to all subscribed webhooks
        logger.info(f"📤 Sending {event_type} notifications to {len(webhooks)} webhooks")

        for webhook in webhooks:
            await self.send_webhook(webhook.id, event_type, payload)


# Global webhook manager instance
webhook_manager = None


def get_webhook_manager(db: AsyncSession = None) -> WebhookManager:
    """Get or create global webhook manager instance"""
    global webhook_manager
    if webhook_manager is None or db is not None:
        webhook_manager = WebhookManager(db)
    return webhook_manager
