"""
Webhook API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from .manager import WebhookManager


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# Pydantic models for request/response
class WebhookCreate(BaseModel):
    """Request model for creating a webhook"""
    url: str = Field(..., description="Webhook URL to POST notifications to")
    events: List[str] = Field(
        ...,
        description="List of events to subscribe to",
        example=["task.completed", "clips.ready"]
    )
    secret: Optional[str] = Field(
        None,
        description="Custom secret for HMAC signing (auto-generated if not provided)"
    )


class WebhookUpdate(BaseModel):
    """Request model for updating a webhook"""
    url: Optional[str] = Field(None, description="New webhook URL")
    events: Optional[List[str]] = Field(None, description="New events list")
    active: Optional[bool] = Field(None, description="Enable/disable webhook")


class WebhookResponse(BaseModel):
    """Response model for webhook data"""
    id: str
    user_id: str
    url: str
    events: List[str]
    secret: str
    active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class WebhookListResponse(BaseModel):
    """Response model for list of webhooks"""
    webhooks: List[WebhookResponse]
    total: int


class WebhookDeleteResponse(BaseModel):
    """Response model for webhook deletion"""
    success: bool
    message: str


# Helper function to get user_id from headers
# In production, this would come from authentication middleware
def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    """Extract user_id from request headers"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing user authentication")
    return x_user_id


@router.post("", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    webhook_data: WebhookCreate,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new webhook

    Creates a webhook that will receive POST notifications for subscribed events.

    **Supported Events:**
    - `task.completed` - Sent when a video processing task completes successfully
    - `task.failed` - Sent when a video processing task fails
    - `clips.ready` - Sent when clips are generated and ready for download

    **Webhook Payload Format:**
    ```json
    {
        "event": "task.completed",
        "timestamp": "2025-11-10T12:00:00Z",
        "data": {
            "task_id": "...",
            "user_id": "...",
            "task_status": "completed",
            "clips": [...]
        }
    }
    ```

    **Security:**
    - Each webhook receives a unique secret for HMAC-SHA256 signing
    - Verify requests using the `X-Webhook-Signature` header
    - Store the secret securely - it's shown only once at creation

    **Example:**
    ```python
    import requests

    response = requests.post(
        "http://localhost:8000/webhooks",
        json={
            "url": "https://example.com/webhooks/supoclip",
            "events": ["task.completed", "clips.ready"]
        },
        headers={"X-User-Id": "user-123"}
    )
    ```
    """
    try:
        manager = WebhookManager(db)
        webhook = await manager.register_webhook(
            user_id=user_id,
            url=webhook_data.url,
            events=webhook_data.events,
            secret=webhook_data.secret
        )

        return WebhookResponse(
            id=webhook.id,
            user_id=webhook.user_id,
            url=webhook.url,
            events=webhook.events,
            secret=webhook.secret,
            active=webhook.active,
            created_at=webhook.created_at.isoformat(),
            updated_at=webhook.updated_at.isoformat()
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create webhook: {str(e)}")


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    active_only: bool = True,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    List all webhooks for the authenticated user

    **Query Parameters:**
    - `active_only` (default: true) - Only return active webhooks

    **Example:**
    ```bash
    curl -X GET "http://localhost:8000/webhooks?active_only=true" \\
         -H "X-User-Id: user-123"
    ```
    """
    try:
        manager = WebhookManager(db)
        webhooks = await manager.get_user_webhooks(user_id, active_only=active_only)

        webhook_responses = [
            WebhookResponse(
                id=w.id,
                user_id=w.user_id,
                url=w.url,
                events=w.events,
                secret=w.secret,
                active=w.active,
                created_at=w.created_at.isoformat(),
                updated_at=w.updated_at.isoformat()
            )
            for w in webhooks
        ]

        return WebhookListResponse(
            webhooks=webhook_responses,
            total=len(webhook_responses)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list webhooks: {str(e)}")


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: str,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific webhook by ID

    **Example:**
    ```bash
    curl -X GET "http://localhost:8000/webhooks/webhook-123" \\
         -H "X-User-Id: user-123"
    ```
    """
    try:
        manager = WebhookManager(db)
        webhook = await manager.get_webhook(webhook_id)

        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")

        if webhook.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this webhook")

        return WebhookResponse(
            id=webhook.id,
            user_id=webhook.user_id,
            url=webhook.url,
            events=webhook.events,
            secret=webhook.secret,
            active=webhook.active,
            created_at=webhook.created_at.isoformat(),
            updated_at=webhook.updated_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get webhook: {str(e)}")


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: str,
    webhook_data: WebhookUpdate,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a webhook configuration

    You can update the URL, events, or active status.

    **Example - Disable a webhook:**
    ```python
    import requests

    response = requests.patch(
        "http://localhost:8000/webhooks/webhook-123",
        json={"active": false},
        headers={"X-User-Id": "user-123"}
    )
    ```

    **Example - Update events:**
    ```python
    response = requests.patch(
        "http://localhost:8000/webhooks/webhook-123",
        json={"events": ["task.completed"]},
        headers={"X-User-Id": "user-123"}
    )
    ```
    """
    try:
        manager = WebhookManager(db)
        webhook = await manager.update_webhook(
            webhook_id=webhook_id,
            user_id=user_id,
            url=webhook_data.url,
            events=webhook_data.events,
            active=webhook_data.active
        )

        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found or not authorized")

        return WebhookResponse(
            id=webhook.id,
            user_id=webhook.user_id,
            url=webhook.url,
            events=webhook.events,
            secret=webhook.secret,
            active=webhook.active,
            created_at=webhook.created_at.isoformat(),
            updated_at=webhook.updated_at.isoformat()
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update webhook: {str(e)}")


@router.delete("/{webhook_id}", response_model=WebhookDeleteResponse)
async def delete_webhook(
    webhook_id: str,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a webhook

    **Example:**
    ```bash
    curl -X DELETE "http://localhost:8000/webhooks/webhook-123" \\
         -H "X-User-Id: user-123"
    ```
    """
    try:
        manager = WebhookManager(db)
        success = await manager.delete_webhook(webhook_id, user_id)

        if not success:
            raise HTTPException(status_code=404, detail="Webhook not found or not authorized")

        return WebhookDeleteResponse(
            success=True,
            message=f"Webhook {webhook_id} deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete webhook: {str(e)}")


@router.get("/events/supported")
async def get_supported_events():
    """
    Get list of supported webhook events

    **Example:**
    ```bash
    curl -X GET "http://localhost:8000/webhooks/events/supported"
    ```
    """
    return {
        "events": WebhookManager.SUPPORTED_EVENTS,
        "descriptions": {
            "task.completed": "Triggered when a video processing task completes successfully",
            "task.failed": "Triggered when a video processing task fails",
            "clips.ready": "Triggered when clips are generated and ready for download"
        }
    }
