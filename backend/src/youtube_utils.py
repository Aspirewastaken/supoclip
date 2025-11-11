"""
Utility functions for YouTube-related operations.
Optimized for high-quality downloads and better error handling.
"""

import re
from urllib.parse import urlparse, parse_qs
import yt_dlp
from typing import Optional, Dict, Any
from pathlib import Path
import logging
import time

from .config import Config
from .errors import (
    youtube_breaker,
    VideoDownloadError,
    YouTubeAPIError,
    VideoNotFoundError,
    VideoTooLargeError,
    NetworkError,
    add_breadcrumb,
)

logger = logging.getLogger(__name__)
config = Config()

class YouTubeDownloader:
    """Enhanced YouTube downloader with optimized settings."""

    def __init__(self):
        self.temp_dir = Path(config.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def get_optimal_download_options(self, video_id: str) -> Dict[str, Any]:
        """Get optimal yt-dlp options for high-quality downloads with enhanced YouTube bypass."""
        output_path = self.temp_dir / f"{video_id}.%(ext)s"

        return {
            'outtmpl': str(output_path),
            # More permissive format selection to avoid "format not available" errors
            'format': 'bv*[height<=1080]+ba/b[height<=1080]/bv*+ba/b',
            'merge_output_format': 'mp4',
            'writesubtitles': False,
            'writeautomaticsub': False,
            # Optimized for speed and reliability
            'socket_timeout': 30,
            'retries': 5,  # Increased retries
            'fragment_retries': 5,
            'http_chunk_size': 10485760,  # 10MB chunks
            # Quiet operation - only errors/warnings
            'quiet': True,
            'no_warnings': False,  # Show warnings but not info
            'ignoreerrors': False,
            # Enhanced headers to avoid 403 errors
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            },
            # Simplified YouTube bypass - use android client for better reliability
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                }
            },
            # Post-processing options
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            # Metadata extraction
            'extract_flat': False,
            'writeinfojson': False,
            # Additional bypass options
            'nocheckcertificate': True,
            'prefer_insecure': False,
            'age_limit': None,
        }

def get_youtube_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various URL formats.
    Supports standard, short, embed, and mobile URLs.
    """
    if not isinstance(url, str) or not url.strip():
        return None

    url = url.strip()

    # Comprehensive regex patterns for different YouTube URL formats
    patterns = [
        r"(?:youtube\.com/(?:.*v=|v/|embed/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})",
        r"youtube\.com/watch\?v=([A-Za-z0-9_-]{11})",
        r"youtube\.com/embed/([A-Za-z0-9_-]{11})",
        r"youtube\.com/v/([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"youtube\.com/shorts/([A-Za-z0-9_-]{11})",
        r"m\.youtube\.com/watch\?v=([A-Za-z0-9_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            video_id = match.group(1)
            # Validate video ID length (YouTube IDs are always 11 characters)
            if len(video_id) == 11:
                return video_id

    # Fallback: parse query parameters
    try:
        parsed_url = urlparse(url)
        if 'youtube.com' in parsed_url.netloc.lower():
            query = parse_qs(parsed_url.query)
            video_ids = query.get("v")
            if video_ids and len(video_ids[0]) == 11:
                return video_ids[0]
    except Exception as e:
        logger.warning(f"Error parsing URL query parameters: {e}")

    return None

def validate_youtube_url(url: str) -> bool:
    """Validate if URL is a proper YouTube URL."""
    video_id = get_youtube_video_id(url)
    return video_id is not None

async def get_youtube_video_info(url: str) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive video information without downloading.
    Returns title, duration, description, and other metadata.
    Protected by circuit breaker.
    """
    video_id = get_youtube_video_id(url)
    if not video_id:
        logger.error(f"Invalid YouTube URL: {url}", extra={"url": url})
        raise VideoNotFoundError(
            message=f"Invalid YouTube URL: {url}",
            details={"url": url, "reason": "Could not extract video ID"}
        )

    add_breadcrumb(
        message="Fetching YouTube video info",
        category="youtube",
        data={"video_id": video_id, "url": url}
    )

    async def _fetch_info():
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extractaudio': False,
                'skip_download': True,
                'socket_timeout': 30,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'keep-alive',
                },
                # Simplified extractor args for better compatibility
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                    }
                },
                'nocheckcertificate': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if not info:
                    raise VideoNotFoundError(
                        message=f"Video information not found for: {url}",
                        details={"video_id": video_id, "url": url}
                    )

                return {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'description': info.get('description', ''),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                    'thumbnail': info.get('thumbnail'),
                    'format_id': info.get('format_id'),
                    'resolution': info.get('resolution'),
                    'fps': info.get('fps'),
                    'filesize': info.get('filesize'),
                }

        except yt_dlp.utils.DownloadError as e:
            logger.error(f"YouTube API error extracting video info: {e}", extra={"video_id": video_id})
            raise YouTubeAPIError(
                message=f"Failed to fetch video information from YouTube",
                details={"video_id": video_id, "url": url, "error": str(e)},
                cause=e
            )
        except Exception as e:
            logger.error(f"Unexpected error extracting video info: {e}", extra={"video_id": video_id}, exc_info=True)
            raise YouTubeAPIError(
                message=f"Unexpected error fetching video information",
                details={"video_id": video_id, "url": url, "error": str(e)},
                cause=e
            )

    # Use circuit breaker for external YouTube API calls
    try:
        return await youtube_breaker.call(_fetch_info)
    except Exception as e:
        logger.error(f"Circuit breaker error for video info: {e}", extra={"video_id": video_id})
        raise

