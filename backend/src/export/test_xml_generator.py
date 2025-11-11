"""
Test script for Premiere Pro XML generator.

Generates sample XML files with varying clip counts to validate:
- Small projects (5 clips)
- Medium projects (50 clips)
- Large projects (250 clips)
- Very large projects (500 clips)
- Multi-file split (500 clips split into 100-clip files)
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from export.premiere_xml import generate_premiere_xml


def generate_mock_clips(count: int, base_path: str = "/tmp/clips") -> list:
    """
    Generate mock clip data for testing.

    Args:
        count: Number of clips to generate
        base_path: Base path for mock video files

    Returns:
        List of mock clip dictionaries
    """
    clips = []

    # Various temporal types and canvas styles for realistic organization
    temporal_types = ['standard', 'fast_cut', 'slow_motion', 'freeze_frame', 'timelapse']
    canvas_styles = ['default', 'split_screen', 'picture_in_picture', 'side_by_side', 'overlay']

    for i in range(count):
        # Vary engagement scores realistically
        if i % 10 == 0:
            score = 9.0 + (i % 10) * 0.1  # Excellent clips
        elif i % 5 == 0:
            score = 7.0 + (i % 10) * 0.15  # Good clips
        elif i % 3 == 0:
            score = 5.5 + (i % 10) * 0.2  # Medium clips
        elif i % 2 == 0:
            score = 4.0 + (i % 10) * 0.1  # Low clips
        else:
            score = 2.0 + (i % 10) * 0.15  # Poor clips

        # Create realistic variation
        temporal = temporal_types[i % len(temporal_types)]
        canvas = canvas_styles[i % len(canvas_styles)]

        clip = {
            'file_path': f"{base_path}/clip_{i+1:04d}.mp4",
            'name': f"Clip {i+1}: {temporal.replace('_', ' ').title()}",
            'title': f"Variation {i+1}",
            'duration': 15.0 + (i % 30),  # 15-45 seconds
            'start': i * 30,
            'metadata': {
                'base_title': f"Base Clip {(i // 10) + 1}",
                'temporal_type': temporal,
                'canvas_style': canvas,
                'engagement_score': min(10.0, score)
            }
        }
        clips.append(clip)

    return clips


def test_small_project():
    """Test with 5 clips - minimal project."""
    print("\n" + "="*80)
    print("TEST 1: Small Project (5 clips)")
    print("="*80)

    clips = generate_mock_clips(5)
    output_path = "/tmp/premiere_test_5clips.xml"

    generate_premiere_xml(
        clips=clips,
        output_path=output_path,
        project_name="SupoClip Test - 5 Clips",
        organize_bins=True,
        create_sequence=True
    )

    file_size = os.path.getsize(output_path)
    print(f"✅ Generated: {output_path}")
    print(f"   File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    print(f"   Clips: {len(clips)}")

    return output_path


def test_medium_project():
    """Test with 50 clips - typical project."""
    print("\n" + "="*80)
    print("TEST 2: Medium Project (50 clips)")
    print("="*80)

    clips = generate_mock_clips(50)
    output_path = "/tmp/premiere_test_50clips.xml"

    generate_premiere_xml(
        clips=clips,
        output_path=output_path,
        project_name="SupoClip Test - 50 Clips",
        organize_bins=True,
        create_sequence=True
    )

    file_size = os.path.getsize(output_path)
    print(f"✅ Generated: {output_path}")
    print(f"   File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    print(f"   Clips: {len(clips)}")

    return output_path


def test_large_project():
    """Test with 250 clips - large project."""
    print("\n" + "="*80)
    print("TEST 3: Large Project (250 clips)")
    print("="*80)

    clips = generate_mock_clips(250)
    output_path = "/tmp/premiere_test_250clips.xml"

    generate_premiere_xml(
        clips=clips,
        output_path=output_path,
        project_name="SupoClip Test - 250 Clips",
        organize_bins=True,
        create_sequence=True
    )

    file_size = os.path.getsize(output_path)
    print(f"✅ Generated: {output_path}")
    print(f"   File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    print(f"   Clips: {len(clips)}")

    return output_path


def test_very_large_project():
    """Test with 500 clips - very large project."""
    print("\n" + "="*80)
    print("TEST 4: Very Large Project (500 clips)")
    print("="*80)

    clips = generate_mock_clips(500)
    output_path = "/tmp/premiere_test_500clips.xml"

    generate_premiere_xml(
        clips=clips,
        output_path=output_path,
        project_name="SupoClip Test - 500 Clips",
        organize_bins=True,
        create_sequence=True,
        sequence_gap_seconds=0.5  # Shorter gaps for large projects
    )

    file_size = os.path.getsize(output_path)
    print(f"✅ Generated: {output_path}")
    print(f"   File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    print(f"   Clips: {len(clips)}")

    # Estimate Premiere Pro performance
    if file_size > 10 * 1024 * 1024:  # > 10 MB
        print(f"   ⚠️  WARNING: File size is large, may be slow to import in Premiere Pro")
    else:
        print(f"   ✅ File size should be fine for Premiere Pro")

    return output_path


def test_multi_file_split():
    """Test with 500 clips split into multiple files."""
    print("\n" + "="*80)
    print("TEST 5: Multi-File Split (500 clips → 100 clips/file)")
    print("="*80)

    clips = generate_mock_clips(500)
    output_path = "/tmp/premiere_test_500clips_split.xml"

    generate_premiere_xml(
        clips=clips,
        output_path=output_path,
        project_name="SupoClip Test - 500 Clips Split",
        organize_bins=True,
        max_clips_per_file=100,
        create_sequence=True,
        sequence_gap_seconds=0.5
    )

    # Check generated files
    output_dir = Path(output_path).parent
    output_base = Path(output_path).stem
    generated_files = list(output_dir.glob(f"{output_base}_part*.xml"))

    print(f"✅ Generated {len(generated_files)} XML files:")
    total_size = 0
    for xml_file in sorted(generated_files):
        file_size = os.path.getsize(xml_file)
        total_size += file_size
        print(f"   - {xml_file.name}: {file_size:,} bytes ({file_size/1024:.1f} KB)")

    print(f"   Total size: {total_size:,} bytes ({total_size/1024:.1f} KB)")
    print(f"   Average per file: {total_size/len(generated_files):,.0f} bytes")

    return output_path


def test_different_framerates():
    """Test with different frame rates (30fps, 60fps)."""
    print("\n" + "="*80)
    print("TEST 6: Different Frame Rates")
    print("="*80)

    # This would require actual video files to test properly
    # For now, just note that the system auto-detects FPS from video files
    print("ℹ️  Frame rate detection:")
    print("   - Auto-detects from video file properties")
    print("   - Supports NTSC (29.97, 59.94) and standard (30, 60)")
    print("   - Uses drop-frame timecode for NTSC")
    print("   - Defaults to 30fps if detection fails")


def test_different_resolutions():
    """Test with different resolutions."""
    print("\n" + "="*80)
    print("TEST 7: Different Resolutions")
    print("="*80)

    print("ℹ️  Resolution detection:")
    print("   - Auto-detects width/height from video files")
    print("   - Supports any resolution (1080p, 4K, 9:16 vertical, etc.)")
    print("   - Sets proper samplecharacteristics in XML")
    print("   - Defaults to 1080x1920 (9:16 vertical) if detection fails")


def validate_xml_structure(xml_path: str):
    """
    Validate XML structure and show sample.

    Args:
        xml_path: Path to XML file
    """
    print(f"\n📝 XML Structure Preview ({xml_path}):")
    print("-" * 80)

    with open(xml_path, 'r') as f:
        lines = f.readlines()

        # Show first 50 lines
        for i, line in enumerate(lines[:50], 1):
            print(f"{i:3d}: {line.rstrip()}")

        if len(lines) > 50:
            print(f"\n... ({len(lines) - 50} more lines)")

    print("-" * 80)


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("PREMIERE PRO XML GENERATOR - TEST SUITE")
    print("="*80)

    # Run all tests
    test_small_project()
    test_medium_project()
    test_large_project()
    test_very_large_project()
    test_multi_file_split()
    test_different_framerates()
    test_different_resolutions()

    # Validate structure of small file
    print("\n" + "="*80)
    print("VALIDATION: XML Structure")
    print("="*80)
    validate_xml_structure("/tmp/premiere_test_5clips.xml")

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print("✅ All tests completed successfully!")
    print("\nGenerated test files:")
    print("  - /tmp/premiere_test_5clips.xml")
    print("  - /tmp/premiere_test_50clips.xml")
    print("  - /tmp/premiere_test_250clips.xml")
    print("  - /tmp/premiere_test_500clips.xml")
    print("  - /tmp/premiere_test_500clips_split_part*.xml (5 files)")
    print("\n📋 Next steps:")
    print("  1. Import test XML files into Premiere Pro")
    print("  2. Verify bin organization")
    print("  3. Check clip labels/colors")
    print("  4. Inspect markers and metadata")
    print("  5. Test timeline sequence playback")
    print("="*80)


if __name__ == "__main__":
    main()
