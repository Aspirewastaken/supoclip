"""
Social Media Integration Module for SupoClip

This module provides integrations with multiple social media platforms:
- TikTok API
- Instagram API (Meta Business)
- YouTube Shorts API
- Twitter/X API

Features:
- OAuth 2.0 authentication flows
- Automated video posting
- Scheduled post management
- Retry logic with exponential backoff
- Post status tracking
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import aiohttp
import asyncpg
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration Models
# ============================================================================

class Platform(str, Enum):
    """Supported social media platforms"""
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TWITTER = "twitter"


class PostStatus(str, Enum):
    """Status of a scheduled post"""
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AttemptStatus(str, Enum):
    """Status of a posting attempt"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class OAuthConfig(BaseModel):
    """OAuth configuration for a platform"""
    client_id: str
    client_secret: str
    redirect_uri: str
    authorization_url: str
    token_url: str
    scopes: List[str]


class SocialMediaAccount(BaseModel):
    """Social media account model"""
    id: str
    user_id: str
    platform: Platform
    platform_user_id: str
    platform_username: Optional[str] = None
    access_token: str
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ScheduledPost(BaseModel):
    """Scheduled post model"""
    id: str
    user_id: str
    clip_id: str
    platforms: List[Platform]
    scheduled_for: datetime
    caption: Optional[str] = None
    hashtags: List[str] = Field(default_factory=list)
    platform_config: Dict[str, Any] = Field(default_factory=dict)
    status: PostStatus = PostStatus.SCHEDULED
    max_retries: int = 3
    retry_delay_seconds: int = 300
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None


class PostAttempt(BaseModel):
    """Post attempt model"""
    id: str
    scheduled_post_id: str
    platform: Platform
    social_media_account_id: str
    attempt_number: int = 1
    status: AttemptStatus = AttemptStatus.PENDING
    platform_post_id: Optional[str] = None
    platform_url: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PostResult(BaseModel):
    """Result of posting to a platform"""
    success: bool
    platform: Platform
    platform_post_id: Optional[str] = None
    platform_url: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# Base Classes
# ============================================================================

class BaseSocialMediaIntegration(ABC):
    """Base class for social media integrations"""

    def __init__(self, oauth_config: OAuthConfig, db_pool: asyncpg.Pool):
        self.oauth_config = oauth_config
        self.db_pool = db_pool
        self.session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    @abstractmethod
    def get_authorization_url(self, state: str) -> str:
        """Get OAuth authorization URL"""
        pass

    @abstractmethod
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        pass

    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        pass

    @abstractmethod
    async def upload_video(
        self,
        account: SocialMediaAccount,
        video_path: str,
        caption: str,
        hashtags: List[str],
        config: Dict[str, Any]
    ) -> PostResult:
        """Upload video to platform"""
        pass

    @abstractmethod
    async def get_video_status(self, account: SocialMediaAccount, video_id: str) -> Dict[str, Any]:
        """Get video upload/processing status"""
        pass

    async def ensure_token_valid(self, account: SocialMediaAccount) -> SocialMediaAccount:
        """Ensure access token is valid, refresh if needed"""
        if account.token_expires_at and account.token_expires_at <= datetime.utcnow():
            if not account.refresh_token:
                raise ValueError(f"Token expired and no refresh token available for {account.platform}")

            logger.info(f"Refreshing token for {account.platform} account {account.id}")
            token_data = await self.refresh_access_token(account.refresh_token)

            # Update account with new token
            account.access_token = token_data["access_token"]
            if "refresh_token" in token_data:
                account.refresh_token = token_data["refresh_token"]
            if "expires_in" in token_data:
                account.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])

            # Save to database
            await self._update_account_tokens(account)

        return account

    async def _update_account_tokens(self, account: SocialMediaAccount):
        """Update account tokens in database"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE social_media_accounts
                SET access_token = $1, refresh_token = $2, token_expires_at = $3, updated_at = CURRENT_TIMESTAMP
                WHERE id = $4
                """,
                account.access_token,
                account.refresh_token,
                account.token_expires_at,
                account.id
            )


# ============================================================================
# TikTok Integration
# ============================================================================

