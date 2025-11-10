"""
Pytest configuration and shared fixtures for SupoClip backend tests.
"""
import pytest
import numpy as np
import cv2
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, List


@pytest.fixture
def sample_transcript() -> str:
    """Sample video transcript with timestamps."""
    return """
[00:00] Welcome to this amazing tutorial about AI and machine learning.
[00:15] Today we're going to cover some really exciting topics that will blow your mind.
[00:30] First, let's talk about neural networks and how they actually work.
[01:00] The key insight is that these networks learn from data, not explicit programming.
[01:30] Now, here's where it gets really interesting - attention mechanisms.
[02:00] Attention allows models to focus on what's important in the input.
[02:30] This breakthrough led to the transformer architecture that powers ChatGPT.
[03:00] Let me show you a practical example of how this works in code.
[03:30] This is absolutely mind-blowing when you see it in action.
[04:00] And that's just the beginning of what's possible with modern AI.
"""


@pytest.fixture
def sample_transcript_segments() -> List[Dict[str, Any]]:
    """Sample transcript segments for AI analysis."""
    return [
        {
            "start_time": "0:15",
            "end_time": "0:30",
            "duration": 15,
            "title": "Hook about exciting topics",
            "reasoning": "Strong opening hook with excitement",
            "engagement_score": 8,
            "category": "emotional"
        },
        {
            "start_time": "1:30",
            "end_time": "2:00",
            "duration": 30,
            "title": "Attention mechanisms explanation",
            "reasoning": "Key technical concept explained clearly",
            "engagement_score": 9,
            "category": "story"
        },
        {
            "start_time": "3:00",
            "end_time": "3:30",
            "duration": 30,
            "title": "Practical code example",
            "reasoning": "Shows real-world application",
            "engagement_score": 7,
            "category": "action"
        }
    ]


@pytest.fixture
def sample_video_duration() -> float:
    """Sample video duration in seconds (5 minutes)."""
    return 300.0


@pytest.fixture
def short_video_duration() -> float:
    """Short video duration (10 minutes)."""
    return 600.0


@pytest.fixture
def medium_video_duration() -> float:
    """Medium video duration (45 minutes)."""
    return 2700.0


@pytest.fixture
def long_video_duration() -> float:
    """Long video duration (2 hours)."""
    return 7200.0


@pytest.fixture
def temp_video_file():
    """Create a temporary test video file."""
    # Create a simple test video (10 frames, 1920x1080, 30fps)
    temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
    temp_path = temp_file.name
    temp_file.close()

    # Generate test video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(temp_path, fourcc, 30.0, (1920, 1080))

    for i in range(30):  # 1 second of video at 30fps
        # Create a colored frame (changes color each frame)
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        frame[:, :] = (i * 8, 100, 200)  # Varying blue channel
        writer.write(frame)

    writer.release()

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_vertical_video_file():
    """Create a temporary vertical (9:16) test video file."""
    temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
    temp_path = temp_file.name
    temp_file.close()

    # Generate vertical test video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(temp_path, fourcc, 30.0, (1080, 1920))

    for i in range(30):  # 1 second of video
        frame = np.zeros((1920, 1080, 3), dtype=np.uint8)
        frame[:, :] = (200, i * 8, 100)  # Varying green channel
        writer.write(frame)

    writer.release()

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def sample_music_library() -> List[Dict[str, Any]]:
    """Sample music library data."""
    return [
        {
            "id": 1,
            "filename": "upbeat-electronic.mp3",
            "path": "/music/upbeat-electronic.mp3",
            "vibe": "Energetic & Modern",
            "context": "Tech content, tutorials, fast-paced",
            "energy": "high",
            "bpm": 140,
            "color": "#FF6B6B"
        },
        {
            "id": 2,
            "filename": "chill-lofi.mp3",
            "path": "/music/chill-lofi.mp3",
            "vibe": "Relaxed & Chill",
            "context": "Study content, calm moments",
            "energy": "low",
            "bpm": 80,
            "color": "#4ECDC4"
        },
        {
            "id": 3,
            "filename": "epic-cinematic.mp3",
            "path": "/music/epic-cinematic.mp3",
            "vibe": "Epic & Dramatic",
            "context": "Storytelling, emotional moments",
            "energy": "medium",
            "bpm": 110,
            "color": "#95E1D3"
        }
    ]


@pytest.fixture
def sample_songs_json(tmp_path, sample_music_library):
    """Create a temporary songs.json file."""
    songs_file = tmp_path / "songs.json"
    with open(songs_file, 'w') as f:
        json.dump({"songs": sample_music_library}, f)
    return str(songs_file)


@pytest.fixture
def sample_clip_metadata() -> Dict[str, Any]:
    """Sample clip metadata."""
    return {
        "start_time": "1:30",
        "end_time": "2:00",
        "duration": 30,
        "title": "Amazing moment",
        "reasoning": "High engagement content",
        "engagement_score": 9,
        "category": "action"
    }


@pytest.fixture
def sample_council_response() -> str:
    """Sample JSON response from AI council member."""
    return json.dumps({
        "candidates": [
            {
                "start_time": "0:15",
                "end_time": "0:35",
                "duration": 20,
                "title": "Strong opening hook",
                "reasoning": "Captures attention immediately with bold claim",
                "engagement_score": 9,
                "category": "emotional"
            },
            {
                "start_time": "2:10",
                "end_time": "2:45",
                "duration": 35,
                "title": "Key insight revealed",
                "reasoning": "This is the core value proposition",
                "engagement_score": 8,
                "category": "story"
            }
        ],
        "overall_assessment": "High-quality educational content with strong hooks",
        "recommended_total_clips": 50
    })


@pytest.fixture
def mock_openrouter_response(mocker):
    """Mock OpenRouter API calls."""
    def _mock_response(response_json: str):
        mock = mocker.patch('src.utils.openrouter_client.call_openrouter')
        mock.return_value = response_json
        return mock
    return _mock_response


@pytest.fixture
def sample_frame():
    """Create a sample video frame (numpy array)."""
    # 1920x1080 frame with gradient
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    for i in range(1080):
        frame[i, :] = (i // 4, 128, 255 - i // 4)
    return frame


@pytest.fixture
def sample_vertical_frame():
    """Create a sample vertical video frame (1080x1920)."""
    frame = np.zeros((1920, 1080, 3), dtype=np.uint8)
    for i in range(1920):
        frame[i, :] = (128, i // 8, 200)
    return frame
