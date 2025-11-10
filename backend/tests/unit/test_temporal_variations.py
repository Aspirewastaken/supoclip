"""
Unit tests for temporal variation generation.

Tests the temporal.py module which creates multiple duration options from base clips.
"""
import pytest
from src.variations.temporal import (
    generate_temporal_variations,
    batch_generate_temporal_variations,
    TemporalVariation,
    _generate_frame_offset
)


class TestTemporalVariations:
    """Test temporal variation generation."""

    def test_generate_base_variation(self):
        """Test that base variation matches original duration."""
        variations = generate_temporal_variations(
            base_start=30.0,
            base_end=50.0,
            video_duration=300.0,
            include_frame_offset=False  # Disable for predictable testing
        )

        assert len(variations) == 3
        base = variations[0]
        assert base.type == 'base'
        assert base.start_time == 30.0
        assert base.end_time == 50.0
        assert base.duration == 20.0
        assert base.frame_offset == 0.0

    def test_generate_plus4s_variation(self):
        """Test +4s variation extends end by 4 seconds."""
        variations = generate_temporal_variations(
            base_start=30.0,
            base_end=50.0,
            video_duration=300.0,
            include_frame_offset=False
        )

        plus4 = variations[1]
        assert plus4.type == '+4s'
        assert plus4.start_time == 30.0
        assert plus4.end_time == 54.0  # 50 + 4
        assert plus4.duration == 24.0

    def test_generate_plus35s_variation(self):
        """Test +35s variation extends end by 35 seconds."""
        variations = generate_temporal_variations(
            base_start=30.0,
            base_end=50.0,
            video_duration=300.0,
            include_frame_offset=False
        )

        plus35 = variations[2]
        assert plus35.type == '+35s'
        assert plus35.start_time == 30.0
        assert plus35.end_time == 85.0  # 50 + 35
        assert plus35.duration == 55.0

    def test_variation_respects_video_end_boundary(self):
        """Test that variations don't extend past video duration."""
        variations = generate_temporal_variations(
            base_start=280.0,
            base_end=295.0,
            video_duration=300.0,
            include_frame_offset=False
        )

        # +4s should be capped at 299 (295 + 4, but max 300)
        plus4 = variations[1]
        assert plus4.end_time == 299.0

        # +35s should be capped at 300
        plus35 = variations[2]
        assert plus35.end_time == 300.0

    def test_frame_offset_applied_when_enabled(self):
        """Test that frame offset is applied when enabled."""
        variations = generate_temporal_variations(
            base_start=30.0,
            base_end=50.0,
            video_duration=300.0,
            include_frame_offset=True
        )

        # Each variation should have a frame offset
        for var in variations:
            assert var.frame_offset > 0.0
            assert 0.083 <= var.frame_offset <= 0.167  # 5-10 frames at 60fps
            # Start time should be adjusted by offset
            assert var.start_time > 30.0

    def test_frame_offset_generation(self):
        """Test that frame offset is within expected range."""
        for _ in range(10):
            offset = _generate_frame_offset()
            # Should be between 5-10 frames at 60fps (0.083 - 0.167 seconds)
            assert 0.083 <= offset <= 0.167

    def test_temporal_variation_dataclass(self):
        """Test TemporalVariation dataclass."""
        var = TemporalVariation(
            type='base',
            start_time=10.0,
            end_time=30.0,
            duration=20.0,
            frame_offset=0.1
        )

        assert var.type == 'base'
        assert var.start_time == 10.0
        assert var.end_time == 30.0
        assert var.duration == 20.0
        assert var.frame_offset == 0.1


class TestBatchTemporalVariations:
    """Test batch processing of temporal variations."""

    def test_batch_generate_creates_3x_variations(self, sample_transcript_segments):
        """Test that batch generation creates 3 variations per clip."""
        clips = sample_transcript_segments[:2]  # Use first 2 clips

        variations = batch_generate_temporal_variations(
            clips=clips,
            video_duration=300.0
        )

        # Should have 3 variations per clip
        assert len(variations) == 6  # 2 clips * 3 variations

    def test_batch_variations_preserve_metadata(self, sample_transcript_segments):
        """Test that variations preserve original clip metadata."""
        clips = sample_transcript_segments[:1]

        variations = batch_generate_temporal_variations(
            clips=clips,
            video_duration=300.0
        )

        # All variations should have original metadata
        for var in variations:
            assert var['title'] == clips[0]['title']
            assert var['reasoning'] == clips[0]['reasoning']
            assert var['category'] == clips[0]['category']
            assert var['original_clip_index'] == 0

    def test_batch_variations_have_correct_types(self, sample_transcript_segments):
        """Test that batch variations have correct type labels."""
        clips = sample_transcript_segments[:1]

        variations = batch_generate_temporal_variations(
            clips=clips,
            video_duration=300.0
        )

        # Should have base, +4s, +35s in that order
        assert variations[0]['variation_type'] == 'base'
        assert variations[1]['variation_type'] == '+4s'
        assert variations[2]['variation_type'] == '+35s'

    def test_batch_parses_timestamp_format(self):
        """Test that batch function correctly parses MM:SS timestamps."""
        clips = [
            {
                'start_time': '1:30',
                'end_time': '2:00',
                'title': 'Test clip',
                'reasoning': 'Test',
                'engagement_score': 8,
                'category': 'story'
            }
        ]

        variations = batch_generate_temporal_variations(
            clips=clips,
            video_duration=300.0
        )

        # Should convert 1:30 to 90 seconds
        assert variations[0]['start_time_seconds'] >= 90.0  # >= because of frame offset

    def test_batch_with_multiple_clips_tracks_indices(self, sample_transcript_segments):
        """Test that original clip index is correctly tracked."""
        clips = sample_transcript_segments

        variations = batch_generate_temporal_variations(
            clips=clips,
            video_duration=300.0
        )

        # Check that indices are assigned correctly
        # First 3 variations should be from clip 0
        assert variations[0]['original_clip_index'] == 0
        assert variations[1]['original_clip_index'] == 0
        assert variations[2]['original_clip_index'] == 0

        # Next 3 from clip 1
        assert variations[3]['original_clip_index'] == 1
        assert variations[4]['original_clip_index'] == 1
        assert variations[5]['original_clip_index'] == 1


@pytest.mark.parametrize("start,end,video_duration,expected_count", [
    (0, 20, 100, 3),
    (50, 70, 200, 3),
    (280, 295, 300, 3),  # Near end
])
def test_variations_always_generate_three(start, end, video_duration, expected_count):
    """Test that variations always generate exactly 3 variants."""
    variations = generate_temporal_variations(
        base_start=start,
        base_end=end,
        video_duration=video_duration,
        include_frame_offset=False
    )

    assert len(variations) == expected_count
