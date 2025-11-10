"""
Calendar API routes for scheduling posts to calendar services.

Supports Google Calendar, iCloud Calendar, and generic CalDAV calendars.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import json

from ...database import get_db
from ...models import CalendarCredential, ScheduledPost, GeneratedClip, Task
from ...integrations.calendar import CalendarIntegration, CalendarProvider
from ...config import Config

logger = logging.getLogger(__name__)
config = Config()
router = APIRouter(prefix="/calendar", tags=["calendar"])


# Helper functions

async def get_user_credential(
    db: AsyncSession, user_id: str, provider: Optional[str] = None
) -> Optional[CalendarCredential]:
    """Get active calendar credential for user"""
    query = select(CalendarCredential).where(
        and_(
            CalendarCredential.user_id == user_id,
            CalendarCredential.is_active == True
        )
    )

    if provider:
        query = query.where(CalendarCredential.provider == provider)

    result = await db.execute(query)
    return result.scalar_one_or_none()


def build_credentials_dict(credential: CalendarCredential) -> Dict[str, Any]:
    """Build credentials dictionary from database model"""
    if credential.provider == "google":
        return {
            "access_token": credential.access_token,
            "refresh_token": credential.refresh_token,
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": config.google_client_id if hasattr(config, 'google_client_id') else None,
            "client_secret": config.google_client_secret if hasattr(config, 'google_client_secret') else None,
        }
    else:  # caldav or icloud
        return {
            "url": credential.caldav_url,
            "username": credential.caldav_username,
            "password": credential.caldav_password,
            "calendar_name": credential.calendar_name,
        }


# OAuth endpoints

@router.get("/oauth/google/url")
async def get_google_oauth_url(request: Request):
    """
    Get Google OAuth authorization URL.

    Returns the URL to redirect users to for Google Calendar authorization.
    """
    user_id = request.headers.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User authentication required")

    try:
        from ...integrations.google_calendar import GoogleCalendarIntegration

        # Get OAuth credentials from config
        client_id = config.google_client_id if hasattr(config, 'google_client_id') else None
        client_secret = config.google_client_secret if hasattr(config, 'google_client_secret') else None
        redirect_uri = config.google_redirect_uri if hasattr(config, 'google_redirect_uri') else "http://localhost:3000/auth/google/callback"

        if not client_id or not client_secret:
            raise HTTPException(
                status_code=500,
                detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in environment."
            )

        auth_url = GoogleCalendarIntegration.get_oauth_url(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            state=user_id,  # Use user_id as state for verification
        )

        return {"auth_url": auth_url}

    except Exception as e:
        logger.error(f"Failed to generate Google OAuth URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oauth/google/callback")
async def google_oauth_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Google OAuth callback and store credentials.

    Expected body:
    {
        "code": "authorization_code_from_google",
        "state": "user_id"
    }
    """
    try:
        data = await request.json()
        code = data.get("code")
        user_id = data.get("state")

        if not code or not user_id:
            raise HTTPException(status_code=400, detail="Missing code or state")

        from ...integrations.google_calendar import GoogleCalendarIntegration

        # Get OAuth credentials from config
        client_id = config.google_client_id if hasattr(config, 'google_client_id') else None
        client_secret = config.google_client_secret if hasattr(config, 'google_client_secret') else None
        redirect_uri = config.google_redirect_uri if hasattr(config, 'google_redirect_uri') else "http://localhost:3000/auth/google/callback"

        # Exchange code for tokens
        tokens = await GoogleCalendarIntegration.exchange_code_for_tokens(
            code=code,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
        )

        # Check if credential already exists
        existing = await get_user_credential(db, user_id, "google")

        if existing:
            # Update existing credential
            existing.access_token = tokens["access_token"]
            existing.refresh_token = tokens["refresh_token"]
            existing.is_active = True
            existing.updated_at = datetime.utcnow()
            credential = existing
        else:
            # Create new credential
            credential = CalendarCredential(
                user_id=user_id,
                provider="google",
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                is_active=True,
            )
            db.add(credential)

        await db.commit()
        await db.refresh(credential)

        logger.info(f"Saved Google Calendar credentials for user {user_id}")

        return {
            "success": True,
            "credential_id": credential.id,
            "provider": "google"
        }

    except Exception as e:
        logger.error(f"Failed to handle Google OAuth callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# CalDAV/iCloud credentials

@router.post("/credentials/caldav")
async def add_caldav_credentials(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Add CalDAV calendar credentials (iCloud, Nextcloud, etc.).

    Expected body:
    {
        "provider": "icloud" or "caldav",
        "url": "https://caldav.icloud.com" (optional for iCloud),
        "username": "apple_id@icloud.com",
        "password": "app-specific-password",
        "calendar_name": "Calendar" (optional)
    }
    """
    user_id = request.headers.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User authentication required")

    try:
        data = await request.json()

        provider = data.get("provider", "caldav")
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password required")

        # Set default URL for iCloud
        if provider == "icloud":
            url = "https://caldav.icloud.com"
        else:
            url = data.get("url")
            if not url:
                raise HTTPException(status_code=400, detail="CalDAV URL required")

        calendar_name = data.get("calendar_name")

        # Test credentials by attempting authentication
        from ...integrations.caldav_calendar import CalDAVCalendarIntegration

        test_integration = CalDAVCalendarIntegration(
            user_id=user_id,
            credentials={
                "url": url,
                "username": username,
                "password": password,
                "calendar_name": calendar_name,
            }
        )

        if not await test_integration.authenticate():
            raise HTTPException(status_code=401, detail="Invalid CalDAV credentials")

        # Check if credential already exists
        existing = await get_user_credential(db, user_id, provider)

        if existing:
            # Update existing credential
            existing.caldav_url = url
            existing.caldav_username = username
            existing.caldav_password = password  # TODO: Encrypt in production
            existing.calendar_name = calendar_name
            existing.is_active = True
            existing.updated_at = datetime.utcnow()
            credential = existing
        else:
            # Create new credential
            credential = CalendarCredential(
                user_id=user_id,
                provider=provider,
                caldav_url=url,
                caldav_username=username,
                caldav_password=password,  # TODO: Encrypt in production
                calendar_name=calendar_name,
                is_active=True,
            )
            db.add(credential)

        await db.commit()
        await db.refresh(credential)

        logger.info(f"Saved {provider} calendar credentials for user {user_id}")

        return {
            "success": True,
            "credential_id": credential.id,
            "provider": provider
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add CalDAV credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/credentials")
async def list_credentials(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """List all calendar credentials for the authenticated user."""
    user_id = request.headers.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User authentication required")

    try:
        result = await db.execute(
            select(CalendarCredential).where(
                CalendarCredential.user_id == user_id
            ).order_by(CalendarCredential.created_at.desc())
        )
        credentials = result.scalars().all()

        # Return safe credential info (without sensitive data)
        return {
            "credentials": [
                {
                    "id": cred.id,
                    "provider": cred.provider,
                    "is_active": cred.is_active,
                    "calendar_name": cred.calendar_name,
                    "created_at": cred.created_at.isoformat(),
                }
                for cred in credentials
            ]
        }

    except Exception as e:
        logger.error(f"Failed to list credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/credentials/{credential_id}")
async def delete_credential(
    credential_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Delete a calendar credential."""
    user_id = request.headers.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User authentication required")

    try:
        result = await db.execute(
            select(CalendarCredential).where(
                and_(
                    CalendarCredential.id == credential_id,
                    CalendarCredential.user_id == user_id
                )
            )
        )
        credential = result.scalar_one_or_none()

        if not credential:
            raise HTTPException(status_code=404, detail="Credential not found")

        await db.delete(credential)
        await db.commit()

        logger.info(f"Deleted calendar credential {credential_id} for user {user_id}")

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete credential: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Scheduling endpoints

@router.post("/schedule")
async def schedule_post(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Schedule a clip to be posted at a specific time.

    Expected body:
    {
        "clip_id": "clip_uuid",
        "scheduled_time": "2025-11-15T10:00:00Z",
        "provider": "google" (optional, uses active credential)
    }
    """
    user_id = request.headers.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User authentication required")

    try:
        data = await request.json()

        clip_id = data.get("clip_id")
        scheduled_time_str = data.get("scheduled_time")
        provider = data.get("provider")

        if not clip_id or not scheduled_time_str:
            raise HTTPException(status_code=400, detail="clip_id and scheduled_time required")

        # Parse scheduled time
        try:
            scheduled_time = datetime.fromisoformat(scheduled_time_str.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid scheduled_time format")

        # Get clip
        result = await db.execute(
            select(GeneratedClip).where(GeneratedClip.id == clip_id)
        )
        clip = result.scalar_one_or_none()

        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")

        # Verify user owns this clip
        result = await db.execute(
            select(Task).where(Task.id == clip.task_id)
        )
        task = result.scalar_one_or_none()

        if not task or task.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get calendar credential
        credential = await get_user_credential(db, user_id, provider)
        if not credential:
            raise HTTPException(
                status_code=400,
                detail=f"No active calendar credential found{' for ' + provider if provider else ''}"
            )

        # Build calendar integration
        creds_dict = build_credentials_dict(credential)
        calendar = CalendarIntegration.get_calendar_integration(
            provider=CalendarProvider(credential.provider),
            user_id=user_id,
            credentials=creds_dict,
        )

        # Authenticate
        if not await calendar.authenticate():
            raise HTTPException(status_code=401, detail="Failed to authenticate with calendar")

        # Prepare clip metadata
        clip_metadata = {
            "filename": clip.filename,
            "duration": clip.duration,
            "start_time": clip.start_time,
            "end_time": clip.end_time,
            "relevance_score": clip.relevance_score,
            "text": clip.text,
            "reasoning": clip.reasoning,
        }

        # Schedule the post
        scheduled_post_obj = await calendar.schedule_post(
            clip_id=clip_id,
            task_id=task.id,
            scheduled_time=scheduled_time,
            clip_metadata=clip_metadata,
        )

        # Save to database
        scheduled_post = ScheduledPost(
            user_id=user_id,
            clip_id=clip_id,
            task_id=task.id,
            calendar_credential_id=credential.id,
            calendar_event_id=scheduled_post_obj.calendar_event_id,
            calendar_provider=credential.provider,
            scheduled_time=scheduled_time,
            title=scheduled_post_obj.title,
            description=scheduled_post_obj.description,
            clip_metadata=clip_metadata,
            status="scheduled",
        )

        db.add(scheduled_post)
        await db.commit()
        await db.refresh(scheduled_post)

        logger.info(f"Scheduled post {scheduled_post.id} for clip {clip_id} at {scheduled_time}")

        return {
            "success": True,
            "scheduled_post_id": scheduled_post.id,
            "calendar_event_id": scheduled_post.calendar_event_id,
            "scheduled_time": scheduled_post.scheduled_time.isoformat(),
            "provider": scheduled_post.calendar_provider,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to schedule post: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
async def list_scheduled_posts(
    request: Request,
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[str] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (ISO format)"),
    limit: int = Query(50, description="Maximum number of results"),
):
    """
    List scheduled posts for the authenticated user.

    Optionally filter by status and date range.
    """
    user_id = request.headers.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User authentication required")

    try:
        query = select(ScheduledPost).where(
            ScheduledPost.user_id == user_id
        )

        if status:
            query = query.where(ScheduledPost.status == status)

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.where(ScheduledPost.scheduled_time >= start_dt)

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.where(ScheduledPost.scheduled_time <= end_dt)

        query = query.order_by(ScheduledPost.scheduled_time.asc()).limit(limit)

        result = await db.execute(query)
        posts = result.scalars().all()

        return {
            "scheduled_posts": [
                {
                    "id": post.id,
                    "clip_id": post.clip_id,
                    "task_id": post.task_id,
                    "scheduled_time": post.scheduled_time.isoformat(),
                    "title": post.title,
                    "status": post.status,
                    "calendar_provider": post.calendar_provider,
                    "calendar_event_id": post.calendar_event_id,
                    "clip_metadata": post.clip_metadata,
                    "created_at": post.created_at.isoformat(),
                }
                for post in posts
            ],
            "total": len(posts),
        }

    except Exception as e:
        logger.error(f"Failed to list scheduled posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/events/{scheduled_post_id}")
async def delete_scheduled_post(
    scheduled_post_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a scheduled post and remove it from the calendar.
    """
    user_id = request.headers.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User authentication required")

    try:
        # Get scheduled post
        result = await db.execute(
            select(ScheduledPost).where(
                and_(
                    ScheduledPost.id == scheduled_post_id,
                    ScheduledPost.user_id == user_id
                )
            )
        )
        post = result.scalar_one_or_none()

        if not post:
            raise HTTPException(status_code=404, detail="Scheduled post not found")

        # Get calendar credential
        result = await db.execute(
            select(CalendarCredential).where(
                CalendarCredential.id == post.calendar_credential_id
            )
        )
        credential = result.scalar_one_or_none()

        if credential:
            # Try to delete calendar event
            try:
                creds_dict = build_credentials_dict(credential)
                calendar = CalendarIntegration.get_calendar_integration(
                    provider=CalendarProvider(credential.provider),
                    user_id=user_id,
                    credentials=creds_dict,
                )

                if await calendar.authenticate():
                    await calendar.delete_event(post.calendar_event_id)
                    logger.info(f"Deleted calendar event {post.calendar_event_id}")
            except Exception as e:
                logger.warning(f"Failed to delete calendar event: {e}")
                # Continue with database deletion even if calendar deletion fails

        # Delete from database
        await db.delete(post)
        await db.commit()

        logger.info(f"Deleted scheduled post {scheduled_post_id}")

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete scheduled post: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/events/{scheduled_post_id}")
async def update_scheduled_post(
    scheduled_post_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a scheduled post (change time or status).

    Expected body:
    {
        "scheduled_time": "2025-11-16T15:00:00Z" (optional),
        "status": "cancelled" (optional)
    }
    """
    user_id = request.headers.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User authentication required")

    try:
        data = await request.json()

        # Get scheduled post
        result = await db.execute(
            select(ScheduledPost).where(
                and_(
                    ScheduledPost.id == scheduled_post_id,
                    ScheduledPost.user_id == user_id
                )
            )
        )
        post = result.scalar_one_or_none()

        if not post:
            raise HTTPException(status_code=404, detail="Scheduled post not found")

        # Update fields
        new_scheduled_time = data.get("scheduled_time")
        new_status = data.get("status")

        if new_scheduled_time:
            try:
                new_time = datetime.fromisoformat(new_scheduled_time.replace("Z", "+00:00"))

                # Update calendar event
                result = await db.execute(
                    select(CalendarCredential).where(
                        CalendarCredential.id == post.calendar_credential_id
                    )
                )
                credential = result.scalar_one_or_none()

                if credential:
                    creds_dict = build_credentials_dict(credential)
                    calendar = CalendarIntegration.get_calendar_integration(
                        provider=CalendarProvider(credential.provider),
                        user_id=user_id,
                        credentials=creds_dict,
                    )

                    if await calendar.authenticate():
                        await calendar.update_event(
                            event_id=post.calendar_event_id,
                            start_time=new_time,
                            end_time=new_time + timedelta(minutes=5),
                        )

                post.scheduled_time = new_time

            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid scheduled_time format")

        if new_status:
            if new_status not in ["scheduled", "published", "failed", "cancelled"]:
                raise HTTPException(status_code=400, detail="Invalid status")
            post.status = new_status

        post.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(post)

        logger.info(f"Updated scheduled post {scheduled_post_id}")

        return {
            "success": True,
            "scheduled_post": {
                "id": post.id,
                "scheduled_time": post.scheduled_time.isoformat(),
                "status": post.status,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update scheduled post: {e}")
        raise HTTPException(status_code=500, detail=str(e))
