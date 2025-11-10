"""
API routes for AI-powered title generation.

Endpoints:
- POST /ai/generate-titles - Generate viral titles for video clips
- POST /ai/generate-titles/batch - Generate titles for multiple clips
- GET /ai/title-styles - Get available title styles
- GET /ai/platforms - Get supported platforms
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...ai.title_generator import (
    TitleGenerator,
    TitleGenerationRequest,
    TitleGenerationResponse,
    Platform,
    TitleStyle,
    generate_titles_for_clip,
)
from ...database import get_db
from ...models import GeneratedClip
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Title Generation"])


@router.post("/generate-titles", response_model=TitleGenerationResponse)
async def generate_titles(request: TitleGenerationRequest):
    """
    Generate viral titles for a video clip using multiple AI models.

    This endpoint uses OpenRouter to access multiple LLMs and generate diverse,
    platform-optimized titles. Each title is scored for virality potential.

    **Parameters:**
    - `transcript_text`: The transcript text of the clip (required)
    - `platform`: Target platform (tiktok, instagram, youtube, twitter, linkedin)
    - `target_audience`: Optional description of target audience
    - `key_topics`: Optional list of key topics/themes
    - `duration_seconds`: Optional clip duration in seconds
    - `num_variations`: Number of titles to generate (3-15, default: 8)
    - `include_styles`: Optional list of specific styles to use

    **Returns:**
    - List of generated titles with virality scores
    - Best scoring title
    - Platform and generation metadata

    **Example:**
    ```json
    {
      "transcript_text": "In this clip I reveal the secret to...",
      "platform": "tiktok",
      "target_audience": "young entrepreneurs",
      "num_variations": 10
    }
    ```
    """
    try:
        logger.info(f"Generating titles for {request.platform.value} platform")

        generator = TitleGenerator()
        response = await generator.generate_titles(request)

        logger.info(f"Successfully generated {response.total_generated} titles")
        return response

    except ValueError as e:
        logger.error(f"Validation error in title generation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating titles: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate titles: {str(e)}"
        )


@router.post("/generate-titles/clip/{clip_id}", response_model=TitleGenerationResponse)
async def generate_titles_for_clip_id(
    clip_id: str,
    platform: str = "tiktok",
    target_audience: Optional[str] = None,
    num_variations: int = 8,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate titles for an existing clip by clip ID.

    This endpoint fetches the clip's transcript from the database and generates
    titles based on that content.

    **Parameters:**
    - `clip_id`: The ID of the clip to generate titles for
    - `platform`: Target platform (query param)
    - `target_audience`: Optional target audience (query param)
    - `num_variations`: Number of variations (query param, default: 8)

    **Returns:**
    - List of generated titles with virality scores

    **Example:**
    ```
    POST /ai/generate-titles/clip/123e4567-e89b-12d3-a456-426614174000?platform=instagram&num_variations=10
    ```
    """
    try:
        # Fetch clip from database
        result = await db.execute(
            select(GeneratedClip).where(GeneratedClip.id == clip_id)
        )
        clip = result.scalar_one_or_none()

        if not clip:
            raise HTTPException(status_code=404, detail=f"Clip not found: {clip_id}")

        if not clip.text:
            raise HTTPException(
                status_code=400,
                detail="Clip has no transcript text available"
            )

        logger.info(f"Generating titles for clip {clip_id}")

        # Generate titles
        request = TitleGenerationRequest(
            transcript_text=clip.text,
            platform=Platform(platform.lower()),
            target_audience=target_audience,
            duration_seconds=clip.duration,
            num_variations=num_variations
        )

        generator = TitleGenerator()
        response = await generator.generate_titles(request)

        logger.info(f"Generated {response.total_generated} titles for clip {clip_id}")
        return response

    except ValueError as e:
        logger.error(f"Invalid platform value: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating titles for clip {clip_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate titles: {str(e)}"
        )


class BatchTitleRequest(BaseModel):
    """Request for batch title generation."""
    clip_ids: List[str]
    platform: str = "tiktok"
    target_audience: Optional[str] = None
    num_variations: int = 8


class BatchTitleResponse(BaseModel):
    """Response for batch title generation."""
    results: Dict[str, TitleGenerationResponse]
    total_clips: int
    successful: int
    failed: int