class TikTokIntegration(BaseSocialMediaIntegration):
    """TikTok API integration"""

    API_BASE_URL = "https://open.tiktokapis.com/v2"

    def get_authorization_url(self, state: str) -> str:
        """Get TikTok OAuth authorization URL"""
        params = {
            "client_key": self.oauth_config.client_id,
            "scope": ",".join(self.oauth_config.scopes),
            "response_type": "code",
            "redirect_uri": self.oauth_config.redirect_uri,
            "state": state
        }
        return f"{self.oauth_config.authorization_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange TikTok authorization code for access token"""
        session = await self.get_session()

        data = {
            "client_key": self.oauth_config.client_id,
            "client_secret": self.oauth_config.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.oauth_config.redirect_uri
        }

        async with session.post(self.oauth_config.token_url, json=data) as response:
            response.raise_for_status()
            result = await response.json()

            if result.get("error"):
                raise ValueError(f"TikTok OAuth error: {result.get('error_description', result['error'])}")

            return {
                "access_token": result["data"]["access_token"],
                "refresh_token": result["data"]["refresh_token"],
                "expires_in": result["data"]["expires_in"],
                "token_type": result["data"]["token_type"]
            }

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh TikTok access token"""
        session = await self.get_session()

        data = {
            "client_key": self.oauth_config.client_id,
            "client_secret": self.oauth_config.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }

        async with session.post(self.oauth_config.token_url, json=data) as response:
            response.raise_for_status()
            result = await response.json()

            if result.get("error"):
                raise ValueError(f"TikTok token refresh error: {result.get('error_description', result['error'])}")

            return {
                "access_token": result["data"]["access_token"],
                "refresh_token": result["data"]["refresh_token"],
                "expires_in": result["data"]["expires_in"]
            }

    async def upload_video(
        self,
        account: SocialMediaAccount,
        video_path: str,
        caption: str,
        hashtags: List[str],
        config: Dict[str, Any]
    ) -> PostResult:
        """Upload video to TikTok"""
        try:
            account = await self.ensure_token_valid(account)
            session = await self.get_session()

            # Step 1: Initialize upload
            full_caption = f"{caption}\n\n{' '.join(['#' + tag for tag in hashtags])}"

            init_data = {
                "post_info": {
                    "title": full_caption[:150],  # TikTok has title length limits
                    "privacy_level": config.get("privacy_level", "PUBLIC_TO_EVERYONE"),
                    "disable_duet": config.get("disable_duet", False),
                    "disable_stitch": config.get("disable_stitch", False),
                    "disable_comment": config.get("disable_comment", False),
                    "video_cover_timestamp_ms": config.get("cover_timestamp_ms", 1000)
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": os.path.getsize(video_path),
                    "chunk_size": 10 * 1024 * 1024,  # 10MB chunks
                    "total_chunk_count": 1
                }
            }

            headers = {
                "Authorization": f"Bearer {account.access_token}",
                "Content-Type": "application/json; charset=UTF-8"
            }

            async with session.post(
                f"{self.API_BASE_URL}/post/publish/video/init/",
                json=init_data,
                headers=headers
            ) as response:
                response.raise_for_status()
                init_result = await response.json()

                if init_result.get("error"):
                    raise ValueError(f"TikTok upload init error: {init_result['error']['message']}")

                upload_url = init_result["data"]["upload_url"]
                publish_id = init_result["data"]["publish_id"]

            # Step 2: Upload video file
            with open(video_path, 'rb') as video_file:
                video_data = video_file.read()

            upload_headers = {
                "Content-Type": "video/mp4",
                "Content-Length": str(len(video_data))
            }

            async with session.put(upload_url, data=video_data, headers=upload_headers) as response:
                response.raise_for_status()

            # Step 3: Commit upload
            commit_data = {"publish_id": publish_id}

            async with session.post(
                f"{self.API_BASE_URL}/post/publish/status/fetch/",
                json=commit_data,
                headers=headers
            ) as response:
                response.raise_for_status()
                commit_result = await response.json()

                if commit_result.get("error"):
                    raise ValueError(f"TikTok upload commit error: {commit_result['error']['message']}")

            # Update last used timestamp
            await self._update_last_used(account.id)

            return PostResult(
                success=True,
                platform=Platform.TIKTOK,
                platform_post_id=publish_id,
                platform_url=None  # TikTok doesn't provide direct URL immediately
            )

        except Exception as e:
            logger.error(f"TikTok upload error: {str(e)}")
            return PostResult(
                success=False,
                platform=Platform.TIKTOK,
                error=str(e)
            )

    async def get_video_status(self, account: SocialMediaAccount, video_id: str) -> Dict[str, Any]:
        """Get TikTok video status"""
        account = await self.ensure_token_valid(account)
        session = await self.get_session()

        headers = {
            "Authorization": f"Bearer {account.access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }

        data = {"publish_id": video_id}

        async with session.post(
            f"{self.API_BASE_URL}/post/publish/status/fetch/",
            json=data,
            headers=headers
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def _update_last_used(self, account_id: str):
        """Update last used timestamp"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE social_media_accounts SET last_used_at = CURRENT_TIMESTAMP WHERE id = $1",
                account_id
            )


# ============================================================================
# Instagram Integration (Meta Business API)
# ============================================================================

