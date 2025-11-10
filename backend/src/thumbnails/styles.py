"""
Pre-defined thumbnail styles for SupoClip.
"""

from typing import List, Optional
from .generator import ThumbnailStyle


# Pre-defined thumbnail styles
THUMBNAIL_STYLES = {
    "bold_yellow": ThumbnailStyle(
        name="Bold Yellow",
        font_size=72,
        font_color="#FFD700",  # Gold
        stroke_width=6,
        stroke_color="#000000",
        background_color="#000000",
        background_opacity=0.6,
        shadow=True,
        glow=False,
        position="middle",
        emoji_size=80,
        padding=40
    ),

    "clean_white": ThumbnailStyle(
        name="Clean White",
        font_size=68,
        font_color="#FFFFFF",
        stroke_width=4,
        stroke_color="#000000",
        background_color=None,
        background_opacity=0.0,
        shadow=True,
        glow=False,
        position="bottom",
        emoji_size=75,
        padding=50
    ),

    "neon_pink": ThumbnailStyle(
        name="Neon Pink",
        font_size=70,
        font_color="#FF10F0",  # Bright pink
        stroke_width=5,
        stroke_color="#FFFFFF",
        background_color="#000000",
        background_opacity=0.7,
        shadow=False,
        glow=True,
        position="top",
        emoji_size=78,
        padding=45
    ),

    "fire_red": ThumbnailStyle(
        name="Fire Red",
        font_size=75,
        font_color="#FF0000",  # Red
        stroke_width=7,
        stroke_color="#FFD700",  # Gold stroke
        background_color="#000000",
        background_opacity=0.5,
        shadow=True,
        glow=True,
        position="middle",
        emoji_size=85,
        padding=35
    ),

    "electric_blue": ThumbnailStyle(
        name="Electric Blue",
        font_size=66,
        font_color="#00BFFF",  # Deep sky blue
        stroke_width=4,
        stroke_color="#000080",  # Navy
        background_color="#FFFFFF",
        background_opacity=0.3,
        shadow=True,
        glow=False,
        position="bottom",
        emoji_size=72,
        padding=55
    ),

    "beast_mode": ThumbnailStyle(
        name="Beast Mode",
        font_size=80,
        font_color="#FF6600",  # Orange
        stroke_width=8,
        stroke_color="#000000",
        background_color="#000000",
        background_opacity=0.8,
        shadow=True,
        glow=True,
        position="middle",
        emoji_size=90,
        padding=30
    ),

    "minimal_black": ThumbnailStyle(
        name="Minimal Black",
        font_size=64,
        font_color="#000000",
        stroke_width=3,
        stroke_color="#FFFFFF",
        background_color="#FFFFFF",
        background_opacity=0.8,
        shadow=False,
        glow=False,
        position="bottom",
        emoji_size=70,
        padding=60
    ),

    "gradient_purple": ThumbnailStyle(
        name="Gradient Purple",
        font_size=70,
        font_color="#9D00FF",  # Purple
        stroke_width=5,
        stroke_color="#FF00FF",  # Magenta
        background_color="#000000",
        background_opacity=0.6,
        shadow=True,
        glow=True,
        position="top",
        emoji_size=76,
        padding=42
    ),

    "viral_green": ThumbnailStyle(
        name="Viral Green",
        font_size=72,
        font_color="#00FF00",  # Lime
        stroke_width=6,
        stroke_color="#000000",
        background_color="#000000",
        background_opacity=0.7,
        shadow=True,
        glow=False,
        position="middle",
        emoji_size=78,
        padding=38
    ),

    "classic_red_white": ThumbnailStyle(
        name="Classic Red & White",
        font_size=68,
        font_color="#FFFFFF",
        stroke_width=5,
        stroke_color="#FF0000",
        background_color="#FF0000",
        background_opacity=0.5,
        shadow=True,
        glow=False,
        position="bottom",
        emoji_size=74,
        padding=48
    ),

    "youtube_premium": ThumbnailStyle(
        name="YouTube Premium",
        font_size=76,
        font_color="#FFFFFF",
        stroke_width=6,
        stroke_color="#FF0000",  # YouTube red
        background_color="#000000",
        background_opacity=0.75,
        shadow=True,
        glow=False,
        position="middle",
        emoji_size=82,
        padding=40
    ),

    "tiktok_style": ThumbnailStyle(
        name="TikTok Style",
        font_size=70,
        font_color="#00F2EA",  # TikTok cyan
        stroke_width=5,
        stroke_color="#FF0050",  # TikTok pink
        background_color="#000000",
        background_opacity=0.6,
        shadow=False,
        glow=True,
        position="bottom",
        emoji_size=76,
        padding=45
    ),

    "mrbeast_style": ThumbnailStyle(
        name="MrBeast Style",
        font_size=78,
        font_color="#FFD700",  # Gold
        stroke_width=8,
        stroke_color="#8B0000",  # Dark red
        background_color="#000000",
        background_opacity=0.7,
        shadow=True,
        glow=True,
        position="middle",
        emoji_size=88,
        padding=35
    ),

    "minimalist": ThumbnailStyle(
        name="Minimalist",
        font_size=62,
        font_color="#000000",
        stroke_width=2,
        stroke_color="#FFFFFF",
        background_color=None,
        background_opacity=0.0,
        shadow=False,
        glow=False,
        position="bottom",
        emoji_size=68,
        padding=65
    ),

    "dramatic_contrast": ThumbnailStyle(
        name="Dramatic Contrast",
        font_size=74,
        font_color="#FFFFFF",
        stroke_width=7,
        stroke_color="#000000",
        background_color=None,
        background_opacity=0.0,
        shadow=True,
        glow=False,
        position="middle",
        emoji_size=80,
        padding=40
    )
}


