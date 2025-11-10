"""
Example script demonstrating AI title generation usage.

This script shows how to use the title generation system both directly
(via the TitleGenerator class) and through the API endpoints.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai.title_generator import (
    TitleGenerator,
    TitleGenerationRequest,
    Platform,
    TitleStyle,
    generate_titles_for_clip
)


async def example_basic():
    """Basic title generation example."""
    print("=" * 80)
    print("Example 1: Basic Title Generation")
    print("=" * 80)

    transcript = """
    In this video, I'm going to reveal the secret strategy that helped me grow
    my business from zero to one million dollars in revenue in just 18 months.
    Most people don't know this, but the algorithm actually favors content that
    does one specific thing. I'm going to show you exactly what that is and how
    you can use it to grow your audience 10x faster.
    """

    # Simple convenience function
    response = await generate_titles_for_clip(
        transcript=transcript,
        platform="tiktok",
        num_variations=5
    )

    print(f"\nGenerated {response.total_generated} titles for {response.platform.value}\n")
    print(f"🏆 BEST TITLE (Score: {response.best_title.virality_score:.2f}):")
    print(f"   {response.best_title.title}")
    print(f"   Style: {response.best_title.style.value}")
    print(f"   Model: {response.best_title.model_used}")
    print(f"   Reasoning: {response.best_title.reasoning}\n")

    print("ALL TITLES:")
    for i, title in enumerate(response.titles, 1):
        print(f"{i}. [{title.virality_score:.2f}] {title.title}")
        print(f"   ({title.style.value}, {title.character_count} chars, {title.model_used})\n")


async def example_platform_comparison():
    """Compare titles across different platforms."""
    print("=" * 80)
    print("Example 2: Platform-Specific Title Optimization")
    print("=" * 80)

    transcript = """
    Today I'm sharing my morning routine that completely transformed my productivity.
    I wake up at 5 AM, meditate for 20 minutes, exercise for 45 minutes, and then
    spend an hour on deep work before checking any messages. This routine has
    helped me achieve more in 6 months than I did in the previous 2 years.
    """

    platforms = [Platform.TIKTOK, Platform.INSTAGRAM, Platform.YOUTUBE]

    for platform in platforms:
        response = await generate_titles_for_clip(
            transcript=transcript,
            platform=platform.value,
            num_variations=3
        )

        print(f"\n📱 {platform.value.upper()} (limit: {TitleGenerator.PLATFORM_LIMITS[platform]} chars)")
        print(f"Best: {response.best_title.title}")
        print(f"Score: {response.best_title.virality_score:.2f}")
        print(f"Style: {response.best_title.style.value}")


async def example_targeted_audience():
    """Generate titles for specific target audiences."""
    print("\n" + "=" * 80)
    print("Example 3: Target Audience Customization")
    print("=" * 80)

    transcript = """
    Let me show you how to build a profitable side hustle while working a full-time
    job. I started my online business while working 9-5 and now make an extra
    $5,000 per month. Here are the exact steps I followed.
    """

    audiences = [
        "young professionals in their 20s",
        "busy parents looking for extra income",
        "college students seeking financial freedom"
    ]

    for audience in audiences:
        response = await generate_titles_for_clip(
            transcript=transcript,
            platform="tiktok",
            target_audience=audience,
            num_variations=2
        )

        print(f"\n👥 Audience: {audience}")
        print(f"   Title: {response.best_title.title}")
        print(f"   Score: {response.best_title.virality_score:.2f}")


async def example_specific_styles():
    """Generate titles with specific styles."""
    print("\n" + "=" * 80)
    print("Example 4: Style-Specific Title Generation")
    print("=" * 80)

    transcript = """
    I tried the viral morning routine for 30 days and the results were shocking.
    My energy levels increased, I lost 10 pounds, and my productivity doubled.
    But there was one unexpected side effect nobody warned me about.
    """

    styles = [
        TitleStyle.QUESTION,
        TitleStyle.SHOCKING,
        TitleStyle.CURIOSITY,
        TitleStyle.LISTICLE
    ]

    generator = TitleGenerator()

    for style in styles:
        request = TitleGenerationRequest(
            transcript_text=transcript,
            platform=Platform.TIKTOK,
            num_variations=2,
            include_styles=[style]
        )

        response = await generator.generate_titles(request)

        print(f"\n✨ Style: {style.value.upper()}")
        print(f"   {response.best_title.title}")


async def example_full_configuration():
    """Full example with all configuration options."""
    print("\n" + "=" * 80)
    print("Example 5: Full Configuration")
    print("=" * 80)

    generator = TitleGenerator()

    request = TitleGenerationRequest(
        transcript_text="""
        In this clip, I break down the psychology behind why certain videos
        go viral while others flop. After analyzing 1000+ viral videos,
        I discovered 3 patterns that all viral content shares.
        """,
        platform=Platform.YOUTUBE,
        target_audience="content creators and marketers",
        key_topics=["viral content", "video marketing", "social media strategy"],
        duration_seconds=45.0,
        num_variations=8,
        include_styles=[TitleStyle.LISTICLE, TitleStyle.HOW_TO, TitleStyle.CURIOSITY]
    )

    response = await generator.generate_titles(request)

    print(f"\nConfiguration:")
    print(f"  Platform: {request.platform.value}")
    print(f"  Audience: {request.target_audience}")
    print(f"  Topics: {', '.join(request.key_topics)}")
    print(f"  Duration: {request.duration_seconds}s")
    print(f"  Variations: {request.num_variations}")
    print(f"  Styles: {[s.value for s in request.include_styles]}")

    print(f"\nResults:")
    print(f"  Generated: {response.total_generated} titles")
    print(f"  Best Score: {response.best_title.virality_score:.2f}")
    print(f"  Best Title: {response.best_title.title}")

    print("\nTop 5 Titles:")
    for i, title in enumerate(response.titles[:5], 1):
        print(f"  {i}. [{title.virality_score:.2f}] {title.title}")


async def example_error_handling():
    """Demonstrate error handling."""
    print("\n" + "=" * 80)
    print("Example 6: Error Handling")
    print("=" * 80)

    generator = TitleGenerator()

    # Test with empty transcript
    try:
        request = TitleGenerationRequest(
            transcript_text="",
            platform=Platform.TIKTOK,
            num_variations=3
        )
        response = await generator.generate_titles(request)
        print("Empty transcript handled successfully")
    except Exception as e:
        print(f"✓ Error caught for empty transcript: {type(e).__name__}")

    # Test with very short transcript
    try:
        request = TitleGenerationRequest(
            transcript_text="Hi",
            platform=Platform.TIKTOK,
            num_variations=3
        )
        response = await generator.generate_titles(request)
        print(f"Short transcript processed: {len(response.titles)} titles generated")
    except Exception as e:
        print(f"✓ Error caught for short transcript: {type(e).__name__}")


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("SupoClip AI Title Generation - Examples")
    print("=" * 80)
    print("\nThis script demonstrates various uses of the title generation system.")
    print("Note: Requires OPENROUTER_API_KEY to be configured in .env\n")

    try:
        # Run examples
        await example_basic()
        await example_platform_comparison()
        await example_targeted_audience()
        await example_specific_styles()
        await example_full_configuration()
        await example_error_handling()

        print("\n" + "=" * 80)
        print("✓ All examples completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("\nMake sure:")
        print("1. OPENROUTER_API_KEY is set in backend/.env")
        print("2. You have sufficient OpenRouter credits")
        print("3. Backend dependencies are installed (uv sync)")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
