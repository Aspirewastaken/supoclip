"""
Media API routes (fonts, transitions, uploads).
"""
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
import logging
import uuid
import json
import aiofiles

from ...config import Config

logger = logging.getLogger(__name__)
config = Config()
router = APIRouter(tags=["media"])


@router.get("/fonts")
async def get_available_fonts():
    """
    Get list of available fonts with metadata.

    Returns fonts with metadata from fonts.json manifest, including:
    - Basic info (name, display name, family)
    - Styling (category, style, weights)
    - Recommendations (sizes, use cases)
    - Installation status (whether font file is present)
    - Preview and licensing information
    """
    try:
        fonts_dir = Path(__file__).parent.parent.parent.parent / "fonts"
        if not fonts_dir.exists():
            return {"fonts": [], "message": "Fonts directory not found"}

        # Load font metadata from fonts.json
        fonts_json_path = fonts_dir / "fonts.json"
        font_metadata = {}

        if fonts_json_path.exists():
            try:
                with open(fonts_json_path, 'r', encoding='utf-8') as f:
                    fonts_data = json.load(f)
                    # Create lookup dictionary by font name
                    for font in fonts_data.get("fonts", []):
                        font_metadata[font["name"]] = font
                logger.info(f"Loaded metadata for {len(font_metadata)} fonts from fonts.json")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse fonts.json: {e}")

        # Scan for actual font files
        installed_fonts = set()
        for font_file in fonts_dir.glob("*.ttf"):
            installed_fonts.add(font_file.stem)

        # Build response with merged data
        font_list = []

        # First, add all fonts from metadata
        for font_name, metadata in font_metadata.items():
            is_installed = metadata["name"] in installed_fonts
            font_info = {
                **metadata,  # Include all metadata
                "installed": is_installed,
                "available": is_installed,  # Alias for clarity
                "download_url_api": f"/fonts/{metadata['name']}" if is_installed else None
            }
            font_list.append(font_info)

        # Then, add any fonts that exist but aren't in metadata
        for font_name in installed_fonts:
            if font_name not in font_metadata:
                font_list.append({
                    "id": font_name.lower().replace(" ", "-"),
                    "name": font_name,
                    "display_name": font_name.replace("-", " ").replace("_", " ").title(),
                    "family": font_name.split("-")[0],
                    "file": f"{font_name}.ttf",
                    "installed": True,
                    "available": True,
                    "category": "unknown",
                    "description": "Custom font (no metadata available)",
                    "download_url_api": f"/fonts/{font_name}"
                })

        # Sort: installed first, then alphabetically
        font_list.sort(key=lambda x: (not x["installed"], x["display_name"]))

        # Get summary stats
        installed_count = sum(1 for f in font_list if f["installed"])
        available_count = sum(1 for f in font_list if not f["installed"])

        logger.info(f"Found {installed_count} installed fonts, {available_count} available to download")

        return {
            "fonts": font_list,
            "summary": {
                "total": len(font_list),
                "installed": installed_count,
                "available_to_download": available_count
            },
            "metadata": fonts_data.get("metadata", {}) if fonts_json_path.exists() else {}
        }

    except Exception as e:
        logger.error(f"Error retrieving fonts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving fonts: {str(e)}")


@router.get("/fonts/{font_name}")
async def get_font_file(font_name: str):
    """Serve a specific font file."""
    try:
        fonts_dir = Path(__file__).parent.parent.parent.parent / "fonts"
        font_path = fonts_dir / f"{font_name}.ttf"

        if not font_path.exists():
            raise HTTPException(status_code=404, detail="Font not found")

        return FileResponse(
            path=str(font_path),
            media_type="font/ttf",
            headers={
                "Cache-Control": "public, max-age=31536000",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving font {font_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving font: {str(e)}")


@router.get("/transitions")
async def get_available_transitions():
    """Get list of available transition effects."""
    try:
        from ...video_utils import get_available_transitions
        transitions = get_available_transitions()

        transition_info = []
        for transition_path in transitions:
            transition_file = Path(transition_path)
            transition_info.append({
                "name": transition_file.stem,
                "display_name": transition_file.stem.replace("_", " ").replace("-", " ").title(),
                "file_path": transition_path
            })

        logger.info(f"Found {len(transition_info)} available transitions")
        return {"transitions": transition_info}

    except Exception as e:
        logger.error(f"Error retrieving transitions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving transitions: {str(e)}")


@router.post("/upload")
async def upload_video(request: Request):
    """Upload a video to the server."""
    try:
        # Get the form data
        form_data = await request.form()
        video_file = form_data.get("video")

        if not video_file or not hasattr(video_file, 'filename'):
            raise HTTPException(status_code=400, detail="No video file provided")

        # Create uploads directory
        uploads_dir = Path(config.temp_dir) / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        file_extension = Path(video_file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        video_path = uploads_dir / unique_filename

        # Save the uploaded file
        async with aiofiles.open(video_path, 'wb') as f:
            content = await video_file.read()
            await f.write(content)

        logger.info(f"✅ Video uploaded successfully to: {video_path}")

        return {
            "message": "Video uploaded successfully",
            "video_path": str(video_path)
        }
    except Exception as e:
        logger.error(f"❌ Error uploading video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading video: {str(e)}")
