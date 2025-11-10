"""
Music swapper system with intelligent selection.

40 songs with metadata, remove after selection, reset when exhausted.
"""
import logging
import random
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class Song:
    """Music track with metadata."""
    id: int
    filename: str
    path: str
    vibe: str
    context: str
    energy: str  # low, medium, high
    bpm: int
    color: str  # For UI color coding


def load_music_library(json_path: str = None) -> List[Song]:
    """
    Load music library from JSON file.

    Args:
        json_path: Path to songs.json file. If None, uses default location.

    Returns:
        List of Song objects
    """
    if json_path is None:
        # Default to backend/music/songs.json
        current_file = Path(__file__)
        backend_dir = current_file.parent.parent.parent  # Go up to backend/
        json_path = backend_dir / "music" / "songs.json"

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)

        songs = []
        for song_data in data.get("songs", []):
            song = Song(
                id=song_data["id"],
                filename=song_data["filename"],
                path=song_data["path"],
                vibe=song_data["vibe"],
                context=song_data["context"],
                energy=song_data["energy"],
                bpm=song_data["bpm"],
                color=song_data["color"]
            )
            songs.append(song)

        logger.info(f"Loaded {len(songs)} songs from {json_path}")
        return songs

    except FileNotFoundError:
        logger.error(f"Music library JSON not found: {json_path}")
        logger.warning("Using empty music library. Add songs to backend/music/songs.json")
        return []
    except Exception as e:
        logger.error(f"Error loading music library: {e}")
        return []


# Load music library from JSON
MUSIC_LIBRARY = load_music_library()


class MusicSwapper:
    """Intelligent music selection system."""

    def __init__(self, music_library: List[Song] = None):
        """
        Initialize music swapper.

        Args:
            music_library: List of Song objects (defaults to MUSIC_LIBRARY)
        """
        self.library = music_library or MUSIC_LIBRARY
        self.available_pool = list(self.library)  # Copy for modification
        logger.info(f"Music swapper initialized with {len(self.library)} songs")

    def get_available_songs(self) -> List[Dict[str, Any]]:
        """
        Get all currently available songs for selection.

        Returns:
            List of song dicts
        """
        return [
            {
                "id": song.id,
                "filename": song.filename,
                "vibe": song.vibe,
                "context": song.context,
                "energy": song.energy,
                "bpm": song.bpm,
                "color": song.color
            }
            for song in self.available_pool
        ]

    def select_song(self, song_id: int) -> Optional[Song]:
        """
        Select a song and remove it from available pool.

        Args:
            song_id: ID of song to select

        Returns:
            Selected Song object, or None if not found
        """
        for i, song in enumerate(self.available_pool):
            if song.id == song_id:
                selected = self.available_pool.pop(i)
                logger.info(f"Selected song: {selected.filename} (ID: {song_id})")
                logger.info(f"Remaining songs in pool: {len(self.available_pool)}")

                # Auto-reset if pool exhausted
                if len(self.available_pool) == 0:
                    logger.info("Pool exhausted! Resetting to full library")
                    self.reset_pool()

                return selected

        logger.warning(f"Song ID {song_id} not found in available pool")
        return None

    def select_random_song(self) -> Song:
        """
        Select a random song from available pool.

        Returns:
            Randomly selected Song object
        """
        if len(self.available_pool) == 0:
            logger.info("Pool empty, resetting before random selection")
            self.reset_pool()

        selected = random.choice(self.available_pool)
        return self.select_song(selected.id)

    def reset_pool(self):
        """Reset available pool to full library."""
        self.available_pool = list(self.library)
        logger.info(f"Pool reset: {len(self.available_pool)} songs available")

    def get_songs_by_energy(self, energy: str) -> List[Song]:
        """
        Get songs filtered by energy level.

        Args:
            energy: 'low', 'medium', or 'high'

        Returns:
            List of matching songs
        """
        return [song for song in self.available_pool if song.energy == energy]

    def get_songs_by_bpm_range(self, min_bpm: int, max_bpm: int) -> List[Song]:
        """
        Get songs filtered by BPM range.

        Args:
            min_bpm: Minimum BPM
            max_bpm: Maximum BPM

        Returns:
            List of matching songs
        """
        return [song for song in self.available_pool if min_bpm <= song.bpm <= max_bpm]

    def save_state(self, filepath: str):
        """
        Save current pool state to file.

        Args:
            filepath: Path to save state JSON
        """
        state = {
            "available_ids": [song.id for song in self.available_pool]
        }

        with open(filepath, 'w') as f:
            json.dump(state, f)

        logger.info(f"Music swapper state saved to {filepath}")

    def load_state(self, filepath: str):
        """
        Load pool state from file.

        Args:
            filepath: Path to state JSON
        """
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)

            available_ids = set(state.get("available_ids", []))
            self.available_pool = [song for song in self.library if song.id in available_ids]

            logger.info(f"Music swapper state loaded: {len(self.available_pool)} songs available")

        except FileNotFoundError:
            logger.warning(f"State file not found: {filepath}, using full library")
            self.reset_pool()


def add_music_to_video(
    video_path: str,
    music_path: str,
    output_path: str,
    music_volume: float = 0.3
) -> bool:
    """
    Add music track to video using FFmpeg.

    Args:
        video_path: Input video path
        music_path: Music file path
        output_path: Output video path
        music_volume: Music volume (0.0 to 1.0)

    Returns:
        True if successful
    """
    import subprocess

    logger.info(f"Adding music {music_path} to {video_path}")

    # FFmpeg command to mix audio
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-i', music_path,
        '-filter_complex',
        f'[1:a]volume={music_volume}[music];[0:a][music]amix=inputs=2:duration=first[aout]',
        '-map', '0:v',
        '-map', '[aout]',
        '-c:v', 'copy',  # Copy video codec (fast)
        '-c:a', 'aac',
        '-b:a', '192k',
        '-y',
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            logger.info(f"✅ Music added successfully: {output_path}")
            return True
        else:
            logger.error(f"FFmpeg error: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error adding music: {e}")
        return False
