"""
API routes for thumbnail generation.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
import io
import base64
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np

from ...database import get_db
from ...thumbnails import (
    ThumbnailGenerator,
    FrameExtractionMethod,
    generate_thumbnails,
    extract_interesting_frames,
    score_thumbnails_with_ai
)
from ...thumbnails.styles import (
    get_style_by_name,
    get_all_styles,
    get_popular_styles,
    get_style_names
)
from ...config import Config

logger = logging.getLogger(__name__)
config = Config()
router = APIRouter(prefix="/thumbnails", tags=["thumbnails"])


# Request/Response Models

class ThumbnailGenerateRequest(BaseModel):
    """Request model for thumbnail generation."""
    video_path: str = Field(..., description="Path to video file")
    text: str = Field(..., description="Text to overlay on thumbnail")
    methods: Optional[List[str]] = Field(
        default=None,
        description="Frame extraction methods: face_closeup, high_motion, first_frame, middle_frame, last_frame, best_composition"
    )
    styles: Optional[List[str]] = Field(
        default=None,
        description="Style names to apply (default: popular styles)"
    )
    start_time: float = Field(default=0.0, description="Start time in seconds")
    end_time: Optional[float] = Field(default=None, description="End time in seconds")
    sizes: Optional[List[Dict[str, int]]] = Field(
        default=None,
        description="Output sizes as [{'width': 1080, 'height': 1920}, ...]"
    )
    enable_ai_scoring: bool = Field(
        default=True,
        description="Enable AI scoring for thumbnails"
    )
    video_title: Optional[str] = Field(
        default=None,
        description="Video title for AI scoring context"
    )
    video_description: Optional[str] = Field(
        default=None,
        description="Video description for AI scoring context"
    )
    return_format: str = Field(
        default="base64",
        description="Return format: 'base64' or 'url'"
    )


class ThumbnailResponse(BaseModel):
    """Response model for a single thumbnail."""
    id: str
    method: str
    style: str
    timestamp: float
    score: float
    size: Dict[str, int]
    image_data: Optional[str] = None  # Base64 encoded image
    image_url: Optional[str] = None   # URL to image file
    metadata: Dict[str, Any]


class ThumbnailGenerateResponse(BaseModel):
    """Response model for thumbnail generation."""
    success: bool
    message: str
    thumbnails: List[ThumbnailResponse]
    total_generated: int
    best_thumbnail: Optional[ThumbnailResponse] = None
    generation_time_seconds: float


class StyleResponse(BaseModel):
    """Response model for style information."""
    name: str
    font_size: int
    font_color: str
    stroke_width: int
    stroke_color: str
    background_color: Optional[str]
    position: str
    has_shadow: bool
    has_glow: bool


class StylesListResponse(BaseModel):
    """Response model for styles list."""
    styles: List[StyleResponse]
    total: int


# API Endpoints

@router.post("/generate", response_model=ThumbnailGenerateResponse)
async def generate_thumbnails_endpoint(
    request: ThumbnailGenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate thumbnails from video with various styles and extraction methods.

    This endpoint:
    1. Extracts interesting frames from the video using specified methods
    2. Applies text overlays with different styles
    3. Generates multiple size variations
    4. Optionally scores thumbnails with AI
    5. Returns thumbnails sorted by score

    **Extraction Methods:**
    - `face_closeup`: Best frame with largest, most centered face
    - `high_motion`: Frame with highest motion/action
    - `first_frame`: First frame of video/segment
    - `middle_frame`: Middle frame of video/segment
    - `last_frame`: Last frame of video/segment
    - `best_composition`: Frame with best composition (sharpness, contrast)

    **Styles:**
    - Use `GET /thumbnails/styles` to see all available styles
    - Popular styles: youtube_premium, mrbeast_style, bold_yellow, tiktok_style

    **Example Request:**
    ```json
    {
        "video_path": "/tmp/my_video.mp4",
        "text": "This Changed EVERYTHING!",
        "methods": ["face_closeup", "high_motion"],
        "styles": ["youtube_premium", "bold_yellow"],
        "start_time": 0.0,
        "end_time": 30.0,
        "sizes": [
            {"width": 1080, "height": 1920},
            {"width": 1280, "height": 720}
        ],
        "enable_ai_scoring": true,
        "video_title": "How I Made $10,000 in One Day"
    }
    ```
    """
    start_time = datetime.now()

    try:
        # Validate video path
        video_path = Path(request.video_path)
        if not video_path.exists():
            raise HTTPException(status_code=404, detail=f"Video file not found: {request.video_path}")

        # Parse extraction methods
        if request.methods:
            try:
                methods = [FrameExtractionMethod(m) for m in request.methods]
            except ValueError as e:
                valid_methods = [m.value for m in FrameExtractionMethod]
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid extraction method. Valid methods: {valid_methods}"
                )
        else:
            # Default methods
            methods = [
                FrameExtractionMethod.FACE_CLOSEUP,
                FrameExtractionMethod.HIGH_MOTION,
                FrameExtractionMethod.BEST_COMPOSITION
            ]

        # Parse styles
        if request.styles:
            styles = []
            for style_name in request.styles:
                style = get_style_by_name(style_name)
                if not style:
                    available = get_style_names()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Style '{style_name}' not found. Available styles: {available}"
                    )
                styles.append(style)
        else:
            # Use popular styles by default
            styles = get_popular_styles()[:3]

        # Parse sizes
        if request.sizes:
            sizes = [(s["width"], s["height"]) for s in request.sizes]
        else:
            # Default sizes: vertical (1080x1920), HD (1280x720), Full HD (1920x1080)
            sizes = [(1080, 1920), (1280, 720), (1920, 1080)]

        logger.info(
            f"Generating thumbnails: {len(methods)} methods × {len(styles)} styles × "
            f"{len(sizes)} sizes = {len(methods) * len(styles) * len(sizes)} total variations"
        )

        # Generate thumbnails
        variations = generate_thumbnails(
            video_path=str(video_path),
            text=request.text,
            methods=methods,
            styles=styles,
            start_time=request.start_time,
            end_time=request.end_time,
            sizes=sizes
        )

        if not variations:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate any thumbnails. Check video file and parameters."
            )

        logger.info(f"Generated {len(variations)} thumbnail variations")

        # Score with AI if enabled
        if request.enable_ai_scoring:
            try:
                logger.info("Scoring thumbnails with AI...")
                variations = await score_thumbnails_with_ai(
                    variations,
                    video_title=request.video_title,
                    video_description=request.video_description
                )
                logger.info("AI scoring completed")
            except Exception as e:
                logger.error(f"AI scoring failed: {e}")
                # Continue without AI scoring

        # Convert to response format
        thumbnails = []
        for idx, variation in enumerate(variations):
            # Convert PIL Image to base64 or save to file
            image_data = None
            image_url = None

            if request.return_format == "base64":
                # Convert to base64
                buffer = io.BytesIO()
                variation.image.save(buffer, format="JPEG", quality=90)
                buffer.seek(0)
                image_data = base64.b64encode(buffer.read()).decode()
            else:
                # Save to file
                output_dir = Path(config.temp_dir) / "thumbnails"
                output_dir.mkdir(parents=True, exist_ok=True)

                filename = (
                    f"thumbnail_{variation.method.value}_{variation.style.name.replace(' ', '_')}_"
                    f"{variation.metadata['size'][0]}x{variation.metadata['size'][1]}_{idx}.jpg"
                )
                output_path = output_dir / filename
                variation.image.save(output_path, format="JPEG", quality=90)
                image_url = f"/thumbnails/{filename}"

            thumbnail_response = ThumbnailResponse(
                id=f"thumb_{idx}",
                method=variation.method.value,
                style=variation.style.name,
                timestamp=variation.timestamp,
                score=variation.score,
                size={
                    "width": variation.metadata["size"][0],
                    "height": variation.metadata["size"][1]
                },
                image_data=image_data,
                image_url=image_url,
                metadata={
                    k: v for k, v in variation.metadata.items()
                    if k not in ["size"]  # Already in size field
                }
            )
            thumbnails.append(thumbnail_response)

        # Get best thumbnail (highest score)
        best_thumbnail = thumbnails[0] if thumbnails else None

        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds()

        logger.info(
            f"Thumbnail generation completed: {len(thumbnails)} thumbnails in {generation_time:.2f}s"
        )

        return ThumbnailGenerateResponse(
            success=True,
            message=f"Successfully generated {len(thumbnails)} thumbnails",
            thumbnails=thumbnails,
            total_generated=len(thumbnails),
            best_thumbnail=best_thumbnail,
            generation_time_seconds=generation_time
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating thumbnails: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Thumbnail generation failed: {str(e)}")


@router.get("/styles", response_model=StylesListResponse)
async def get_styles(
    position: Optional[str] = Query(None, description="Filter by position: top, middle, bottom"),
    with_glow: Optional[bool] = Query(None, description="Filter styles with glow effect"),
    with_background: Optional[bool] = Query(None, description="Filter styles with background"),
    popular_only: bool = Query(False, description="Return only popular/recommended styles")
):
    """
    Get available thumbnail styles.

    Returns a list of all available text overlay styles with their properties.
    Use filters to find specific styles for your use case.

    **Example Response:**
    ```json
    {
        "styles": [
            {
                "name": "YouTube Premium",
                "font_size": 76,
                "font_color": "#FFFFFF",
                "stroke_width": 6,
                "stroke_color": "#FF0000",
                "background_color": "#000000",
                "position": "middle",
                "has_shadow": true,
                "has_glow": false
            }
        ],
        "total": 1
    }
    ```
    """
    try:
        # Get styles based on filters
        if popular_only:
            styles = get_popular_styles()
        elif position:
            from ...thumbnails.styles import get_styles_by_position
            styles = get_styles_by_position(position)
        elif with_glow is not None:
            from ...thumbnails.styles import get_styles_with_glow
            all_styles = get_all_styles()
            if with_glow:
                from ...thumbnails.styles import get_styles_with_glow
                styles = get_styles_with_glow()
            else:
                from ...thumbnails.styles import get_styles_with_glow
                glow_styles = set(s.name for s in get_styles_with_glow())
                styles = [s for s in all_styles if s.name not in glow_styles]
        elif with_background is not None:
            from ...thumbnails.styles import get_styles_with_background
            all_styles = get_all_styles()
            if with_background:
                from ...thumbnails.styles import get_styles_with_background
                styles = get_styles_with_background()
            else:
                from ...thumbnails.styles import get_styles_with_background
                bg_styles = set(s.name for s in get_styles_with_background())
                styles = [s for s in all_styles if s.name not in bg_styles]
        else:
            styles = get_all_styles()

        # Convert to response format
        style_responses = [
            StyleResponse(
                name=style.name,
                font_size=style.font_size,
                font_color=style.font_color,
                stroke_width=style.stroke_width,
                stroke_color=style.stroke_color,
                background_color=style.background_color,
                position=style.position,
                has_shadow=style.shadow,
                has_glow=style.glow
            )
            for style in styles
        ]

        return StylesListResponse(
            styles=style_responses,
            total=len(style_responses)
        )

    except Exception as e:
        logger.error(f"Error getting styles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve styles: {str(e)}")


@router.get("/methods")
async def get_extraction_methods():
    """
    Get available frame extraction methods.

    Returns information about all available methods for extracting
    interesting frames from videos.

    **Methods:**
    - `face_closeup`: Finds frames with the largest, most centered faces
    - `high_motion`: Finds frames with the most motion/action
    - `first_frame`: Uses the first frame of the video/segment
    - `middle_frame`: Uses the middle frame of the video/segment
    - `last_frame`: Uses the last frame of the video/segment
    - `best_composition`: Finds frames with best composition (sharpness, contrast, brightness)
    """
    methods = [
        {
            "value": method.value,
            "name": method.value.replace('_', ' ').title(),
            "description": _get_method_description(method)
        }
        for method in FrameExtractionMethod
    ]

    return {
        "methods": methods,
        "total": len(methods)
    }


def _get_method_description(method: FrameExtractionMethod) -> str:
    """Get description for extraction method."""
    descriptions = {
        FrameExtractionMethod.FACE_CLOSEUP: "Extracts frame with largest, most centered face - great for talking head content",
        FrameExtractionMethod.HIGH_MOTION: "Extracts frame with highest motion/action - perfect for dynamic content",
        FrameExtractionMethod.FIRST_FRAME: "Uses first frame of video/segment - good for consistent branding",
        FrameExtractionMethod.MIDDLE_FRAME: "Uses middle frame of video/segment - safe, balanced choice",
        FrameExtractionMethod.LAST_FRAME: "Uses last frame of video/segment - works for conclusion shots",
        FrameExtractionMethod.BEST_COMPOSITION: "Finds frame with best composition (sharpness, contrast) - ideal for quality"
    }
    return descriptions.get(method, "")


@router.get("/preview")
async def preview_style(
    style_name: str = Query(..., description="Style name to preview"),
    text: str = Query(default="Preview Text", description="Text to preview")
):
    """
    Preview a thumbnail style.

    Generates a simple preview of the text overlay style without needing a video.
    Useful for selecting styles before generating actual thumbnails.
    """
    try:
        style = get_style_by_name(style_name)
        if not style:
            available = get_style_names()
            raise HTTPException(
                status_code=404,
                detail=f"Style '{style_name}' not found. Available styles: {available}"
            )

        # Create a simple preview image
        from PIL import Image, ImageDraw, ImageFont

        # Create base image (placeholder)
        width, height = 1280, 720
        img = Image.new('RGB', (width, height), (100, 100, 100))

        # Create generator and apply style
        from ...thumbnails.generator import ThumbnailGenerator
        generator = ThumbnailGenerator.__new__(ThumbnailGenerator)
        generator.video_clip = None
        generator.face_detector = None
        generator.haar_cascade = None

        # Create sample frame
        frame = np.array(img)

        # Apply text overlay
        result_img = generator.apply_text_overlay(frame, text, style)

        # Convert to bytes
        buffer = io.BytesIO()
        result_img.save(buffer, format="JPEG", quality=90)
        buffer.seek(0)

        return StreamingResponse(buffer, media_type="image/jpeg")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing style: {e}")
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")
