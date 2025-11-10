"""
Unit tests for music swapper system.

Tests the music/swapper.py module which manages intelligent music selection.
"""
import pytest
import json
import tempfile
from pathlib import Path
from src.music.swapper import (
    Song,
    MusicSwapper,
    load_music_library,
)


class TestSongDataclass:
    """Test Song dataclass."""

    def test_song_creation(self):
        """Test creating a Song object."""
        song = Song(
            id=1,
            filename="test.mp3",
            path="/music/test.mp3",
            vibe="Energetic",
            context="Tech content",
            energy="high",
            bpm=140,
            color="#FF6B6B"
        )

        assert song.id == 1
        assert song.filename == "test.mp3"
        assert song.energy == "high"
        assert song.bpm == 140


class TestLoadMusicLibrary:
    """Test music library loading."""

    def test_load_from_json(self, sample_songs_json):
        """Test loading music library from JSON file."""
        songs = load_music_library(sample_songs_json)

        assert len(songs) == 3
        assert all(isinstance(s, Song) for s in songs)

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file returns empty list."""
        songs = load_music_library("/nonexistent/songs.json")

        assert songs == []

    def test_load_parses_all_fields(self, sample_songs_json):
        """Test that all fields are correctly parsed."""
        songs = load_music_library(sample_songs_json)

        song = songs[0]
        assert song.id == 1
        assert song.filename == "upbeat-electronic.mp3"
        assert song.vibe == "Energetic & Modern"
        assert song.energy == "high"
        assert song.bpm == 140
        assert song.color == "#FF6B6B"


class TestMusicSwapper:
    """Test MusicSwapper class."""

    @pytest.fixture
    def swapper(self, sample_music_library):
        """Create a MusicSwapper with sample library."""
        songs = [Song(**data) for data in sample_music_library]
        return MusicSwapper(music_library=songs)

    def test_initialization(self, swapper, sample_music_library):
        """Test swapper initializes with full library."""
        assert len(swapper.library) == 3
        assert len(swapper.available_pool) == 3

    def test_get_available_songs(self, swapper):
        """Test getting available songs."""
        available = swapper.get_available_songs()

        assert len(available) == 3
        assert all(isinstance(s, dict) for s in available)
        assert all('id' in s for s in available)

    def test_select_song_removes_from_pool(self, swapper):
        """Test that selecting a song removes it from available pool."""
        initial_count = len(swapper.available_pool)

        song = swapper.select_song(song_id=1)

        assert song is not None
        assert song.id == 1
        assert len(swapper.available_pool) == initial_count - 1

    def test_select_song_returns_none_for_invalid_id(self, swapper):
        """Test that selecting invalid ID returns None."""
        song = swapper.select_song(song_id=999)

        assert song is None

    def test_select_random_song(self, swapper):
        """Test random song selection."""
        song = swapper.select_random_song()

        assert song is not None
        assert isinstance(song, Song)
        assert len(swapper.available_pool) == 2  # One removed

    def test_pool_auto_resets_when_exhausted(self, swapper):
        """Test that pool automatically resets when exhausted."""
        # Select all songs
        swapper.select_song(1)
        swapper.select_song(2)
        swapper.select_song(3)  # This should trigger auto-reset

        # Pool should be refilled
        assert len(swapper.available_pool) == 3

    def test_manual_reset_pool(self, swapper):
        """Test manually resetting the pool."""
        swapper.select_song(1)
        swapper.select_song(2)
        assert len(swapper.available_pool) == 1

        swapper.reset_pool()

        assert len(swapper.available_pool) == 3

    def test_get_songs_by_energy(self, swapper):
        """Test filtering songs by energy level."""
        high_energy = swapper.get_songs_by_energy('high')
        low_energy = swapper.get_songs_by_energy('low')

        assert len(high_energy) == 1
        assert high_energy[0].energy == 'high'
        assert len(low_energy) == 1
        assert low_energy[0].energy == 'low'

    def test_get_songs_by_bpm_range(self, swapper):
        """Test filtering songs by BPM range."""
        slow_songs = swapper.get_songs_by_bpm_range(70, 100)
        fast_songs = swapper.get_songs_by_bpm_range(120, 150)

        assert len(slow_songs) == 1
        assert slow_songs[0].bpm == 80
        assert len(fast_songs) == 1
        assert fast_songs[0].bpm == 140

    def test_random_selection_resets_empty_pool(self, sample_music_library):
        """Test that random selection resets if pool is empty."""
        songs = [Song(**data) for data in sample_music_library]
        swapper = MusicSwapper(music_library=songs)

        # Manually empty the pool
        swapper.available_pool = []

        # Random selection should reset and select
        song = swapper.select_random_song()

        assert song is not None
        assert len(swapper.available_pool) == 2  # Reset to 3, then selected 1


class TestMusicSwapperState:
    """Test music swapper state persistence."""

    @pytest.fixture
    def swapper(self, sample_music_library):
        songs = [Song(**data) for data in sample_music_library]
        return MusicSwapper(music_library=songs)

    def test_save_state(self, swapper, tmp_path):
        """Test saving swapper state to file."""
        # Select some songs
        swapper.select_song(1)
        swapper.select_song(2)

        state_file = tmp_path / "state.json"
        swapper.save_state(str(state_file))

        assert state_file.exists()

        # Verify state content
        with open(state_file, 'r') as f:
            data = json.load(f)

        assert 'available_ids' in data
        assert len(data['available_ids']) == 1
        assert 3 in data['available_ids']  # Only ID 3 should remain

    def test_load_state(self, swapper, tmp_path):
        """Test loading swapper state from file."""
        # Create a state file manually
        state_file = tmp_path / "state.json"
        with open(state_file, 'w') as f:
            json.dump({"available_ids": [1, 3]}, f)

        swapper.load_state(str(state_file))

        # Should only have songs with IDs 1 and 3
        assert len(swapper.available_pool) == 2
        assert all(s.id in [1, 3] for s in swapper.available_pool)

    def test_load_nonexistent_state_resets(self, swapper):
        """Test that loading nonexistent state file resets pool."""
        swapper.select_song(1)  # Reduce pool
        assert len(swapper.available_pool) == 2

        swapper.load_state("/nonexistent/state.json")

        # Should reset to full library
        assert len(swapper.available_pool) == 3

    def test_save_and_load_round_trip(self, swapper, tmp_path):
        """Test save/load round trip preserves state."""
        # Select songs
        swapper.select_song(1)
        original_count = len(swapper.available_pool)

        # Save state
        state_file = tmp_path / "state.json"
        swapper.save_state(str(state_file))

        # Create new swapper and load state
        new_swapper = MusicSwapper(music_library=swapper.library)
        new_swapper.load_state(str(state_file))

        assert len(new_swapper.available_pool) == original_count


class TestMusicSelection:
    """Test music selection behavior and edge cases."""

    def test_selecting_all_songs_in_sequence(self, sample_music_library):
        """Test selecting all songs exhausts and resets pool."""
        songs = [Song(**data) for data in sample_music_library]
        swapper = MusicSwapper(music_library=songs)

        # Select all 3 songs
        song1 = swapper.select_song(1)
        song2 = swapper.select_song(2)
        song3 = swapper.select_song(3)

        assert song1 is not None
        assert song2 is not None
        assert song3 is not None

        # Pool should be reset after exhaustion
        assert len(swapper.available_pool) == 3

    def test_cannot_select_same_song_twice_without_reset(self, sample_music_library):
        """Test that same song can't be selected twice without reset."""
        songs = [Song(**data) for data in sample_music_library]
        swapper = MusicSwapper(music_library=songs)

        song1 = swapper.select_song(1)
        song2 = swapper.select_song(1)  # Try to select again

        assert song1 is not None
        assert song2 is None  # Should be None (not in pool anymore)

    def test_filtering_preserves_pool_state(self, sample_music_library):
        """Test that filtering doesn't modify the pool."""
        songs = [Song(**data) for data in sample_music_library]
        swapper = MusicSwapper(music_library=songs)

        # Filter songs
        high_energy = swapper.get_songs_by_energy('high')

        # Pool should remain unchanged
        assert len(swapper.available_pool) == 3
        assert len(high_energy) == 1


@pytest.mark.parametrize("energy,expected_count", [
    ("high", 1),
    ("low", 1),
    ("medium", 1),
])
def test_energy_filtering(sample_music_library, energy, expected_count):
    """Test energy filtering with different levels."""
    songs = [Song(**data) for data in sample_music_library]
    swapper = MusicSwapper(music_library=songs)

    filtered = swapper.get_songs_by_energy(energy)

    assert len(filtered) == expected_count
    assert all(s.energy == energy for s in filtered)


@pytest.mark.parametrize("min_bpm,max_bpm,expected_count", [
    (0, 90, 1),      # Low BPM
    (100, 120, 1),   # Medium BPM
    (130, 150, 1),   # High BPM
    (0, 200, 3),     # All songs
])
def test_bpm_range_filtering(sample_music_library, min_bpm, max_bpm, expected_count):
    """Test BPM range filtering."""
    songs = [Song(**data) for data in sample_music_library]
    swapper = MusicSwapper(music_library=songs)

    filtered = swapper.get_songs_by_bpm_range(min_bpm, max_bpm)

    assert len(filtered) == expected_count
    assert all(min_bpm <= s.bpm <= max_bpm for s in filtered)