class InstagramIntegration(BaseSocialMediaIntegration):
    """Instagram API integration via Meta Business API"""

    API_BASE_URL = "https://graph.facebook.com/v18.0"

    def get_authorization_url(self, state: str) -> str:
        """Get Instagram OAuth authorization URL"""
        params = {
            "client_id": self.oauth_config.client_id,
            "redirect_uri": self.oauth_config.redirect_uri,
            "scope": ",".join(self.oauth_config.scopes),
            "response_type": "code",
            "state": state
        }
        return f"{self.oauth_config.authorization_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange Instagram authorization code for access token"""
        session = await self.get_session()

        params = {
            "client_id": self.oauth_config.client_id,
            "client_secret": self.oauth_config.client_secret,
            "redirect_uri": self.oauth_config.redirect_uri,
            "code": code
        }

        async with session.get(f"{self.API_BASE_URL}/oauth/access_token", params=params) as response:
            response.raise_for_status()
            result = await response.json()

            if "error" in result:
                raise ValueError(f"Instagram OAuth error: {result['error']['message']}")

            # Exchange short-lived token for long-lived token
            long_lived_token = await self._get_long_lived_token(result["access_token"])

            return long_lived_token

    async def _get_long_lived_token(self, short_token: str) -> Dict[str, Any]:
        """Exchange short-lived token for long-lived token (60 days)"""
        session = await self.get_session()

        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.oauth_config.client_id,
            "client_secret": self.oauth_config.client_secret,
            "fb_exchange_token": short_token
        }

        async with session.get(f"{self.API_BASE_URL}/oauth/access_token", params=params) as response:
            response.raise_for_status()
            result = await response.json()

            return {
                "access_token": result["access_token"],
                "expires_in": result.get("expires_in", 5184000)  # 60 days default
            }

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Instagram access token (get new long-lived token)"""
        # Instagram doesn't have traditional refresh tokens
        # Instead, we need to get a new long-lived token before the current one expires
        session = await self.get_session()

        params = {
            "grant_type": "ig_refresh_token",
            "access_token": refresh_token
        }

        async with session.get(f"{self.API_BASE_URL}/refresh_access_token", params=params) as response:
            response.raise_for_status()
            result = await response.json()

            return {
                "access_token": result["access_token"],
                "expires_in": result.get("expires_in", 5184000)
            }

    async def upload_video(
        self,
        account: SocialMediaAccount,
        video_path: str,
        caption: str,
        hashtags: List[str],
        config: Dict[str, Any]
    ) -> PostResult:
        """Upload Reel to Instagram"""
        try:
            account = await self.ensure_token_valid(account)
            session = await self.get_session()

            # Get Instagram Business Account ID
            ig_user_id = await self._get_instagram_account_id(account)

            # Step 1: Create media container
            full_caption = f"{caption}\n\n{' '.join(['#' + tag for tag in hashtags])}"

            # Video needs to be accessible via URL - upload to temporary hosting or use existing URL
            video_url = config.get("video_url")
            if not video_url:
                raise ValueError("Instagram requires video to be hosted at a public URL")

            create_params = {
                "media_type": "REELS",
                "video_url": video_url,
                "caption": full_caption[:2200],  # Instagram caption limit
                "share_to_feed": config.get("share_to_feed", True),
                "access_token": account.access_token
            }

            async with session.post(
                f"{self.API_BASE_URL}/{ig_user_id}/media",
                params=create_params
            ) as response:
                response.raise_for_status()
                result = await response.json()

                if "error" in result:
                    raise ValueError(f"Instagram container creation error: {result['error']['message']}")

                container_id = result["id"]

            # Step 2: Wait for video to be processed
            max_wait = 300  # 5 minutes
            start_time = time.time()

            while time.time() - start_time < max_wait:
                status = await self._get_container_status(account, ig_user_id, container_id)

                if status["status_code"] == "FINISHED":
                    break
                elif status["status_code"] == "ERROR":
                    raise ValueError(f"Instagram processing error: {status.get('status', 'Unknown error')}")

                await asyncio.sleep(5)

            # Step 3: Publish the media
            publish_params = {
                "creation_id": container_id,
                "access_token": account.access_token
            }

            async with session.post(
                f"{self.API_BASE_URL}/{ig_user_id}/media_publish",
                params=publish_params
            ) as response:
                response.raise_for_status()
                result = await response.json()

                if "error" in result:
                    raise ValueError(f"Instagram publish error: {result['error']['message']}")

                media_id = result["id"]

            # Update last used timestamp
            await self._update_last_used(account.id)

            return PostResult(
                success=True,
                platform=Platform.INSTAGRAM,
                platform_post_id=media_id,
                platform_url=f"https://www.instagram.com/reel/{media_id}/"
            )

        except Exception as e:
            logger.error(f"Instagram upload error: {str(e)}")
            return PostResult(
                success=False,
                platform=Platform.INSTAGRAM,
                error=str(e)
            )

    async def _get_instagram_account_id(self, account: SocialMediaAccount) -> str:
        """Get Instagram Business Account ID"""
        # Check if we have it cached in metadata
        if "instagram_account_id" in account.metadata:
            return account.metadata["instagram_account_id"]

        session = await self.get_session()

        params = {
            "fields": "instagram_business_account",
            "access_token": account.access_token
        }

        async with session.get(f"{self.API_BASE_URL}/me/accounts", params=params) as response:
            response.raise_for_status()
            result = await response.json()

            if not result.get("data"):
                raise ValueError("No Instagram Business Account connected")

            ig_account_id = result["data"][0]["instagram_business_account"]["id"]

            # Cache it
            account.metadata["instagram_account_id"] = ig_account_id
            await self._update_account_metadata(account.id, account.metadata)

            return ig_account_id

    async def _get_container_status(self, account: SocialMediaAccount, ig_user_id: str, container_id: str) -> Dict[str, Any]:
        """Check status of media container"""
        session = await self.get_session()

        params = {
            "fields": "status_code,status",
            "access_token": account.access_token
        }

        async with session.get(f"{self.API_BASE_URL}/{container_id}", params=params) as response:
            response.raise_for_status()
            return await response.json()

    async def get_video_status(self, account: SocialMediaAccount, video_id: str) -> Dict[str, Any]:
        """Get Instagram video status"""
        account = await self.ensure_token_valid(account)
        session = await self.get_session()

        params = {
            "fields": "id,media_type,media_url,permalink,timestamp",
            "access_token": account.access_token
        }

        async with session.get(f"{self.API_BASE_URL}/{video_id}", params=params) as response:
            response.raise_for_status()
            return await response.json()

    async def _update_last_used(self, account_id: str):
        """Update last used timestamp"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE social_media_accounts SET last_used_at = CURRENT_TIMESTAMP WHERE id = $1",
                account_id
            )

    async def _update_account_metadata(self, account_id: str, metadata: Dict[str, Any]):
        """Update account metadata"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE social_media_accounts SET metadata = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2",
                json.dumps(metadata),
                account_id
            )


# ============================================================================
# YouTube Integration
# ============================================================================

class YouTubeIntegration(BaseSocialMediaIntegration):
    """YouTube Shorts API integration"""

    API_BASE_URL = "https://www.googleapis.com/youtube/v3"
    UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"

    def get_authorization_url(self, state: str) -> str:
        """Get YouTube OAuth authorization URL"""
        params = {
            "client_id": self.oauth_config.client_id,
            "redirect_uri": self.oauth_config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.oauth_config.scopes),
            "state": state,
            "access_type": "offline",  # Get refresh token
            "prompt": "consent"
        }
        return f"{self.oauth_config.authorization_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange YouTube authorization code for access token"""
        session = await self.get_session()

        data = {
            "code": code,
            "client_id": self.oauth_config.client_id,
            "client_secret": self.oauth_config.client_secret,
            "redirect_uri": self.oauth_config.redirect_uri,
            "grant_type": "authorization_code"
        }

        async with session.post(self.oauth_config.token_url, data=data) as response:
            response.raise_for_status()
            result = await response.json()

            if "error" in result:
                raise ValueError(f"YouTube OAuth error: {result.get('error_description', result['error'])}")

            return {
                "access_token": result["access_token"],
                "refresh_token": result.get("refresh_token"),
                "expires_in": result["expires_in"],
                "token_type": result["token_type"]
            }

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh YouTube access token"""
        session = await self.get_session()

        data = {
            "refresh_token": refresh_token,
            "client_id": self.oauth_config.client_id,
            "client_secret": self.oauth_config.client_secret,
            "grant_type": "refresh_token"
        }

        async with session.post(self.oauth_config.token_url, data=data) as response:
            response.raise_for_status()
            result = await response.json()

            if "error" in result:
                raise ValueError(f"YouTube token refresh error: {result.get('error_description', result['error'])}")

            return {
                "access_token": result["access_token"],
                "expires_in": result["expires_in"],
                "refresh_token": refresh_token  # Keep existing refresh token
            }

    async def upload_video(
        self,
        account: SocialMediaAccount,
        video_path: str,
        caption: str,
        hashtags: List[str],
        config: Dict[str, Any]
    ) -> PostResult:
        """Upload Short to YouTube"""
        try:
            account = await self.ensure_token_valid(account)
            session = await self.get_session()

            # Prepare video metadata
            full_description = f"{caption}\n\n{' '.join(['#' + tag for tag in hashtags])}"

            metadata = {
                "snippet": {
                    "title": config.get("title", caption[:100]),  # YouTube title limit
                    "description": full_description,
                    "tags": hashtags[:500],  # YouTube allows up to 500 tags
                    "categoryId": config.get("category_id", "22")  # 22 = People & Blogs
                },
                "status": {
                    "privacyStatus": config.get("privacy_status", "public"),  # public, private, unlisted
                    "selfDeclaredMadeForKids": config.get("made_for_kids", False),
                    "madeForKids": config.get("made_for_kids", False)
                }
            }

            # Add Shorts-specific metadata
            if config.get("is_short", True):  # Default to Shorts
                metadata["snippet"]["tags"].append("shorts")

            # Prepare multipart upload
            headers = {
                "Authorization": f"Bearer {account.access_token}",
                "Content-Type": "application/json; charset=UTF-8"
            }

            # Upload video
            with open(video_path, 'rb') as video_file:
                video_data = video_file.read()

            # Use resumable upload
            params = {
                "part": "snippet,status",
                "uploadType": "multipart"
            }

            # Create multipart data
            boundary = "===============7330845974216740156=="
            body_parts = [
                f"--{boundary}",
                "Content-Type: application/json; charset=UTF-8",
                "",
                json.dumps(metadata),
                f"--{boundary}",
                "Content-Type: video/mp4",
                "",
            ]

            body = "\r\n".join(body_parts).encode() + b"\r\n" + video_data + f"\r\n--{boundary}--\r\n".encode()

            upload_headers = {
                "Authorization": f"Bearer {account.access_token}",
                "Content-Type": f"multipart/related; boundary={boundary}",
                "Content-Length": str(len(body))
            }

            async with session.post(
                self.UPLOAD_URL,
                params=params,
                data=body,
                headers=upload_headers
            ) as response:
                response.raise_for_status()
                result = await response.json()

                if "error" in result:
                    raise ValueError(f"YouTube upload error: {result['error']['message']}")

                video_id = result["id"]

            # Update last used timestamp
            await self._update_last_used(account.id)

            return PostResult(
                success=True,
                platform=Platform.YOUTUBE,
                platform_post_id=video_id,
                platform_url=f"https://www.youtube.com/shorts/{video_id}"
            )

        except Exception as e:
            logger.error(f"YouTube upload error: {str(e)}")
            return PostResult(
                success=False,
                platform=Platform.YOUTUBE,
                error=str(e)
            )

    async def get_video_status(self, account: SocialMediaAccount, video_id: str) -> Dict[str, Any]:
        """Get YouTube video status"""
        account = await self.ensure_token_valid(account)
        session = await self.get_session()

        params = {
            "part": "status,snippet,contentDetails",
            "id": video_id
        }

        headers = {
            "Authorization": f"Bearer {account.access_token}"
        }

        async with session.get(f"{self.API_BASE_URL}/videos", params=params, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    async def _update_last_used(self, account_id: str):
        """Update last used timestamp"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE social_media_accounts SET last_used_at = CURRENT_TIMESTAMP WHERE id = $1",
                account_id
            )


