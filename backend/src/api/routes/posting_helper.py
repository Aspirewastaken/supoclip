"""
Posting Helper API routes for screenshot analysis and content generation.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import base64
import logging
from typing import Dict, List, Any

from ...database import get_db
from ...services.vision_service import VisionService
from ...config import Config

logger = logging.getLogger(__name__)
config = Config()
router = APIRouter(prefix="/posting", tags=["posting"])


@router.post("/analyze-screenshot")
async def analyze_screenshot(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze a screenshot using vision AI to generate posting suggestions.

    This endpoint:
    1. Accepts an image upload (screenshot)
    2. Uses vision AI to analyze the screenshot
    3. Detects account type and platform
    4. Generates platform-specific titles, hashtags, and descriptions

    Returns:
        - account_type: Detected account type from screenshot
        - platform: Detected platform (TikTok, Instagram, YouTube, etc.)
        - suggestions: Platform-specific content suggestions
    """
    logger.info(f"📸 Analyzing screenshot: {file.filename}")

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image (PNG, JPG, JPEG, etc.)"
        )

    try:
        # Read image file
        image_data = await file.read()

        # Convert to base64 for vision API
        base64_image = base64.b64encode(image_data).decode('utf-8')

        # Initialize vision service
        vision_service = VisionService()

        # Analyze screenshot
        analysis_result = await vision_service.analyze_screenshot(
            base64_image=base64_image,
            image_type=file.content_type
        )

        logger.info(f"✅ Analysis complete - Platform: {analysis_result.get('platform')}, Account: {analysis_result.get('account_type')}")

        return analysis_result

    except Exception as e:
        logger.error(f"❌ Error analyzing screenshot: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing screenshot: {str(e)}"
        )


@router.post("/generate-content")
async def generate_platform_content(
    platform: str,
    video_title: str = None,
    video_description: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate platform-specific content without screenshot analysis.

    This is a simpler endpoint that generates content based on video metadata.

    Args:
        platform: Target platform (tiktok, instagram, youtube_shorts)
        video_title: Optional video title
        video_description: Optional video description
    """
    logger.info(f"📝 Generating content for platform: {platform}")

    if platform not in ["tiktok", "instagram", "youtube_shorts"]:
        raise HTTPException(
            status_code=400,
            detail="Platform must be one of: tiktok, instagram, youtube_shorts"
        )

    try:
        vision_service = VisionService()

        # Generate content without screenshot
        content = await vision_service.generate_platform_content(
            platform=platform,
            video_title=video_title,
            video_description=video_description
        )

        logger.info(f"✅ Content generated for {platform}")

        return {
            "platform": platform,
            "content": content
        }

    except Exception as e:
        logger.error(f"❌ Error generating content: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating content: {str(e)}"
        )
