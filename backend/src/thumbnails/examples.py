"""
Example usage of the SupoClip Thumbnail Generation System.

Run these examples to test the thumbnail generation functionality.
"""

import asyncio
from pathlib import Path
from typing import List

from .generator import (
    ThumbnailGenerator,
    FrameExtractionMethod,
    generate_thumbnails,
    extract_interesting_frames,
    score_thumbnails_with_ai,
    ThumbnailVariation
)
from .styles import (
    get_style_by_name,
    get_all_styles,
    get_popular_styles,
    get_style_names
)


def example_1_basic_usage(video_path: str, output_dir: str = "output"):
    """
    Example 1: Basic thumbnail generation with default settings.

    Args:
        video_path: Path to video file
        output_dir: Directory to save thumbnails
    """
    print("=" * 60)
    print("Example 1: Basic Thumbnail Generation")
    print("=" * 60)

    # Generate thumbnails with defaults
    variations = generate_thumbnails(
        video_path=video_path,
        text="This Changed EVERYTHING!"
    )

    print(f"\n✓ Generated {len(variations)} thumbnail variations")

    # Save top 5 thumbnails
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    for i, variation in enumerate(variations[:5]):
        filename = f"basic_{i+1}_{variation.method.value}_{variation.style.name.replace(' ', '_')}.jpg"
        output_file = output_path / filename
        variation.image.save(output_file, quality=95)
        print(f"  Saved: {filename}")
        print(f"    Method: {variation.method.value}")
        print(f"    Style: {variation.style.name}")
        print(f"    Score: {variation.score:.3f}")

    print(f"\n✓ Thumbnails saved to {output_dir}/\n")


def example_2_custom_methods_and_styles(video_path: str, output_dir: str = "output"):
    """
    Example 2: Custom extraction methods and specific styles.

    Args:
        video_path: Path to video file
        output_dir: Directory to save thumbnails
    """
    print("=" * 60)
    print("Example 2: Custom Methods & Styles")
    print("=" * 60)

    # Define specific extraction methods
    methods = [
        FrameExtractionMethod.FACE_CLOSEUP,
        FrameExtractionMethod.HIGH_MOTION,
        FrameExtractionMethod.BEST_COMPOSITION
    ]

    # Choose specific styles
    styles = [
        get_style_by_name("youtube_premium"),
        get_style_by_name("mrbeast_style"),
        get_style_by_name("tiktok_style")
    ]

    # Custom sizes
    sizes = [
        (1080, 1920),  # Vertical (Instagram/TikTok)
        (1280, 720)    # Horizontal (YouTube)
    ]

    print(f"\nMethods: {[m.value for m in methods]}")
    print(f"Styles: {[s.name for s in styles]}")
    print(f"Sizes: {sizes}")

    # Generate thumbnails
    variations = generate_thumbnails(
        video_path=video_path,
        text="How I Made $10,000 in ONE DAY",
        methods=methods,
        styles=styles,
        start_time=5.0,  # Start at 5 seconds
        end_time=35.0,   # End at 35 seconds
        sizes=sizes
    )

    print(f"\n✓ Generated {len(variations)} variations")
    print(f"  = {len(methods)} methods × {len(styles)} styles × {len(sizes)} sizes")

    # Save all variations
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    for i, variation in enumerate(variations):
        size_str = f"{variation.metadata['size'][0]}x{variation.metadata['size'][1]}"
        filename = f"custom_{i+1}_{variation.method.value}_{size_str}.jpg"
        output_file = output_path / filename
        variation.image.save(output_file, quality=90)

    print(f"✓ All thumbnails saved to {output_dir}/\n")