@router.post("/generate-titles/batch", response_model=BatchTitleResponse)
async def generate_titles_batch(
    request: BatchTitleRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate titles for multiple clips in a batch.

    This endpoint processes multiple clips and generates titles for each one.
    Useful for bulk title generation workflows.

    **Parameters:**
    - `clip_ids`: List of clip IDs to generate titles for
    - `platform`: Target platform for all clips
    - `target_audience`: Optional target audience
    - `num_variations`: Number of variations per clip

    **Returns:**
    - Dictionary mapping clip IDs to their title generation results
    - Summary statistics

    **Example:**
    ```json
    {
      "clip_ids": ["clip-1", "clip-2", "clip-3"],
      "platform": "youtube",
      "num_variations": 5
    }
    ```
    """
    try:
        logger.info(f"Batch generating titles for {len(request.clip_ids)} clips")

        results = {}
        successful = 0
        failed = 0

        generator = TitleGenerator()

        for clip_id in request.clip_ids:
            try:
                # Fetch clip
                result = await db.execute(
                    select(GeneratedClip).where(GeneratedClip.id == clip_id)
                )
                clip = result.scalar_one_or_none()

                if not clip or not clip.text:
                    logger.warning(f"Skipping clip {clip_id}: not found or no transcript")
                    failed += 1
                    continue

                # Generate titles
                gen_request = TitleGenerationRequest(
                    transcript_text=clip.text,
                    platform=Platform(request.platform.lower()),
                    target_audience=request.target_audience,
                    duration_seconds=clip.duration,
                    num_variations=request.num_variations
                )

                response = await generator.generate_titles(gen_request)
                results[clip_id] = response
                successful += 1

            except Exception as e:
                logger.error(f"Failed to generate titles for clip {clip_id}: {e}")
                failed += 1
                continue

        logger.info(f"Batch complete: {successful} successful, {failed} failed")

        return BatchTitleResponse(
            results=results,
            total_clips=len(request.clip_ids),
            successful=successful,
            failed=failed
        )

    except Exception as e:
        logger.error(f"Error in batch title generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Batch generation failed: {str(e)}"
        )


@router.get("/title-styles")
async def get_title_styles():
    """
    Get all available title styles with descriptions.

    Returns a list of title style options that can be used to customize
    title generation. Each style represents a different approach to
    creating engaging titles.

    **Returns:**
    - List of style objects with name and description
    """
    styles = {
        "question": {
            "name": "Question",
            "description": "Starts with a question to create curiosity",
            "example": "Why Are People Obsessed With This Simple Trick?"
        },
        "shocking": {
            "name": "Shocking",
            "description": "Uses shocking or surprising elements",
            "example": "This One Mistake Cost Me Everything"
        },
        "how_to": {
            "name": "How-To",
            "description": "Educational/tutorial format",
            "example": "How to Master This Skill in 30 Days"
        },
        "listicle": {
            "name": "Listicle",
            "description": "Number-based format (X ways to...)",
            "example": "5 Secrets Nobody Tells You About Success"
        },
        "story": {
            "name": "Story",
            "description": "Narrative or story-based hook",
            "example": "The Day I Discovered This Changed Everything"
        },
        "direct": {
            "name": "Direct",
            "description": "Straightforward value proposition",
            "example": "The Only Strategy You Need for Growth"
        },
        "curiosity": {
            "name": "Curiosity Gap",
            "description": "Creates information gap technique",
            "example": "What They Don't Want You to Know"
        },
        "emotional": {
            "name": "Emotional",
            "description": "Leads with emotional hook",
            "example": "This Will Make You Rethink Everything"
        }
    }

    return {
        "styles": styles,
        "total": len(styles)
    }


@router.get("/platforms")
async def get_supported_platforms():
    """
    Get all supported social media platforms.

    Returns information about each platform including character limits
    and style guidelines.

    **Returns:**
    - Dictionary of platform information
    """
    from ...ai.title_generator import TitleGenerator

    platforms = {
        "tiktok": {
            "name": "TikTok",
            "character_limit": TitleGenerator.PLATFORM_LIMITS[Platform.TIKTOK],
            "style": TitleGenerator.PLATFORM_STYLES[Platform.TIKTOK],
            "optimal_length": "50-100 characters"
        },
        "instagram": {
            "name": "Instagram",
            "character_limit": TitleGenerator.PLATFORM_LIMITS[Platform.INSTAGRAM],
            "style": TitleGenerator.PLATFORM_STYLES[Platform.INSTAGRAM],
            "optimal_length": "40-90 characters"
        },
        "youtube": {
            "name": "YouTube",
            "character_limit": TitleGenerator.PLATFORM_LIMITS[Platform.YOUTUBE],
            "style": TitleGenerator.PLATFORM_STYLES[Platform.YOUTUBE],
            "optimal_length": "50-80 characters"
        },
        "twitter": {
            "name": "Twitter",
            "character_limit": TitleGenerator.PLATFORM_LIMITS[Platform.TWITTER],
            "style": TitleGenerator.PLATFORM_STYLES[Platform.TWITTER],
            "optimal_length": "60-100 characters"
        },
        "linkedin": {
            "name": "LinkedIn",
            "character_limit": TitleGenerator.PLATFORM_LIMITS[Platform.LINKEDIN],
            "style": TitleGenerator.PLATFORM_STYLES[Platform.LINKEDIN],
            "optimal_length": "40-90 characters"
        }
    }

    return {
        "platforms": platforms,
        "total": len(platforms)
    }


# Import BaseModel for batch requests
from pydantic import BaseModel
from typing import Dict