async def get_youtube_video_title(url: str) -> Optional[str]:
    """
    Get the title of a YouTube video from a URL.
    Enhanced with better error handling and validation.
    """
    try:
        video_info = await get_youtube_video_info(url)
        return video_info.get('title') if video_info else None
    except Exception as e:
        logger.error(f"Error getting YouTube video title: {e}", extra={"url": url})
        return None

async def download_youtube_video(url: str, max_retries: int = 3) -> Optional[Path]:
    """
    Download YouTube video with optimized settings and retry logic.
    Returns the path to the downloaded file.
    Protected by circuit breaker and enhanced error handling.

    Raises:
        VideoNotFoundError: If video ID cannot be extracted or video not found
        VideoDownloadError: If download fails after all retries
        YouTubeAPIError: If YouTube API fails
    """
    logger.info(f"Starting YouTube download: {url}")

    video_id = get_youtube_video_id(url)
    if not video_id:
        logger.error(f"Could not extract video ID from URL: {url}", extra={"url": url})
        raise VideoNotFoundError(
            message=f"Could not extract video ID from URL",
            details={"url": url}
        )

    add_breadcrumb(
        message="Starting YouTube video download",
        category="youtube",
        data={"video_id": video_id, "url": url}
    )

    downloader = YouTubeDownloader()

    # Get video info first to validate and get metadata
    try:
        video_info = await get_youtube_video_info(url)
    except Exception as e:
        logger.error(f"Failed to retrieve video information: {e}", extra={"video_id": video_id})
        raise

    logger.info(
        f"Video: '{video_info.get('title')}' ({video_info.get('duration')}s)",
        extra={"video_id": video_id, "title": video_info.get('title'), "duration": video_info.get('duration')}
    )

    # Check if video is too long
    duration = video_info.get('duration', 0)
    if duration > 3600:  # 1 hour limit
        logger.warning(
            f"Video duration ({duration}s) exceeds recommended limit",
            extra={"video_id": video_id, "duration": duration}
        )
        raise VideoTooLargeError(
            message=f"Video duration ({duration}s) exceeds 1 hour limit",
            details={"video_id": video_id, "duration": duration, "limit": 3600}
        )

    # Wrap download in circuit breaker
    async def _download():
        # Retry download with exponential backoff
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Download attempt {attempt + 1}/{max_retries}",
                    extra={"video_id": video_id, "attempt": attempt + 1}
                )

                ydl_opts = downloader.get_optimal_download_options(video_id)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Download the video
                    ydl.download([url])

                    # Find the downloaded file
                    logger.info(f"Searching for downloaded file: {video_id}.*")
                    for file_path in downloader.temp_dir.glob(f"{video_id}.*"):
                        if file_path.is_file() and file_path.suffix.lower() in ['.mp4', '.mkv', '.webm']:
                            file_size = file_path.stat().st_size
                            logger.info(
                                f"Download successful: {file_path.name} ({file_size // 1024 // 1024}MB)",
                                extra={"video_id": video_id, "file_size_mb": file_size // 1024 // 1024}
                            )
                            return file_path

                    logger.warning(
                        f"No video file found after download attempt {attempt + 1}",
                        extra={"video_id": video_id, "attempt": attempt + 1}
                    )

            except yt_dlp.utils.DownloadError as e:
                last_error = e
                logger.warning(
                    f"Download attempt {attempt + 1} failed: {e}",
                    extra={"video_id": video_id, "attempt": attempt + 1, "error": str(e)}
                )
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

            except Exception as e:
                last_error = e
                logger.error(
                    f"Unexpected error during download attempt {attempt + 1}: {e}",
                    extra={"video_id": video_id, "attempt": attempt + 1},
                    exc_info=True
                )
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

        # All retries failed
        logger.error(f"All download attempts failed for: {url}", extra={"video_id": video_id})
        raise VideoDownloadError(
            message=f"Failed to download video after {max_retries} attempts",
            details={"video_id": video_id, "url": url, "attempts": max_retries, "last_error": str(last_error)},
            cause=last_error
        )

    try:
        return await youtube_breaker.call(_download)
    except Exception as e:
        logger.error(f"Circuit breaker error during download: {e}", extra={"video_id": video_id})
        raise

def get_video_duration(url: str) -> Optional[int]:
    """Get video duration in seconds without downloading."""
    video_info = get_youtube_video_info(url)
    return video_info.get('duration') if video_info else None

def is_video_suitable_for_processing(url: str, min_duration: int = 60, max_duration: int = 7200) -> bool:
    """
    Check if video is suitable for processing based on duration and other factors.
    Default limits: 1 minute to 2 hours.
    """
    video_info = get_youtube_video_info(url)
    if not video_info:
        return False

    duration = video_info.get('duration', 0)

    # Check duration constraints
    if duration < min_duration or duration > max_duration:
        logger.warning(f"Video duration {duration}s outside allowed range ({min_duration}-{max_duration}s)")
        return False

    # Additional checks could go here (e.g., content type, quality, etc.)

    return True

def cleanup_downloaded_files(video_id: str):
    """Clean up downloaded files for a specific video ID."""
    temp_dir = Path(config.temp_dir)

    for file_path in temp_dir.glob(f"{video_id}.*"):
        try:
            if file_path.is_file():
                file_path.unlink()
                logger.info(f"Cleaned up: {file_path.name}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {file_path.name}: {e}")

# Backward compatibility functions
def extract_video_id(url: str) -> Optional[str]:
    """Backward compatibility wrapper."""
    return get_youtube_video_id(url)