async def example_3_ai_scoring(video_path: str, output_dir: str = "output"):
    """
    Example 3: AI-powered thumbnail scoring.

    Args:
        video_path: Path to video file
        output_dir: Directory to save thumbnails
    """
    print("=" * 60)
    print("Example 3: AI-Powered Scoring")
    print("=" * 60)

    # Generate thumbnails
    print("\nGenerating thumbnails...")
    variations = generate_thumbnails(
        video_path=video_path,
        text="You Won't BELIEVE What Happened!",
        methods=[
            FrameExtractionMethod.FACE_CLOSEUP,
            FrameExtractionMethod.HIGH_MOTION
        ],
        styles=get_popular_styles()[:3]
    )

    print(f"✓ Generated {len(variations)} variations")

    # Score with AI
    print("\nScoring with AI (this may take a moment)...")
    scored_variations = await score_thumbnails_with_ai(
        variations,
        video_title="My Incredible Journey to Success",
        video_description="In this video, I share my story of how I achieved my dreams"
    )

    print(f"✓ AI scoring completed\n")

    # Display top 5 with scores and reasoning
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print("Top 5 Thumbnails:")
    print("-" * 60)
    for i, var in enumerate(scored_variations[:5]):
        print(f"\n#{i+1} - Score: {var.score:.3f}")
        print(f"  Method: {var.method.value}")
        print(f"  Style: {var.style.name}")
        print(f"  Timestamp: {var.timestamp:.2f}s")

        if "ai_reasoning" in var.metadata:
            print(f"  Reasoning: {var.metadata['ai_reasoning']}")

        if "ai_strengths" in var.metadata:
            print(f"  Strengths: {', '.join(var.metadata['ai_strengths'])}")

        # Save thumbnail
        filename = f"ai_top_{i+1}_score_{var.score:.2f}.jpg"
        output_file = output_path / filename
        var.image.save(output_file, quality=95)

    print(f"\n✓ Top thumbnails saved to {output_dir}/\n")


def example_4_frame_extraction_comparison(video_path: str, output_dir: str = "output"):
    """
    Example 4: Compare all frame extraction methods.

    Args:
        video_path: Path to video file
        output_dir: Directory to save thumbnails
    """
    print("=" * 60)
    print("Example 4: Frame Extraction Comparison")
    print("=" * 60)

    # Use all extraction methods
    all_methods = list(FrameExtractionMethod)

    print(f"\nTesting {len(all_methods)} extraction methods:")
    for method in all_methods:
        print(f"  - {method.value}")

    # Use a single, bold style for comparison
    style = get_style_by_name("youtube_premium")

    # Generate one thumbnail per method
    variations = generate_thumbnails(
        video_path=video_path,
        text="COMPARISON TEST",
        methods=all_methods,
        styles=[style],
        sizes=[(1280, 720)]  # Single size for comparison
    )

    print(f"\n✓ Generated {len(variations)} variations")

    # Save with method name in filename
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print("\nResults:")
    print("-" * 60)
    for variation in variations:
        filename = f"method_{variation.method.value}.jpg"
        output_file = output_path / filename
        variation.image.save(output_file, quality=95)

        print(f"\n{variation.method.value}:")
        print(f"  Timestamp: {variation.timestamp:.2f}s")
        print(f"  Metadata: {variation.metadata}")
        print(f"  Saved: {filename}")

    print(f"\n✓ Comparison saved to {output_dir}/\n")


def example_5_style_showcase(video_path: str, output_dir: str = "output"):
    """
    Example 5: Showcase all available styles.

    Args:
        video_path: Path to video file
        output_dir: Directory to save thumbnails
    """
    print("=" * 60)
    print("Example 5: Style Showcase")
    print("=" * 60)

    # Get all styles
    all_styles = get_all_styles()

    print(f"\nShowcasing {len(all_styles)} styles:")
    for style in all_styles:
        print(f"  - {style.name}")

    # Use middle frame for consistency
    variations = generate_thumbnails(
        video_path=video_path,
        text="STYLE SHOWCASE",
        methods=[FrameExtractionMethod.MIDDLE_FRAME],
        styles=all_styles,
        sizes=[(1280, 720)]
    )

    print(f"\n✓ Generated {len(variations)} variations")

    # Save each style
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    for variation in variations:
        style_name = variation.style.name.replace(' ', '_').replace('&', 'and')
        filename = f"style_{style_name}.jpg"
        output_file = output_path / filename
        variation.image.save(output_file, quality=95)

    print(f"✓ Style showcase saved to {output_dir}/\n")


def example_6_batch_processing(video_paths: List[str], output_dir: str = "output"):
    """
    Example 6: Batch process multiple videos.

    Args:
        video_paths: List of video file paths
        output_dir: Directory to save thumbnails
    """
    print("=" * 60)
    print("Example 6: Batch Processing")
    print("=" * 60)

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print(f"\nProcessing {len(video_paths)} videos...")

    for i, video_path in enumerate(video_paths):
        video_name = Path(video_path).stem
        print(f"\n[{i+1}/{len(video_paths)}] Processing: {video_name}")

        try:
            # Generate single best thumbnail per video
            variations = generate_thumbnails(
                video_path=video_path,
                text=video_name.upper(),
                methods=[FrameExtractionMethod.BEST_COMPOSITION],
                styles=[get_style_by_name("youtube_premium")],
                sizes=[(1280, 720)]
            )

            if variations:
                filename = f"batch_{i+1}_{video_name}.jpg"
                output_file = output_path / filename
                variations[0].image.save(output_file, quality=90)
                print(f"  ✓ Saved: {filename}")
            else:
                print(f"  ✗ Failed to generate thumbnail")

        except Exception as e:
            print(f"  ✗ Error: {e}")

    print(f"\n✓ Batch processing complete. Check {output_dir}/\n")


