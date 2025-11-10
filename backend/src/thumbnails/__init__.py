"""
Thumbnail generation module for SupoClip.
"""

from .generator import (
    ThumbnailGenerator,
    ThumbnailStyle,
    ThumbnailVariation,
    generate_thumbnails,
    extract_interesting_frames,
    score_thumbnails_with_ai
)
from .styles import (
    get_style_by_name,
    get_all_styles,
    THUMBNAIL_STYLES
)

__all__ = [
    "ThumbnailGenerator",
    "ThumbnailStyle",
    "ThumbnailVariation",
    "generate_thumbnails",
    "extract_interesting_frames",
    "score_thumbnails_with_ai",
    "get_style_by_name",
    "get_all_styles",
    "THUMBNAIL_STYLES"
]