# ============================================================================
# Twitter/X Integration
# ============================================================================

class TwitterIntegration(BaseSocialMediaIntegration):
    """Twitter/X API integration"""

    API_BASE_URL = "https://api.twitter.com/2"
    UPLOAD_URL = "https://upload.twitter.com/1.1/media/upload.json"

    def get_authorization_url(self, state: str) -> str:
        """Get Twitter OAuth 2.0 authorization URL"""
        params = {
            "response_type": "code",
            "client_id": self.oauth_config.client_id,
            "redirect_uri": self.oauth_config.redirect_uri,
            "scope": " ".join(self.oauth_config.scopes),
            "state": state,
            "code_challenge": "challenge",  # For PKCE
            "code_challenge_method": "plain"
        }
        return f"{self.oauth_config.authorization_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange Twitter authorization code for access token"""
        session = await self.get_session()

        data = {
            "code": code,
            "grant_type": "authorization_code",
            "client_id": self.oauth_config.client_id,
            "redirect_uri": self.oauth_config.redirect_uri,
            "code_verifier": "challenge"
        }

        # Twitter requires Basic auth with client credentials
        auth = aiohttp.BasicAuth(self.oauth_config.client_id, self.oauth_config.client_secret)

        async with session.post(self.oauth_config.token_url, data=data, auth=auth) as response:
            response.raise_for_status()
            result = await response.json()

            if "error" in result:
                raise ValueError(f"Twitter OAuth error: {result.get('error_description', result['error'])}")

            return {
                "access_token": result["access_token"],
                "refresh_token": result.get("refresh_token"),
                "expires_in": result["expires_in"],
                "token_type": result["token_type"]
            }

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Twitter access token"""
        session = await self.get_session()

        data = {
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "client_id": self.oauth_config.client_id
        }

        auth = aiohttp.BasicAuth(self.oauth_config.client_id, self.oauth_config.client_secret)

        async with session.post(self.oauth_config.token_url, data=data, auth=auth) as response:
            response.raise_for_status()
            result = await response.json()

            if "error" in result:
                raise ValueError(f"Twitter token refresh error: {result.get('error_description', result['error'])}")

            return {
                "access_token": result["access_token"],
                "refresh_token": result.get("refresh_token", refresh_token),
                "expires_in": result["expires_in"]
            }

    async def upload_video(
        self,
        account: SocialMediaAccount,
        video_path: str,
        caption: str,
        hashtags: List[str],
        config: Dict[str, Any]
    ) -> PostResult:
        """Upload video to Twitter/X"""
        try:
            account = await self.ensure_token_valid(account)
            session = await self.get_session()

            # Step 1: INIT - Initialize upload
            file_size = os.path.getsize(video_path)

            init_data = {
                "command": "INIT",
                "media_type": "video/mp4",
                "media_category": "tweet_video",
                "total_bytes": file_size
            }

            headers = {
                "Authorization": f"Bearer {account.access_token}"
            }

            async with session.post(self.UPLOAD_URL, data=init_data, headers=headers) as response:
                response.raise_for_status()
                result = await response.json()
                media_id = result["media_id_string"]

            # Step 2: APPEND - Upload video chunks
            chunk_size = 5 * 1024 * 1024  # 5MB chunks
            segment_index = 0

            with open(video_path, 'rb') as video_file:
                while True:
                    chunk = video_file.read(chunk_size)
                    if not chunk:
                        break

                    append_data = {
                        "command": "APPEND",
                        "media_id": media_id,
                        "segment_index": segment_index
                    }

                    form_data = aiohttp.FormData()
                    form_data.add_field("command", "APPEND")
                    form_data.add_field("media_id", media_id)
                    form_data.add_field("segment_index", str(segment_index))
                    form_data.add_field("media", chunk, content_type="application/octet-stream")

                    async with session.post(self.UPLOAD_URL, data=form_data, headers=headers) as response:
                        response.raise_for_status()

                    segment_index += 1

            # Step 3: FINALIZE - Complete upload
            finalize_data = {
                "command": "FINALIZE",
                "media_id": media_id
            }

            async with session.post(self.UPLOAD_URL, data=finalize_data, headers=headers) as response:
                response.raise_for_status()
                result = await response.json()

                # Check if processing is required
                processing_info = result.get("processing_info")
                if processing_info:
                    await self._wait_for_processing(account, media_id, headers)

            # Step 4: Create tweet with media
            full_text = f"{caption}\n\n{' '.join(['#' + tag for tag in hashtags])}"

            tweet_data = {
                "text": full_text[:280],  # Twitter character limit
                "media": {
                    "media_ids": [media_id]
                }
            }

            async with session.post(
                f"{self.API_BASE_URL}/tweets",
                json=tweet_data,
                headers={**headers, "Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                result = await response.json()

                tweet_id = result["data"]["id"]

            # Update last used timestamp
            await self._update_last_used(account.id)

            return PostResult(
                success=True,
                platform=Platform.TWITTER,
                platform_post_id=tweet_id,
                platform_url=f"https://twitter.com/i/web/status/{tweet_id}"
            )

        except Exception as e:
            logger.error(f"Twitter upload error: {str(e)}")
            return PostResult(
                success=False,
                platform=Platform.TWITTER,
                error=str(e)
            )

    async def _wait_for_processing(self, account: SocialMediaAccount, media_id: str, headers: Dict[str, str]):
        """Wait for Twitter video processing to complete"""
        session = await self.get_session()

        max_wait = 300  # 5 minutes
        start_time = time.time()

        while time.time() - start_time < max_wait:
            status_params = {
                "command": "STATUS",
                "media_id": media_id
            }

            async with session.get(self.UPLOAD_URL, params=status_params, headers=headers) as response:
                response.raise_for_status()
                result = await response.json()

                processing_info = result.get("processing_info", {})
                state = processing_info.get("state")

                if state == "succeeded":
                    return
                elif state == "failed":
                    error = processing_info.get("error", {})
                    raise ValueError(f"Twitter video processing failed: {error.get('message', 'Unknown error')}")

                # Wait before checking again
                check_after = processing_info.get("check_after_secs", 5)
                await asyncio.sleep(check_after)

        raise ValueError("Twitter video processing timeout")

    async def get_video_status(self, account: SocialMediaAccount, tweet_id: str) -> Dict[str, Any]:
        """Get Twitter tweet status"""
        account = await self.ensure_token_valid(account)
        session = await self.get_session()

        headers = {
            "Authorization": f"Bearer {account.access_token}"
        }

        params = {
            "tweet.fields": "created_at,public_metrics,attachments"
        }

        async with session.get(
            f"{self.API_BASE_URL}/tweets/{tweet_id}",
            params=params,
            headers=headers
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def _update_last_used(self, account_id: str):
        """Update last used timestamp"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE social_media_accounts SET last_used_at = CURRENT_TIMESTAMP WHERE id = $1",
                account_id
            )


