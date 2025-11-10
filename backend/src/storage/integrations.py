"""
CDN integration helpers for video processing pipeline.

Handles automatic CDN upload after clip generation and URL management.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio

from .cdn import get_cdn_provider, upload_to_cdn, get_cdn_url

logger = logging.getLogger(__name__)


async def upload_clip_to_cdn(
    clip_path: str,
    filename: str,
    task_id: str
) -> Optional[str]:
    """
    Upload a clip to CDN after generation.

    Args:
        clip_path: Local path to the clip file
        filename: Clip filename
        task_id: Task ID for organizing clips

    Returns:
        CDN URL if successful, None otherwise
    """
    try:
        # Get CDN provider
        provider = get_cdn_provider()
        if not provider:
            logger.debug("CDN not configured, skipping upload")
            return None

        # Construct remote path: clips/{task_id}/{filename}
        remote_path = f"clips/{task_id}/{filename}"

        # Upload to CDN
        logger.info(f"📤 Uploading clip to CDN: {filename}")
        success = await upload_to_cdn(
            local_path=clip_path,
            remote_path=remote_path,
            provider=provider,
            content_type='video/mp4'
        )

        if success:
            # Get CDN URL
            cdn_url = get_cdn_url(
                remote_path=remote_path,
                provider=provider,
                signed=False  # Public URLs by default
            )
            logger.info(f"✅ Clip uploaded to CDN: {cdn_url}")
            return cdn_url
        else:
            logger.warning(f"⚠️ Failed to upload clip to CDN: {filename}")
            return None

    except Exception as e:
        logger.error(f"❌ Error uploading clip to CDN: {e}")
        return None


async def upload_clips_batch(
    clips_info: list,
    task_id: str
) -> Dict[str, Optional[str]]:
    """
    Upload multiple clips to CDN in batch (parallel).

    Args:
        clips_info: List of clip info dicts with 'path' and 'filename'
        task_id: Task ID for organizing clips

    Returns:
        Dictionary mapping filename to CDN URL (or None if failed)
    """
    try:
        # Upload clips in parallel
        upload_tasks = [
            upload_clip_to_cdn(
                clip_path=clip['path'],
                filename=clip['filename'],
                task_id=task_id
            )
            for clip in clips_info
        ]

        cdn_urls = await asyncio.gather(*upload_tasks, return_exceptions=True)

        # Map filenames to CDN URLs
        result = {}
        for clip, cdn_url in zip(clips_info, cdn_urls):
            if isinstance(cdn_url, Exception):
                logger.error(f"❌ Exception uploading {clip['filename']}: {cdn_url}")
                result[clip['filename']] = None
            else:
                result[clip['filename']] = cdn_url

        success_count = sum(1 for url in result.values() if url is not None)
        logger.info(f"📊 Uploaded {success_count}/{len(clips_info)} clips to CDN")

        return result

    except Exception as e:
        logger.error(f"❌ Error in batch CDN upload: {e}")
        return {clip['filename']: None for clip in clips_info}


def get_clip_url(
    filename: str,
    cdn_url: Optional[str] = None,
    task_id: Optional[str] = None,
    signed: bool = False,
    expiry: int = 3600
) -> str:
    """
    Get the best available URL for a clip with CDN fallback.

    Priority:
    1. CDN URL (if provided and valid)
    2. Generate CDN URL (if CDN configured)
    3. Direct serving URL (fallback)

    Args:
        filename: Clip filename
        cdn_url: Pre-existing CDN URL from database
        task_id: Task ID (for generating CDN path)
        signed: Whether to generate signed URL
        expiry: URL expiration in seconds (for signed URLs)

    Returns:
        Best available URL for the clip
    """
    # Use existing CDN URL if available
    if cdn_url:
        return cdn_url

    # Try to generate CDN URL if provider is configured
    provider = get_cdn_provider()
    if provider and task_id:
        remote_path = f"clips/{task_id}/{filename}"
        cdn_url = get_cdn_url(
            remote_path=remote_path,
            provider=provider,
            signed=signed,
            expiry=expiry
        )
        return cdn_url

    # Fallback to direct serving
    return f"/clips/{filename}"


async def cleanup_cdn_clips(task_id: str, filenames: list) -> int:
    """
    Delete clips from CDN when task is deleted.

    Args:
        task_id: Task ID
        filenames: List of clip filenames to delete

    Returns:
        Number of clips successfully deleted
    """
    try:
        from .cdn import delete_from_cdn

        provider = get_cdn_provider()
        if not provider:
            return 0

        delete_tasks = [
            delete_from_cdn(
                remote_path=f"clips/{task_id}/{filename}",
                provider=provider
            )
            for filename in filenames
        ]

        results = await asyncio.gather(*delete_tasks, return_exceptions=True)

        success_count = sum(1 for r in results if r is True)
        logger.info(f"🗑️ Deleted {success_count}/{len(filenames)} clips from CDN")

        return success_count

    except Exception as e:
        logger.error(f"❌ Error cleaning up CDN clips: {e}")
        return 0
