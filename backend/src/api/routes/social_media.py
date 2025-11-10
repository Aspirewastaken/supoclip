"""
Social Media Integration API Routes

Endpoints for connecting social media accounts, posting clips,
and managing scheduled posts.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Query, Header, Depends
from pydantic import BaseModel, Field

from ...database import get_db_pool
from ...integrations.social_media import (
    Platform,
    PostStatus,
    SocialMediaManager,
    create_oauth_state,
    verify_oauth_state,
    init_integrations
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/social",
    tags=["Social Media"],
    responses={
        401: {"description": "Unauthorized - Missing or invalid user_id header"},
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"}
    }
)

# Global manager instance (initialized in lifespan)
_social_media_manager: Optional[SocialMediaManager] = None


async def get_social_media_manager() -> SocialMediaManager:
    """Get or initialize social media manager"""
    global _social_media_manager

    if _social_media_manager is None:
        db_pool = await get_db_pool()
        _social_media_manager = await init_integrations(db_pool)

    return _social_media_manager


def get_user_id(user_id: str = Header(..., description="User ID from authentication")) -> str:
    """Get user ID from header"""
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing user_id header")
    return user_id


# ============================================================================
# Request/Response Models
# ============================================================================

class ConnectPlatformResponse(BaseModel):
    """Response for platform connection request"""
    authorization_url: str = Field(..., description="OAuth authorization URL to redirect user to")
    state: str = Field(..., description="OAuth state parameter for security")


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request"""
    code: str = Field(..., description="Authorization code from OAuth provider")
    state: str = Field(..., description="OAuth state parameter")


class SocialMediaAccountResponse(BaseModel):
    """Social media account details"""
    id: str
    platform: Platform
    platform_username: Optional[str] = None
    is_active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime


class PostRequest(BaseModel):
    """Request to post a clip"""
    clip_id: str = Field(..., description="ID of the clip to post")
    platforms: List[Platform] = Field(..., description="Platforms to post to")
    caption: Optional[str] = Field(None, description="Post caption/description")
    hashtags: Optional[List[str]] = Field(default_factory=list, description="Hashtags (without # symbol)")
    scheduled_for: Optional[datetime] = Field(None, description="When to post (None = immediately)")
    platform_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Platform-specific configuration"
    )


class PostResponse(BaseModel):
    """Response from posting a clip"""
    post_id: str = Field(..., description="Scheduled post ID")
    status: PostStatus
    scheduled_for: datetime
    platforms: List[Platform]


class ScheduledPostResponse(BaseModel):
    """Scheduled post details"""
    id: str
    clip_id: str
    filename: str
    platforms: List[Platform]
    scheduled_for: datetime
    caption: Optional[str] = None
    hashtags: List[str]
    status: PostStatus
    created_at: datetime
    processed_at: Optional[datetime] = None


class PostAttemptResponse(BaseModel):
    """Post attempt details"""
    id: str
    platform: Platform
    attempt_number: int
    status: str
    platform_post_id: Optional[str] = None
    platform_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime


# ============================================================================
# OAuth Endpoints
# ============================================================================