def get_style_by_name(name: str) -> Optional[ThumbnailStyle]:
    """
    Get a thumbnail style by name.

    Args:
        name: Style name (case-insensitive, spaces/underscores flexible)

    Returns:
        ThumbnailStyle or None if not found
    """
    # Normalize name
    normalized = name.lower().replace(' ', '_').replace('-', '_')

    for key, style in THUMBNAIL_STYLES.items():
        if key == normalized or style.name.lower().replace(' ', '_') == normalized:
            return style

    return None


def get_all_styles() -> List[ThumbnailStyle]:
    """
    Get all available thumbnail styles.

    Returns:
        List of all ThumbnailStyle objects
    """
    return list(THUMBNAIL_STYLES.values())


def get_style_names() -> List[str]:
    """
    Get all available style names.

    Returns:
        List of style names
    """
    return [style.name for style in THUMBNAIL_STYLES.values()]


def get_popular_styles() -> List[ThumbnailStyle]:
    """
    Get the most popular/recommended styles.

    Returns:
        List of recommended ThumbnailStyle objects
    """
    popular = [
        "youtube_premium",
        "mrbeast_style",
        "bold_yellow",
        "tiktok_style",
        "fire_red"
    ]

    return [THUMBNAIL_STYLES[key] for key in popular if key in THUMBNAIL_STYLES]


def get_styles_by_position(position: str) -> List[ThumbnailStyle]:
    """
    Get styles filtered by text position.

    Args:
        position: "top", "middle", or "bottom"

    Returns:
        List of matching ThumbnailStyle objects
    """
    return [style for style in THUMBNAIL_STYLES.values() if style.position == position]


def get_styles_with_glow() -> List[ThumbnailStyle]:
    """
    Get styles that have glow effect enabled.

    Returns:
        List of ThumbnailStyle objects with glow
    """
    return [style for style in THUMBNAIL_STYLES.values() if style.glow]


def get_styles_with_background() -> List[ThumbnailStyle]:
    """
    Get styles that have background color.

    Returns:
        List of ThumbnailStyle objects with background
    """
    return [style for style in THUMBNAIL_STYLES.values() if style.background_color]