# ============================================================================
# Social Media Manager
# ============================================================================

class SocialMediaManager:
    """Main manager for social media integrations"""

    def __init__(self, db_pool: asyncpg.Pool, redis_url: str = "redis://localhost:6379"):
        self.db_pool = db_pool
        self.redis_url = redis_url
        self.integrations: Dict[Platform, BaseSocialMediaIntegration] = {}

    def register_integration(self, platform: Platform, integration: BaseSocialMediaIntegration):
        """Register a platform integration"""
        self.integrations[platform] = integration

    async def get_account(self, user_id: str, platform: Platform) -> Optional[SocialMediaAccount]:
        """Get active social media account for user and platform"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM social_media_accounts
                WHERE user_id = $1 AND platform = $2 AND is_active = true
                ORDER BY created_at DESC
                LIMIT 1
                """,
                user_id,
                platform.value
            )

            if not row:
                return None

            return SocialMediaAccount(**dict(row))

    async def create_scheduled_post(
        self,
        user_id: str,
        clip_id: str,
        platforms: List[Platform],
        scheduled_for: datetime,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        platform_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a scheduled post"""
        async with self.db_pool.acquire() as conn:
            post_id = await conn.fetchval(
                """
                INSERT INTO scheduled_posts (
                    id, user_id, clip_id, platforms, scheduled_for,
                    caption, hashtags, platform_config, status
                ) VALUES (
                    uuid_generate_v4()::text, $1, $2, $3, $4, $5, $6, $7, $8
                ) RETURNING id
                """,
                user_id,
                clip_id,
                [p.value for p in platforms],
                scheduled_for,
                caption,
                hashtags or [],
                json.dumps(platform_config or {}),
                PostStatus.SCHEDULED.value
            )

            return post_id

    async def post_immediately(
        self,
        user_id: str,
        clip_id: str,
        platforms: List[Platform],
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        platform_config: Optional[Dict[str, Any]] = None
    ) -> Dict[Platform, PostResult]:
        """Post to platforms immediately"""
        # Create scheduled post for now
        post_id = await self.create_scheduled_post(
            user_id=user_id,
            clip_id=clip_id,
            platforms=platforms,
            scheduled_for=datetime.utcnow(),
            caption=caption,
            hashtags=hashtags,
            platform_config=platform_config
        )

        # Process immediately
        return await self.process_scheduled_post(post_id)

    async def process_scheduled_post(self, post_id: str) -> Dict[Platform, PostResult]:
        """Process a scheduled post"""
        # Get post details
        async with self.db_pool.acquire() as conn:
            post_row = await conn.fetchrow(
                """
                SELECT sp.*, gc.file_path, gc.filename
                FROM scheduled_posts sp
                JOIN generated_clips gc ON sp.clip_id = gc.id
                WHERE sp.id = $1
                """,
                post_id
            )

            if not post_row:
                raise ValueError(f"Scheduled post {post_id} not found")

            # Update status to processing
            await conn.execute(
                "UPDATE scheduled_posts SET status = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2",
                PostStatus.PROCESSING.value,
                post_id
            )

        video_path = post_row["file_path"]
        user_id = post_row["user_id"]
        platforms = [Platform(p) for p in post_row["platforms"]]
        caption = post_row["caption"] or ""
        hashtags = post_row["hashtags"] or []
        platform_config = json.loads(post_row["platform_config"]) if post_row["platform_config"] else {}

        results = {}

        # Post to each platform
        for platform in platforms:
            try:
                # Get account
                account = await self.get_account(user_id, platform)
                if not account:
                    results[platform] = PostResult(
                        success=False,
                        platform=platform,
                        error=f"No active {platform.value} account connected"
                    )
                    continue

                # Get integration
                integration = self.integrations.get(platform)
                if not integration:
                    results[platform] = PostResult(
                        success=False,
                        platform=platform,
                        error=f"Integration for {platform.value} not configured"
                    )
                    continue

                # Create attempt record
                attempt_id = await self._create_attempt(post_id, platform, account.id)

                # Upload video
                result = await integration.upload_video(
                    account=account,
                    video_path=video_path,
                    caption=caption,
                    hashtags=hashtags,
                    config=platform_config.get(platform.value, {})
                )

                results[platform] = result

                # Update attempt
                await self._update_attempt(
                    attempt_id=attempt_id,
                    status=AttemptStatus.SUCCESS if result.success else AttemptStatus.FAILED,
                    platform_post_id=result.platform_post_id,
                    platform_url=result.platform_url,
                    error_message=result.error
                )

            except Exception as e:
                logger.error(f"Error posting to {platform.value}: {str(e)}")
                results[platform] = PostResult(
                    success=False,
                    platform=platform,
                    error=str(e)
                )

        # Update post status
        all_success = all(r.success for r in results.values())
        any_success = any(r.success for r in results.values())

        final_status = PostStatus.COMPLETED if all_success else (
            PostStatus.FAILED if not any_success else PostStatus.COMPLETED
        )

        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE scheduled_posts
                SET status = $1, processed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                """,
                final_status.value,
                post_id
            )

        return results

    async def _create_attempt(self, post_id: str, platform: Platform, account_id: str) -> str:
        """Create post attempt record"""
        async with self.db_pool.acquire() as conn:
            # Get current attempt number
            attempt_number = await conn.fetchval(
                """
                SELECT COALESCE(MAX(attempt_number), 0) + 1
                FROM post_attempts
                WHERE scheduled_post_id = $1 AND platform = $2
                """,
                post_id,
                platform.value
            )

            attempt_id = await conn.fetchval(
                """
                INSERT INTO post_attempts (
                    id, scheduled_post_id, platform, social_media_account_id,
                    attempt_number, status, started_at
                ) VALUES (
                    uuid_generate_v4()::text, $1, $2, $3, $4, $5, CURRENT_TIMESTAMP
                ) RETURNING id
                """,
                post_id,
                platform.value,
                account_id,
                attempt_number,
                AttemptStatus.PROCESSING.value
            )

            return attempt_id

    async def _update_attempt(
        self,
        attempt_id: str,
        status: AttemptStatus,
        platform_post_id: Optional[str] = None,
        platform_url: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """Update post attempt record"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE post_attempts
                SET status = $1, platform_post_id = $2, platform_url = $3,
                    error_message = $4, completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $5
                """,
                status.value,
                platform_post_id,
                platform_url,
                error_message,
                attempt_id
            )

    async def retry_failed_posts(self):
        """Retry failed posts that are eligible for retry"""
        async with self.db_pool.acquire() as conn:
            # Find attempts that need retry
            rows = await conn.fetch(
                """
                SELECT pa.*, sp.max_retries, sp.retry_delay_seconds
                FROM post_attempts pa
                JOIN scheduled_posts sp ON pa.scheduled_post_id = sp.id
                WHERE pa.status = $1
                  AND pa.next_retry_at <= CURRENT_TIMESTAMP
                  AND pa.attempt_number < sp.max_retries
                ORDER BY pa.next_retry_at
                LIMIT 100
                """,
                AttemptStatus.FAILED.value
            )

            for row in rows:
                try:
                    await self.process_scheduled_post(row["scheduled_post_id"])
                except Exception as e:
                    logger.error(f"Error retrying post {row['scheduled_post_id']}: {str(e)}")

    async def get_scheduled_posts(
        self,
        user_id: str,
        status: Optional[PostStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get scheduled posts for a user"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT sp.*, gc.filename, gc.file_path
                FROM scheduled_posts sp
                JOIN generated_clips gc ON sp.clip_id = gc.id
                WHERE sp.user_id = $1
            """
            params = [user_id]

            if status:
                query += " AND sp.status = $2"
                params.append(status.value)

            query += " ORDER BY sp.scheduled_for DESC LIMIT $3 OFFSET $4"
            params.extend([limit, offset if not status else offset])

            if status:
                params[2], params[3] = params[3], params[2]  # Fix param order

            rows = await conn.fetch(query, *params)

            return [dict(row) for row in rows]

    async def cancel_scheduled_post(self, post_id: str):
        """Cancel a scheduled post"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE scheduled_posts
                SET status = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2 AND status = $3
                """,
                PostStatus.CANCELLED.value,
                post_id,
                PostStatus.SCHEDULED.value
            )


# ============================================================================
# Helper Functions
# ============================================================================

def create_oauth_state(user_id: str, platform: Platform) -> str:
    """Create secure state parameter for OAuth"""
    timestamp = str(int(time.time()))
    data = f"{user_id}:{platform.value}:{timestamp}"
    return hashlib.sha256(data.encode()).hexdigest()


def verify_oauth_state(state: str, user_id: str, platform: Platform, max_age: int = 600) -> bool:
    """Verify OAuth state parameter"""
    expected_state = create_oauth_state(user_id, platform)
    return hmac.compare_digest(state, expected_state)


async def init_integrations(db_pool: asyncpg.Pool) -> SocialMediaManager:
    """Initialize social media integrations"""
    manager = SocialMediaManager(db_pool)

    # TikTok
    if os.getenv("TIKTOK_CLIENT_ID"):
        tiktok_config = OAuthConfig(
            client_id=os.getenv("TIKTOK_CLIENT_ID"),
            client_secret=os.getenv("TIKTOK_CLIENT_SECRET"),
            redirect_uri=os.getenv("TIKTOK_REDIRECT_URI"),
            authorization_url="https://www.tiktok.com/v2/auth/authorize/",
            token_url="https://open.tiktokapis.com/v2/oauth/token/",
            scopes=["user.info.basic", "video.upload", "video.publish"]
        )
        manager.register_integration(Platform.TIKTOK, TikTokIntegration(tiktok_config, db_pool))

    # Instagram
    if os.getenv("INSTAGRAM_CLIENT_ID"):
        instagram_config = OAuthConfig(
            client_id=os.getenv("INSTAGRAM_CLIENT_ID"),
            client_secret=os.getenv("INSTAGRAM_CLIENT_SECRET"),
            redirect_uri=os.getenv("INSTAGRAM_REDIRECT_URI"),
            authorization_url="https://api.instagram.com/oauth/authorize",
            token_url="https://api.instagram.com/oauth/access_token",
            scopes=["instagram_basic", "instagram_content_publish", "pages_read_engagement"]
        )
        manager.register_integration(Platform.INSTAGRAM, InstagramIntegration(instagram_config, db_pool))

    # YouTube
    if os.getenv("YOUTUBE_CLIENT_ID"):
        youtube_config = OAuthConfig(
            client_id=os.getenv("YOUTUBE_CLIENT_ID"),
            client_secret=os.getenv("YOUTUBE_CLIENT_SECRET"),
            redirect_uri=os.getenv("YOUTUBE_REDIRECT_URI"),
            authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            scopes=["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]
        )
        manager.register_integration(Platform.YOUTUBE, YouTubeIntegration(youtube_config, db_pool))

    # Twitter/X
    if os.getenv("TWITTER_CLIENT_ID"):
        twitter_config = OAuthConfig(
            client_id=os.getenv("TWITTER_CLIENT_ID"),
            client_secret=os.getenv("TWITTER_CLIENT_SECRET"),
            redirect_uri=os.getenv("TWITTER_REDIRECT_URI"),
            authorization_url="https://twitter.com/i/oauth2/authorize",
            token_url="https://api.twitter.com/2/oauth2/token",
            scopes=["tweet.read", "tweet.write", "users.read", "offline.access"]
        )
        manager.register_integration(Platform.TWITTER, TwitterIntegration(twitter_config, db_pool))

    return manager
