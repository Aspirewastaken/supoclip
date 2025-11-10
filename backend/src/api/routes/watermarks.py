"""
Watermark management API routes.

Handles uploading, listing, and deleting watermark videos for accounts.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import logging
import os
import shutil
import subprocess
import json
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/watermarks", tags=["watermarks"])

# Watermark directory (at backend/watermarks/)
WATERMARKS_DIR = Path(__file__).parent.parent.parent.parent / "watermarks"
WATERMARKS_DIR.mkdir(parents=True, exist_ok=True)
METADATA_FILE = WATERMARKS_DIR / "metadata.json"


def validate_mp4_format(file_path: str) -> Dict[str, Any]:
    """
    Validate that the uploaded file is a valid MP4 video.

    Uses FFprobe to check video format and codec.

    Args:
        file_path: Path to the video file

    Returns:
        Dict with validation results:
        - valid: bool
        - format: str (container format)
        - video_codec: str
        - duration: float (seconds)
        - width: int
        - height: int
        - error: str (if invalid)
    """
    try:
        # Use ffprobe to get video information
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            return {
                "valid": False,
                "error": "Failed to analyze video file"
            }

        probe_data = json.loads(result.stdout)

        # Check format
        if 'format' not in probe_data:
            return {
                "valid": False,
                "error": "No format information found"
            }

        format_name = probe_data['format'].get('format_name', '')
        if 'mp4' not in format_name:
            return {
                "valid": False,
                "error": f"Invalid format: {format_name}. Only MP4 is supported."
            }

        # Find video stream
        video_stream = None
        for stream in probe_data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break

        if not video_stream:
            return {
                "valid": False,
                "error": "No video stream found in file"
            }

        # Extract video information
        video_codec = video_stream.get('codec_name', 'unknown')
        width = video_stream.get('width', 0)
        height = video_stream.get('height', 0)
        duration = float(probe_data['format'].get('duration', 0))

        # Validate minimum requirements
        if width < 100 or height < 100:
            return {
                "valid": False,
                "error": f"Video resolution too small: {width}x{height}. Minimum 100x100 required."
            }

        if duration < 0.1:
            return {
                "valid": False,
                "error": f"Video duration too short: {duration}s. Minimum 0.1s required."
            }

        return {
            "valid": True,
            "format": format_name,
            "video_codec": video_codec,
            "duration": duration,
            "width": width,
            "height": height
        }

    except subprocess.TimeoutExpired:
        return {
            "valid": False,
            "error": "Video validation timeout"
        }
    except json.JSONDecodeError:
        return {
            "valid": False,
            "error": "Failed to parse video metadata"
        }
    except Exception as e:
        logger.error(f"Error validating video: {e}", exc_info=True)
        return {
            "valid": False,
            "error": f"Validation error: {str(e)}"
        }


def detect_green_screen(file_path: str) -> Dict[str, Any]:
    """
    Detect if video has green screen (optional feature).

    Uses FFmpeg to analyze average color in the video.

    Args:
        file_path: Path to video file

    Returns:
        Dict with:
        - has_green_screen: bool
        - confidence: float (0-1)
        - avg_green_ratio: float
    """
    try:
        # Extract a single frame and check if it's predominantly green
        cmd = [
            'ffmpeg',
            '-i', file_path,
            '-vf', 'select=eq(n\\,0),scale=100:100',
            '-vframes', '1',
            '-f', 'rawvideo',
            '-pix_fmt', 'rgb24',
            '-'
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=10)

        if result.returncode != 0 or len(result.stdout) == 0:
            return {
                "has_green_screen": False,
                "confidence": 0.0,
                "avg_green_ratio": 0.0,
                "note": "Could not analyze green screen"
            }

        # Parse RGB data (100x100 = 30000 bytes for RGB24)
        rgb_data = result.stdout
        expected_size = 100 * 100 * 3  # 100x100 pixels, 3 bytes per pixel (RGB)

        if len(rgb_data) < expected_size:
            return {
                "has_green_screen": False,
                "confidence": 0.0,
                "avg_green_ratio": 0.0,
                "note": "Incomplete frame data"
            }

        # Calculate average green ratio
        total_pixels = len(rgb_data) // 3
        green_pixels = 0

        for i in range(0, len(rgb_data[:expected_size]), 3):
            r, g, b = rgb_data[i], rgb_data[i+1], rgb_data[i+2]
            # Consider pixel "green" if G is significantly higher than R and B
            if g > 100 and g > r * 1.5 and g > b * 1.5:
                green_pixels += 1

        green_ratio = green_pixels / total_pixels if total_pixels > 0 else 0.0
        has_green_screen = green_ratio > 0.5  # If >50% of pixels are green

        return {
            "has_green_screen": has_green_screen,
            "confidence": min(green_ratio * 2, 1.0),  # Scale to 0-1
            "avg_green_ratio": green_ratio,
            "note": "Green screen detected" if has_green_screen else "No green screen detected"
        }

    except subprocess.TimeoutExpired:
        return {
            "has_green_screen": False,
            "confidence": 0.0,
            "avg_green_ratio": 0.0,
            "note": "Green screen detection timeout"
        }
    except Exception as e:
        logger.error(f"Error detecting green screen: {e}")
        return {
            "has_green_screen": False,
            "confidence": 0.0,
            "avg_green_ratio": 0.0,
            "note": f"Error: {str(e)}"
        }


@router.post("/upload")
async def upload_watermark(
    request: Request,
    account_id: str = Form(...),
    watermark: UploadFile = File(...)
):
    """
    Upload a watermark video for a specific account.

    The watermark will be saved as {account_id}.mp4 in the watermarks directory.
    Validates MP4 format and optionally detects green screen.

    Args:
        account_id: User/account ID (will be used as filename)
        watermark: MP4 video file

    Returns:
        JSON response with upload status and file information
    """
    try:
        logger.info(f"Uploading watermark for account: {account_id}")

        # Validate account_id (basic sanitization)
        if not account_id or len(account_id) < 1 or len(account_id) > 100:
            raise HTTPException(
                status_code=400,
                detail="Invalid account_id. Must be 1-100 characters."
            )

        # Remove any path traversal attempts
        safe_account_id = "".join(c for c in account_id if c.isalnum() or c in "-_")
        if safe_account_id != account_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid account_id. Only alphanumeric, dash, and underscore allowed."
            )

        # Check file extension
        if not watermark.filename.lower().endswith('.mp4'):
            raise HTTPException(
                status_code=400,
                detail="Only MP4 files are supported"
            )

        # Create temporary file for validation
        temp_path = WATERMARKS_DIR / f"temp_{account_id}.mp4"

        try:
            # Save uploaded file temporarily
            with open(temp_path, 'wb') as f:
                content = await watermark.read()
                f.write(content)

            # Validate MP4 format
            validation_result = validate_mp4_format(str(temp_path))

            if not validation_result.get("valid"):
                # Remove invalid file
                temp_path.unlink()
                raise HTTPException(
                    status_code=400,
                    detail=validation_result.get("error", "Invalid video file")
                )

            # Optional: Detect green screen
            green_screen_info = detect_green_screen(str(temp_path))

            # Move to final location
            final_path = WATERMARKS_DIR / f"{account_id}.mp4"
            shutil.move(str(temp_path), str(final_path))

            logger.info(f"Watermark uploaded successfully: {final_path}")

            return {
                "message": "Watermark uploaded successfully",
                "account_id": account_id,
                "filename": f"{account_id}.mp4",
                "file_path": str(final_path),
                "video_info": {
                    "format": validation_result.get("format"),
                    "codec": validation_result.get("video_codec"),
                    "duration": validation_result.get("duration"),
                    "width": validation_result.get("width"),
                    "height": validation_result.get("height")
                },
                "green_screen": green_screen_info
            }

        finally:
            # Cleanup temp file if it still exists
            if temp_path.exists():
                temp_path.unlink()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading watermark: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading watermark: {str(e)}"
        )


@router.get("/")
async def list_watermarks():
    """
    List all available watermarks.

    Returns information about all watermark files in the watermarks directory,
    including default.mp4 and account-specific watermarks.

    Returns:
        JSON response with list of watermarks and metadata
    """
    try:
        watermarks = []

        # List all .mp4 files in watermarks directory
        for watermark_file in WATERMARKS_DIR.glob("*.mp4"):
            account_id = watermark_file.stem  # filename without extension

            # Get file size
            file_size = watermark_file.stat().st_size

            # Get video info if possible
            validation_result = validate_mp4_format(str(watermark_file))

            watermark_info = {
                "account_id": account_id,
                "filename": watermark_file.name,
                "file_path": str(watermark_file),
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "is_default": account_id == "default"
            }

            # Add video info if validation succeeded
            if validation_result.get("valid"):
                watermark_info["video_info"] = {
                    "format": validation_result.get("format"),
                    "codec": validation_result.get("video_codec"),
                    "duration": validation_result.get("duration"),
                    "width": validation_result.get("width"),
                    "height": validation_result.get("height")
                }

            watermarks.append(watermark_info)

        # Load metadata if exists
        metadata = {}
        if METADATA_FILE.exists():
            try:
                with open(METADATA_FILE, 'r') as f:
                    metadata = json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")

        # Sort: default first, then alphabetically
        watermarks.sort(key=lambda x: (not x["is_default"], x["account_id"]))

        logger.info(f"Listed {len(watermarks)} watermarks")

        return {
            "watermarks": watermarks,
            "total": len(watermarks),
            "metadata": metadata,
            "watermarks_dir": str(WATERMARKS_DIR)
        }

    except Exception as e:
        logger.error(f"Error listing watermarks: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing watermarks: {str(e)}"
        )


@router.delete("/{account_id}")
async def delete_watermark(account_id: str):
    """
    Delete a watermark for a specific account.

    Removes the {account_id}.mp4 file and any associated metadata.
    Cannot delete the default.mp4 watermark.

    Args:
        account_id: Account ID whose watermark to delete

    Returns:
        JSON response with deletion status
    """
    try:
        logger.info(f"Deleting watermark for account: {account_id}")

        # Prevent deletion of default watermark
        if account_id == "default":
            raise HTTPException(
                status_code=403,
                detail="Cannot delete default watermark"
            )

        # Sanitize account_id
        safe_account_id = "".join(c for c in account_id if c.isalnum() or c in "-_")
        if safe_account_id != account_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid account_id format"
            )

        # Check if watermark exists
        watermark_path = WATERMARKS_DIR / f"{account_id}.mp4"

        if not watermark_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Watermark not found for account: {account_id}"
            )

        # Delete the file
        watermark_path.unlink()

        # Remove from metadata if exists
        if METADATA_FILE.exists():
            try:
                with open(METADATA_FILE, 'r') as f:
                    metadata = json.load(f)

                if account_id in metadata:
                    del metadata[account_id]

                    with open(METADATA_FILE, 'w') as f:
                        json.dump(metadata, f, indent=2)

                    logger.info(f"Removed metadata for account: {account_id}")
            except Exception as e:
                logger.error(f"Error updating metadata: {e}")

        logger.info(f"Watermark deleted successfully for account: {account_id}")

        return {
            "message": "Watermark deleted successfully",
            "account_id": account_id,
            "deleted_file": str(watermark_path)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting watermark: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting watermark: {str(e)}"
        )


@router.get("/{account_id}")
async def get_watermark(account_id: str):
    """
    Get a specific watermark file.

    Returns the watermark video file for download or streaming.
    Falls back to default.mp4 if account-specific watermark doesn't exist.

    Args:
        account_id: Account ID

    Returns:
        FileResponse with MP4 video
    """
    try:
        # Sanitize account_id
        safe_account_id = "".join(c for c in account_id if c.isalnum() or c in "-_")
        if safe_account_id != account_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid account_id format"
            )

        # Try account-specific watermark
        watermark_path = WATERMARKS_DIR / f"{account_id}.mp4"

        if not watermark_path.exists():
            # Fall back to default
            watermark_path = WATERMARKS_DIR / "default.mp4"

            if not watermark_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail="No watermark found for this account (no default either)"
                )

        return FileResponse(
            path=str(watermark_path),
            media_type="video/mp4",
            filename=watermark_path.name,
            headers={
                "Cache-Control": "public, max-age=3600",
                "Access-Control-Allow-Origin": "*"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving watermark: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error serving watermark: {str(e)}"
        )


@router.put("/{account_id}/metadata")
async def update_watermark_metadata(
    account_id: str,
    request: Request
):
    """
    Update watermark metadata (position, scale, opacity) for an account.

    Args:
        account_id: Account ID
        request: JSON body with metadata:
            - position: str (top_left, top_right, bottom_left, bottom_right, center)
            - scale: float (0.01-1.0, represents percentage of video width)
            - opacity: float (0.0-1.0)

    Returns:
        JSON response with updated metadata
    """
    try:
        data = await request.json()

        # Sanitize account_id
        safe_account_id = "".join(c for c in account_id if c.isalnum() or c in "-_")
        if safe_account_id != account_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid account_id format"
            )

        # Validate position
        valid_positions = ["top_left", "top_right", "bottom_left", "bottom_right", "center"]
        position = data.get("position", "bottom_right")
        if position not in valid_positions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid position. Must be one of: {', '.join(valid_positions)}"
            )

        # Validate scale
        scale = data.get("scale", 0.15)
        try:
            scale = float(scale)
            if scale < 0.01 or scale > 1.0:
                raise ValueError()
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400,
                detail="Invalid scale. Must be a number between 0.01 and 1.0"
            )

        # Validate opacity
        opacity = data.get("opacity", 1.0)
        try:
            opacity = float(opacity)
            if opacity < 0.0 or opacity > 1.0:
                raise ValueError()
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400,
                detail="Invalid opacity. Must be a number between 0.0 and 1.0"
            )

        # Load existing metadata
        metadata = {}
        if METADATA_FILE.exists():
            with open(METADATA_FILE, 'r') as f:
                metadata = json.load(f)

        # Update account metadata
        metadata[account_id] = {
            "position": position,
            "scale": scale,
            "opacity": opacity
        }

        # Save metadata
        with open(METADATA_FILE, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Updated watermark metadata for account: {account_id}")

        return {
            "message": "Metadata updated successfully",
            "account_id": account_id,
            "metadata": metadata[account_id]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating metadata: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error updating metadata: {str(e)}"
        )