def example_7_custom_style(video_path: str, output_dir: str = "output"):
    """
    Example 7: Create and use a custom thumbnail style.

    Args:
        video_path: Path to video file
        output_dir: Directory to save thumbnails
    """
    print("=" * 60)
    print("Example 7: Custom Style Creation")
    print("=" * 60)

    from .generator import ThumbnailStyle

    # Create custom style
    custom_style = ThumbnailStyle(
        name="My Viral Style",
        font_size=80,
        font_color="#FF00FF",      # Magenta
        stroke_width=7,
        stroke_color="#FFFF00",    # Yellow
        background_color="#000000",
        background_opacity=0.8,
        shadow=True,
        glow=True,
        position="middle",
        emoji_size=85,
        padding=30
    )

    print("\nCustom Style Properties:")
    print(f"  Name: {custom_style.name}")
    print(f"  Font Color: {custom_style.font_color}")
    print(f"  Stroke Color: {custom_style.stroke_color}")
    print(f"  Background: {custom_style.background_color} (opacity: {custom_style.background_opacity})")
    print(f"  Effects: Shadow={custom_style.shadow}, Glow={custom_style.glow}")

    # Generate with custom style
    variations = generate_thumbnails(
        video_path=video_path,
        text="CUSTOM STYLE TEST",
        methods=[FrameExtractionMethod.MIDDLE_FRAME],
        styles=[custom_style],
        sizes=[(1280, 720)]
    )

    # Save
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    if variations:
        filename = "custom_style_example.jpg"
        output_file = output_path / filename
        variations[0].image.save(output_file, quality=95)
        print(f"\n✓ Custom style thumbnail saved: {output_dir}/{filename}\n")


def list_available_resources():
    """List all available extraction methods and styles."""
    print("=" * 60)
    print("Available Resources")
    print("=" * 60)

    # Extraction methods
    print("\nFrame Extraction Methods:")
    for method in FrameExtractionMethod:
        print(f"  - {method.value}")

    # Styles
    print(f"\nAvailable Styles ({len(get_all_styles())} total):")
    for style in get_all_styles():
        effects = []
        if style.shadow:
            effects.append("shadow")
        if style.glow:
            effects.append("glow")
        if style.background_color:
            effects.append("background")

        effects_str = f" [{', '.join(effects)}]" if effects else ""
        print(f"  - {style.name}{effects_str}")

    # Popular styles
    print("\nPopular/Recommended Styles:")
    for style in get_popular_styles():
        print(f"  - {style.name}")

    print()


# Main runner
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python examples.py <video_path> [example_number]")
        print("\nExamples:")
        print("  1 - Basic usage with defaults")
        print("  2 - Custom methods and styles")
        print("  3 - AI-powered scoring (async)")
        print("  4 - Frame extraction comparison")
        print("  5 - Style showcase")
        print("  6 - Batch processing (requires multiple videos)")
        print("  7 - Custom style creation")
        print("  list - List available resources")
        sys.exit(1)

    video_path = sys.argv[1]
    example_num = sys.argv[2] if len(sys.argv) > 2 else "1"

    if example_num == "list":
        list_available_resources()
        sys.exit(0)

    # Verify video exists
    if not Path(video_path).exists():
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    # Run example
    try:
        if example_num == "1":
            example_1_basic_usage(video_path)
        elif example_num == "2":
            example_2_custom_methods_and_styles(video_path)
        elif example_num == "3":
            asyncio.run(example_3_ai_scoring(video_path))
        elif example_num == "4":
            example_4_frame_extraction_comparison(video_path)
        elif example_num == "5":
            example_5_style_showcase(video_path)
        elif example_num == "6":
            # For batch processing, pass multiple videos
            if len(sys.argv) > 3:
                example_6_batch_processing(sys.argv[2:])
            else:
                print("Example 6 requires multiple video paths")
        elif example_num == "7":
            example_7_custom_style(video_path)
        else:
            print(f"Unknown example: {example_num}")
            sys.exit(1)

        print("✓ Example completed successfully!")

    except Exception as e:
        print(f"\n✗ Error running example: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