@router.get(
    "/connect/{platform}",
    response_model=ConnectPlatformResponse,
    summary="Connect Social Media Platform",
    description="""
    Get OAuth authorization URL for connecting a social media platform.

    The user should be redirected to the returned `authorization_url`.
    After authorization, the platform will redirect back to your callback URL
    with a `code` parameter.

    Supported platforms:
    - `tiktok`: TikTok
    - `instagram`: Instagram (requires Facebook Business account)
    - `youtube`: YouTube Shorts
    - `twitter`: Twitter/X
    """
)
async def connect_platform(
    platform: Platform,
    user_id: str = Depends(get_user_id),
    manager: SocialMediaManager = Depends(get_social_media_manager)
):
    """Get OAuth authorization URL for platform"""
    try:
        # Check if integration is available
        integration = manager.integrations.get(platform)
        if not integration:
            raise HTTPException(
                status_code=400,
                detail=f"{platform.value} integration not configured. "
                       f"Please set up OAuth credentials in environment variables."
            )

        # Generate OAuth state
        state = create_oauth_state(user_id, platform)

        # Get authorization URL
        auth_url = integration.get_authorization_url(state)

        return ConnectPlatformResponse(
            authorization_url=auth_url,
            state=state
        )

    except Exception as e:
        logger.error(f"Error connecting {platform.value}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/callback/{platform}",
    response_model=SocialMediaAccountResponse,
    summary="OAuth Callback Handler",
    description="""
    Handle OAuth callback and save access tokens.

    This endpoint should be called after the user authorizes the app on the platform.
    The platform will redirect back with a `code` parameter.
    """
)
async def oauth_callback(
    platform: Platform,
    callback_data: OAuthCallbackRequest,
    user_id: str = Depends(get_user_id),
    manager: SocialMediaManager = Depends(get_social_media_manager)
):
    """Handle OAuth callback and save tokens"""
    try:
        # Get integration
        integration = manager.integrations.get(platform)
        if not integration:
            raise HTTPException(
                status_code=400,
                detail=f"{platform.value} integration not configured"
            )

        # Exchange code for token
        token_data = await integration.exchange_code_for_token(callback_data.code)

        # Get user info from platform (implementation depends on platform)
        # For now, we'll use placeholder values
        platform_user_id = f"{user_id}_{platform.value}"
        platform_username = None  # Would fetch from platform API

        # Save to database
        async with manager.db_pool.acquire() as conn:
            # Check if account already exists
            existing = await conn.fetchrow(
                """
                SELECT id FROM social_media_accounts
                WHERE user_id = $1 AND platform = $2 AND platform_user_id = $3
                """,
                user_id,
                platform.value,
                platform_user_id
            )

            if existing:
                # Update existing account
                await conn.execute(
                    """
                    UPDATE social_media_accounts
                    SET access_token = $1, refresh_token = $2, token_expires_at = $3,
                        is_active = true, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $4
                    """,
                    token_data["access_token"],
                    token_data.get("refresh_token"),
                    datetime.utcnow() if not token_data.get("expires_in") else None,
                    existing["id"]
                )
                account_id = existing["id"]
            else:
                # Create new account
                account_id = await conn.fetchval(
                    """
                    INSERT INTO social_media_accounts (
                        id, user_id, platform, platform_user_id, platform_username,
                        access_token, refresh_token, token_expires_at, metadata
                    ) VALUES (
                        uuid_generate_v4()::text, $1, $2, $3, $4, $5, $6, $7, $8
                    ) RETURNING id
                    """,
                    user_id,
                    platform.value,
                    platform_user_id,
                    platform_username,
                    token_data["access_token"],
                    token_data.get("refresh_token"),
                    datetime.utcnow() if not token_data.get("expires_in") else None,
                    json.dumps({})
                )

            # Get account details
            account = await conn.fetchrow(
                "SELECT * FROM social_media_accounts WHERE id = $1",
                account_id
            )

        return SocialMediaAccountResponse(**dict(account))

    except Exception as e:
        logger.error(f"Error handling OAuth callback for {platform.value}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/accounts",
    response_model=List[SocialMediaAccountResponse],
    summary="List Connected Accounts",
    description="Get all connected social media accounts for the authenticated user"
)
async def list_accounts(
    user_id: str = Depends(get_user_id),
    manager: SocialMediaManager = Depends(get_social_media_manager)
):
    """List all connected social media accounts"""
    try:
        async with manager.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, user_id, platform, platform_user_id, platform_username,
                       is_active, last_used_at, created_at, updated_at
                FROM social_media_accounts
                WHERE user_id = $1
                ORDER BY created_at DESC
                """,
                user_id
            )

        return [SocialMediaAccountResponse(**dict(row)) for row in rows]

    except Exception as e:
        logger.error(f"Error listing accounts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/accounts/{account_id}",
    summary="Disconnect Account",
    description="Disconnect and remove a social media account"
)
async def disconnect_account(
    account_id: str,
    user_id: str = Depends(get_user_id),
    manager: SocialMediaManager = Depends(get_social_media_manager)
):
    """Disconnect a social media account"""
    try:
        async with manager.db_pool.acquire() as conn:
            # Verify ownership
            account = await conn.fetchrow(
                "SELECT * FROM social_media_accounts WHERE id = $1",
                account_id
            )

            if not account:
                raise HTTPException(status_code=404, detail="Account not found")

            if account["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Not authorized")

            # Delete account
            await conn.execute(
                "DELETE FROM social_media_accounts WHERE id = $1",
                account_id
            )

        return {"message": f"Account disconnected successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting account: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Posting Endpoints
# ============================================================================

@router.post(
    "/post",
    response_model=PostResponse,
    summary="Post or Schedule Clip",
    description="""
    Post a clip to social media platforms immediately or schedule for later.

    If `scheduled_for` is provided, the post will be queued for publishing at that time.
    Otherwise, it will be posted immediately.

    The clip must be a generated clip from SupoClip (use clip ID from /tasks/{task_id}/clips).
    """
)
async def post_clip(
    post_data: PostRequest,
    user_id: str = Depends(get_user_id),
    manager: SocialMediaManager = Depends(get_social_media_manager)
):
    """Post or schedule a clip to social media platforms"""
    try:
        # Verify clip exists and belongs to user
        async with manager.db_pool.acquire() as conn:
            clip = await conn.fetchrow(
                """
                SELECT gc.*, t.user_id
                FROM generated_clips gc
                JOIN tasks t ON gc.task_id = t.id
                WHERE gc.id = $1
                """,
                post_data.clip_id
            )

            if not clip:
                raise HTTPException(status_code=404, detail="Clip not found")

            if clip["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Not authorized")

        # Determine if posting immediately or scheduling
        scheduled_for = post_data.scheduled_for or datetime.utcnow()
        is_immediate = post_data.scheduled_for is None

        if is_immediate:
            # Post immediately
            results = await manager.post_immediately(
                user_id=user_id,
                clip_id=post_data.clip_id,
                platforms=post_data.platforms,
                caption=post_data.caption,
                hashtags=post_data.hashtags,
                platform_config=post_data.platform_config
            )

            # Get the post ID (from database)
            async with manager.db_pool.acquire() as conn:
                post = await conn.fetchrow(
                    """
                    SELECT * FROM scheduled_posts
                    WHERE user_id = $1 AND clip_id = $2
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    user_id,
                    post_data.clip_id
                )

            return PostResponse(
                post_id=post["id"],
                status=PostStatus(post["status"]),
                scheduled_for=post["scheduled_for"],
                platforms=[Platform(p) for p in post["platforms"]]
            )
        else:
            # Schedule for later
            post_id = await manager.create_scheduled_post(
                user_id=user_id,
                clip_id=post_data.clip_id,
                platforms=post_data.platforms,
                scheduled_for=scheduled_for,
                caption=post_data.caption,
                hashtags=post_data.hashtags,
                platform_config=post_data.platform_config
            )

            return PostResponse(
                post_id=post_id,
                status=PostStatus.SCHEDULED,
                scheduled_for=scheduled_for,
                platforms=post_data.platforms
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error posting clip: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/scheduled",
    response_model=List[ScheduledPostResponse],
    summary="List Scheduled Posts",
    description="""
    Get all scheduled posts for the authenticated user.

    Optionally filter by status.
    """
)
async def list_scheduled_posts(
    user_id: str = Depends(get_user_id),
    status: Optional[PostStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of posts to return"),
    offset: int = Query(0, ge=0, description="Number of posts to skip"),
    manager: SocialMediaManager = Depends(get_social_media_manager)
):
    """List scheduled posts"""
    try:
        posts = await manager.get_scheduled_posts(
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset
        )

        return [
            ScheduledPostResponse(
                id=post["id"],
                clip_id=post["clip_id"],
                filename=post["filename"],
                platforms=[Platform(p) for p in post["platforms"]],
                scheduled_for=post["scheduled_for"],
                caption=post.get("caption"),
                hashtags=post.get("hashtags", []),
                status=PostStatus(post["status"]),
                created_at=post["created_at"],
                processed_at=post.get("processed_at")
            )
            for post in posts
        ]

    except Exception as e:
        logger.error(f"Error listing scheduled posts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/scheduled/{post_id}",
    response_model=ScheduledPostResponse,
    summary="Get Scheduled Post Details",
    description="Get details of a specific scheduled post"
)
async def get_scheduled_post(
    post_id: str,
    user_id: str = Depends(get_user_id),
    manager: SocialMediaManager = Depends(get_social_media_manager)
):
    """Get scheduled post details"""
    try:
        async with manager.db_pool.acquire() as conn:
            post = await conn.fetchrow(
                """
                SELECT sp.*, gc.filename
                FROM scheduled_posts sp
                JOIN generated_clips gc ON sp.clip_id = gc.id
                WHERE sp.id = $1
                """,
                post_id
            )

            if not post:
                raise HTTPException(status_code=404, detail="Scheduled post not found")

            if post["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Not authorized")

        return ScheduledPostResponse(
            id=post["id"],
            clip_id=post["clip_id"],
            filename=post["filename"],
            platforms=[Platform(p) for p in post["platforms"]],
            scheduled_for=post["scheduled_for"],
            caption=post.get("caption"),
            hashtags=post.get("hashtags", []),
            status=PostStatus(post["status"]),
            created_at=post["created_at"],
            processed_at=post.get("processed_at")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scheduled post: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/scheduled/{post_id}/attempts",
    response_model=List[PostAttemptResponse],
    summary="Get Post Attempts",
    description="Get all posting attempts for a scheduled post (useful for debugging failures)"
)
async def get_post_attempts(
    post_id: str,
    user_id: str = Depends(get_user_id),
    manager: SocialMediaManager = Depends(get_social_media_manager)
):
    """Get posting attempts for a scheduled post"""
    try:
        async with manager.db_pool.acquire() as conn:
            # Verify ownership
            post = await conn.fetchrow(
                "SELECT user_id FROM scheduled_posts WHERE id = $1",
                post_id
            )

            if not post:
                raise HTTPException(status_code=404, detail="Scheduled post not found")

            if post["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Not authorized")

            # Get attempts
            attempts = await conn.fetch(
                """
                SELECT id, scheduled_post_id, platform, social_media_account_id,
                       attempt_number, status, platform_post_id, platform_url,
                       error_message, error_code, created_at
                FROM post_attempts
                WHERE scheduled_post_id = $1
                ORDER BY created_at DESC
                """,
                post_id
            )

        return [
            PostAttemptResponse(**dict(attempt))
            for attempt in attempts
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting post attempts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/scheduled/{post_id}",
    summary="Cancel Scheduled Post",
    description="Cancel a scheduled post (only works for posts that haven't been processed yet)"
)
async def cancel_scheduled_post(
    post_id: str,
    user_id: str = Depends(get_user_id),
    manager: SocialMediaManager = Depends(get_social_media_manager)
):
    """Cancel a scheduled post"""
    try:
        async with manager.db_pool.acquire() as conn:
            # Verify ownership
            post = await conn.fetchrow(
                "SELECT * FROM scheduled_posts WHERE id = $1",
                post_id
            )

            if not post:
                raise HTTPException(status_code=404, detail="Scheduled post not found")

            if post["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Not authorized")

            if post["status"] != PostStatus.SCHEDULED.value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot cancel post with status: {post['status']}"
                )

        # Cancel the post
        await manager.cancel_scheduled_post(post_id)

        return {"message": "Scheduled post cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling scheduled post: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
