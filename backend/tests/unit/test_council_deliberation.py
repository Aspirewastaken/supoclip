"""
Unit tests for AI council deliberation system.

Tests the council/deliberation.py module for multi-LLM clip selection.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch
from src.council.models import (
    ClipCandidate,
    ModelAnalysis,
    CouncilDeliberation,
    CouncilMember
)
from src.council.deliberation import (
    calculate_target_clips,
    deduplicate_candidates,
    select_final_clips,
    calculate_consensus,
    run_council_analysis,
)


class TestCalculateTargetClips:
    """Test target clip calculation based on video duration."""

    def test_short_video_15min(self):
        """Test short video (0-15 min) -> 50 clips."""
        target = calculate_target_clips(600)  # 10 minutes

        assert target == 50

    def test_boundary_15min(self):
        """Test boundary at exactly 15 minutes."""
        target = calculate_target_clips(900)  # 15 minutes

        assert target == 50

    def test_medium_video_45min(self):
        """Test medium video (15-90 min) -> 250 clips."""
        target = calculate_target_clips(2700)  # 45 minutes

        assert target == 250

    def test_boundary_90min(self):
        """Test boundary at exactly 90 minutes."""
        target = calculate_target_clips(5400)  # 90 minutes

        assert target == 250

    def test_long_video_2hours(self):
        """Test long video (90+ min) -> 500 clips."""
        target = calculate_target_clips(7200)  # 2 hours

        assert target == 500

    @pytest.mark.parametrize("duration,expected", [
        (300, 50),     # 5 min
        (900, 50),     # 15 min (boundary)
        (1800, 250),   # 30 min
        (5400, 250),   # 90 min (boundary)
        (10800, 500),  # 3 hours
    ])
    def test_various_durations(self, duration, expected):
        """Test target clips for various durations."""
        assert calculate_target_clips(duration) == expected


class TestDeduplicateCandidates:
    """Test candidate deduplication logic."""

    def test_empty_list(self):
        """Test deduplication with empty list."""
        result = deduplicate_candidates([])

        assert result == []

    def test_no_duplicates(self):
        """Test list with no overlapping clips."""
        candidates = [
            ClipCandidate(
                start_time="0:10",
                end_time="0:30",
                duration=20,
                title="Clip 1",
                reasoning="Test",
                engagement_score=8,
                category="action"
            ),
            ClipCandidate(
                start_time="1:00",
                end_time="1:20",
                duration=20,
                title="Clip 2",
                reasoning="Test",
                engagement_score=7,
                category="story"
            ),
        ]

        result = deduplicate_candidates(candidates)

        assert len(result) == 2

    def test_removes_duplicates_within_5s(self):
        """Test that clips within 5 seconds are deduplicated."""
        candidates = [
            ClipCandidate(
                start_time="0:10",
                end_time="0:30",
                duration=20,
                title="Clip 1",
                reasoning="Test",
                engagement_score=8,
                category="action"
            ),
            ClipCandidate(
                start_time="0:12",  # Only 2 seconds apart
                end_time="0:32",
                duration=20,
                title="Clip 2",
                reasoning="Test",
                engagement_score=7,
                category="action"
            ),
        ]

        result = deduplicate_candidates(candidates)

        # Should keep only the higher scored one
        assert len(result) == 1
        assert result[0].engagement_score == 8

    def test_keeps_higher_engagement_score(self):
        """Test that deduplication keeps clip with higher engagement score."""
        candidates = [
            ClipCandidate(
                start_time="0:10",
                end_time="0:30",
                duration=20,
                title="Lower score",
                reasoning="Test",
                engagement_score=6,
                category="action"
            ),
            ClipCandidate(
                start_time="0:11",  # 1 second apart
                end_time="0:31",
                duration=20,
                title="Higher score",
                reasoning="Test",
                engagement_score=9,
                category="action"
            ),
        ]

        result = deduplicate_candidates(candidates)

        assert len(result) == 1
        assert result[0].title == "Higher score"
        assert result[0].engagement_score == 9

    def test_sorts_by_start_time(self):
        """Test that candidates are sorted by start time before deduplication."""
        candidates = [
            ClipCandidate(
                start_time="2:00",
                end_time="2:20",
                duration=20,
                title="Later",
                reasoning="Test",
                engagement_score=8,
                category="action"
            ),
            ClipCandidate(
                start_time="0:10",
                end_time="0:30",
                duration=20,
                title="Earlier",
                reasoning="Test",
                engagement_score=7,
                category="story"
            ),
        ]

        result = deduplicate_candidates(candidates)

        # Should be sorted by time
        assert result[0].title == "Earlier"
        assert result[1].title == "Later"


class TestSelectFinalClips:
    """Test final clip selection based on votes."""

    def test_selects_top_clips_by_votes(self):
        """Test that clips with most YES votes are selected."""
        candidates = [
            {
                "candidate": ClipCandidate(
                    start_time="0:10",
                    end_time="0:30",
                    duration=20,
                    title="High votes",
                    reasoning="Test",
                    engagement_score=8,
                    category="action"
                ),
                "yes_votes": 5,
                "no_votes": 0,
                "total_confidence": 4.5
            },
            {
                "candidate": ClipCandidate(
                    start_time="1:00",
                    end_time="1:20",
                    duration=20,
                    title="Low votes",
                    reasoning="Test",
                    engagement_score=7,
                    category="story"
                ),
                "yes_votes": 2,
                "no_votes": 3,
                "total_confidence": 1.5
            },
        ]

        result = select_final_clips(candidates, target_clips=1)

        assert len(result) == 1
        assert result[0].title == "High votes"

    def test_respects_target_clips_limit(self):
        """Test that selection respects target clip count."""
        candidates = [
            {
                "candidate": ClipCandidate(
                    start_time=f"0:{i*10}",
                    end_time=f"0:{i*10+10}",
                    duration=10,
                    title=f"Clip {i}",
                    reasoning="Test",
                    engagement_score=8,
                    category="action"
                ),
                "yes_votes": 5 - i,  # Decreasing votes
                "no_votes": 0,
                "total_confidence": 4.0
            }
            for i in range(10)
        ]

        result = select_final_clips(candidates, target_clips=3)

        assert len(result) == 3

    def test_uses_confidence_as_tiebreaker(self):
        """Test that total confidence breaks ties in votes."""
        candidates = [
            {
                "candidate": ClipCandidate(
                    start_time="0:10",
                    end_time="0:30",
                    duration=20,
                    title="Higher confidence",
                    reasoning="Test",
                    engagement_score=8,
                    category="action"
                ),
                "yes_votes": 3,
                "no_votes": 2,
                "total_confidence": 2.8
            },
            {
                "candidate": ClipCandidate(
                    start_time="1:00",
                    end_time="1:20",
                    duration=20,
                    title="Lower confidence",
                    reasoning="Test",
                    engagement_score=7,
                    category="story"
                ),
                "yes_votes": 3,
                "no_votes": 2,
                "total_confidence": 1.5
            },
        ]

        result = select_final_clips(candidates, target_clips=1)

        # Should select the one with higher confidence (tie on votes)
        assert result[0].title == "Higher confidence"


class TestCalculateConsensus:
    """Test consensus level calculation."""

    def test_perfect_consensus(self):
        """Test perfect consensus (all 5 votes YES)."""
        voted = [
            {
                "candidate": ClipCandidate(
                    start_time="0:10",
                    end_time="0:30",
                    duration=20,
                    title="Clip",
                    reasoning="Test",
                    engagement_score=8,
                    category="action"
                ),
                "yes_votes": 5,
                "no_votes": 0,
                "total_confidence": 5.0
            }
        ]

        final = [voted[0]["candidate"]]

        consensus = calculate_consensus(voted, final)

        assert consensus == 1.0  # 5/5 = 1.0

    def test_no_consensus(self):
        """Test no consensus (no YES votes)."""
        voted = [
            {
                "candidate": ClipCandidate(
                    start_time="0:10",
                    end_time="0:30",
                    duration=20,
                    title="Clip",
                    reasoning="Test",
                    engagement_score=8,
                    category="action"
                ),
                "yes_votes": 0,
                "no_votes": 5,
                "total_confidence": 0.0
            }
        ]

        final = [voted[0]["candidate"]]

        consensus = calculate_consensus(voted, final)

        assert consensus == 0.0

    def test_partial_consensus(self):
        """Test partial consensus (3 out of 5 votes)."""
        voted = [
            {
                "candidate": ClipCandidate(
                    start_time="0:10",
                    end_time="0:30",
                    duration=20,
                    title="Clip",
                    reasoning="Test",
                    engagement_score=8,
                    category="action"
                ),
                "yes_votes": 3,
                "no_votes": 2,
                "total_confidence": 3.0
            }
        ]

        final = [voted[0]["candidate"]]

        consensus = calculate_consensus(voted, final)

        assert abs(consensus - 0.6) < 0.01  # 3/5 = 0.6

    def test_empty_inputs(self):
        """Test consensus with empty inputs."""
        consensus = calculate_consensus([], [])

        assert consensus == 0.0

    def test_average_consensus_across_multiple_clips(self):
        """Test consensus averaged across multiple final clips."""
        clip1 = ClipCandidate(
            start_time="0:10",
            end_time="0:30",
            duration=20,
            title="Clip 1",
            reasoning="Test",
            engagement_score=8,
            category="action"
        )
        clip2 = ClipCandidate(
            start_time="1:00",
            end_time="1:20",
            duration=20,
            title="Clip 2",
            reasoning="Test",
            engagement_score=7,
            category="story"
        )

        voted = [
            {
                "candidate": clip1,
                "yes_votes": 5,  # 100% consensus
                "no_votes": 0,
                "total_confidence": 5.0
            },
            {
                "candidate": clip2,
                "yes_votes": 3,  # 60% consensus
                "no_votes": 2,
                "total_confidence": 3.0
            }
        ]

        final = [clip1, clip2]

        consensus = calculate_consensus(voted, final)

        # Average of (5/5 + 3/5) / 2 = (1.0 + 0.6) / 2 = 0.8
        assert abs(consensus - 0.8) < 0.01


@pytest.mark.asyncio
@pytest.mark.requires_api
class TestCouncilAnalysis:
    """Integration tests for full council analysis (requires mocking)."""

    async def test_run_council_analysis_structure(self, sample_transcript, sample_video_duration, mocker):
        """Test that council analysis returns correct structure."""
        # Mock the OpenRouter API calls
        mock_response = json.dumps({
            "candidates": [
                {
                    "start_time": "0:15",
                    "end_time": "0:35",
                    "duration": 20,
                    "title": "Test clip",
                    "reasoning": "Test reasoning",
                    "engagement_score": 8,
                    "category": "action"
                }
            ],
            "overall_assessment": "Good content",
            "recommended_total_clips": 50
        })

        mocker.patch(
            'src.council.deliberation.call_openrouter',
            return_value=mock_response
        )

        result = await run_council_analysis(
            transcript=sample_transcript,
            video_duration=sample_video_duration,
            user_notes="Test notes"
        )

        assert isinstance(result, CouncilDeliberation)
        assert result.video_duration == sample_video_duration
        assert result.target_clips > 0
        assert isinstance(result.model_analyses, list)
        assert isinstance(result.final_candidates, list)
        assert 0 <= result.consensus_level <= 1

    async def test_target_clips_calculated_correctly(self, sample_transcript, mocker):
        """Test that target clips are calculated based on video duration."""
        mock_response = json.dumps({
            "candidates": [],
            "overall_assessment": "Test",
            "recommended_total_clips": 50
        })

        mocker.patch(
            'src.council.deliberation.call_openrouter',
            return_value=mock_response
        )

        # Test with short video (should be 50 clips)
        result = await run_council_analysis(
            transcript=sample_transcript,
            video_duration=600,  # 10 minutes
            user_notes=""
        )

        assert result.target_clips == 50

        # Test with medium video (should be 250 clips)
        result = await run_council_analysis(
            transcript=sample_transcript,
            video_duration=2700,  # 45 minutes
            user_notes=""
        )

        assert result.target_clips == 250


class TestClipCandidateValidation:
    """Test ClipCandidate model validation."""

    def test_valid_clip_candidate(self):
        """Test creating a valid clip candidate."""
        clip = ClipCandidate(
            start_time="0:10",
            end_time="0:30",
            duration=20,
            title="Test clip",
            reasoning="Good content",
            engagement_score=8.5,
            category="action"
        )

        assert clip.start_time == "0:10"
        assert clip.duration == 20
        assert clip.engagement_score == 8.5

    def test_engagement_score_bounds(self):
        """Test that engagement score must be 0-10."""
        # Valid score
        clip = ClipCandidate(
            start_time="0:10",
            end_time="0:30",
            duration=20,
            title="Test",
            reasoning="Test",
            engagement_score=5.0,
            category="action"
        )
        assert clip.engagement_score == 5.0

        # Invalid score (>10) should raise validation error
        with pytest.raises(Exception):  # Pydantic ValidationError
            ClipCandidate(
                start_time="0:10",
                end_time="0:30",
                duration=20,
                title="Test",
                reasoning="Test",
                engagement_score=11.0,
                category="action"
            )


class TestModelAnalysis:
    """Test ModelAnalysis structure."""

    def test_model_analysis_creation(self):
        """Test creating a ModelAnalysis object."""
        candidates = [
            ClipCandidate(
                start_time="0:10",
                end_time="0:30",
                duration=20,
                title="Clip 1",
                reasoning="Good",
                engagement_score=8,
                category="action"
            )
        ]

        analysis = ModelAnalysis(
            model_name="Test Model",
            candidates=candidates,
            overall_assessment="Quality content",
            recommended_total_clips=50
        )

        assert analysis.model_name == "Test Model"
        assert len(analysis.candidates) == 1
        assert analysis.recommended_total_clips == 50
