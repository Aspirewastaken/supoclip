"""
Tests for folder organization system.

Run with:
    pytest tests/test_folder_organizer.py -v
"""
import pytest
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil

from src.utils.folder_organizer import FolderOrganizer, organize_matrix_clips


@pytest.fixture
def temp_clips_dir():
    """Create temporary clips directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def organizer(temp_clips_dir):
    """Create FolderOrganizer instance with temp directory."""
    return FolderOrganizer(base_clips_dir=temp_clips_dir, retention_days=30)


@pytest.fixture
def sample_clip_file(temp_clips_dir):
    """Create a sample clip file."""
    clip_path = Path(temp_clips_dir) / "sample_clip.mp4"
    clip_path.write_text("fake video data")
    return str(clip_path)


class TestChannelNameSanitization:
    """Test channel name sanitization."""

    def test_sanitize_normal_name(self, organizer):
        result = organizer.sanitize_channel_name("Joe Rogan Experience")
        assert result == "joe_rogan_experience"

    def test_sanitize_special_characters(self, organizer):
        result = organizer.sanitize_channel_name("Channel: Name/With\\Special*Chars")
        assert result == "channel_namewithspecialchars"

    def test_sanitize_multiple_spaces(self, organizer):
        result = organizer.sanitize_channel_name("My    Channel   Name")
        assert result == "my_channel_name"

    def test_sanitize_empty_name(self, organizer):
        result = organizer.sanitize_channel_name("")
        assert result == "unknown_channel"

    def test_sanitize_long_name(self, organizer):
        long_name = "A" * 200
        result = organizer.sanitize_channel_name(long_name)
        assert len(result) <= 100


class TestChannelExtraction:
    """Test channel name extraction from metadata."""

    def test_extract_from_uploader(self, organizer):
        metadata = {'uploader': 'Joe Rogan Experience'}
        result = organizer.get_channel_name_from_metadata(video_metadata=metadata)
        assert result == "joe_rogan_experience"

    def test_extract_from_channel(self, organizer):
        metadata = {'channel': 'Lex Fridman'}
        result = organizer.get_channel_name_from_metadata(video_metadata=metadata)
        assert result == "lex_fridman"

    def test_user_input_priority(self, organizer):
        metadata = {'uploader': 'Original Channel'}
        result = organizer.get_channel_name_from_metadata(
            video_metadata=metadata,
            user_input='Override Channel'
        )
        assert result == "override_channel"

    def test_fallback_unknown(self, organizer):
        result = organizer.get_channel_name_from_metadata()
        assert result == "unknown_channel"


class TestFolderCreation:
    """Test dated folder creation."""

    def test_create_dated_folder(self, organizer):
        channel_name = "test_channel"
        date = datetime(2025, 11, 10)

        folder_path = organizer.create_dated_folder(channel_name, date)

        assert folder_path.exists()
        assert folder_path.is_dir()
        assert "test_channel" in str(folder_path)
        assert "2025-11-10" in str(folder_path)

    def test_get_dated_folder_path(self, organizer):
        channel_name = "test_channel"
        date = datetime(2025, 11, 10)

        folder_path = organizer.get_dated_folder_path(channel_name, date)

        assert "test_channel" in str(folder_path)
        assert "2025-11-10" in str(folder_path)

    def test_create_nested_structure(self, organizer):
        folder_path = organizer.create_dated_folder("channel1", datetime(2025, 11, 10))

        # Verify nested structure exists
        assert folder_path.parent.name == "channel1"
        assert folder_path.name == "2025-11-10"


class TestClipOrganization:
    """Test single clip organization."""

    def test_organize_single_clip(self, organizer, sample_clip_file):
        result = organizer.organize_clip(
            clip_path=sample_clip_file,
            channel_name="test_channel",
            metadata={'duration': 30.5}
        )

        assert result['success'] is True
        assert result['channel_name'] == "test_channel"
        assert Path(result['new_path']).exists()
        assert 'test_channel' in result['new_path']
        assert '2025-' in result['date']

    def test_organize_with_explicit_date(self, organizer, sample_clip_file):
        date = datetime(2025, 1, 1)

        result = organizer.organize_clip(
            clip_path=sample_clip_file,
            channel_name="test_channel",
            date=date
        )

        assert '2025-01-01' in result['new_path']

    def test_organize_duplicate_filename(self, organizer, temp_clips_dir):
        # Create two clips with same name
        clip1 = Path(temp_clips_dir) / "duplicate.mp4"
        clip2 = Path(temp_clips_dir) / "duplicate.mp4.tmp"

        clip1.write_text("clip 1 data")
        clip2.write_text("clip 2 data")

        # Organize first clip
        result1 = organizer.organize_clip(str(clip1), "test_channel")

        # Rename second clip to match first
        clip2_renamed = Path(temp_clips_dir) / "duplicate.mp4"
        clip2.rename(clip2_renamed)

        # Organize second clip (should get incremented name)
        result2 = organizer.organize_clip(str(clip2_renamed), "test_channel")

        # Check both exist and have different filenames
        assert Path(result1['new_path']).exists()
        assert Path(result2['new_path']).exists()
        assert result1['filename'] != result2['filename']


class TestBatchOrganization:
    """Test batch clip organization."""

    def test_organize_clips_batch(self, organizer, temp_clips_dir):
        # Create multiple clips
        clips = []
        for i in range(3):
            clip_path = Path(temp_clips_dir) / f"clip_{i}.mp4"
            clip_path.write_text(f"clip {i} data")
            clips.append({
                'file_path': str(clip_path),
                'duration': 30 + i
            })

        result = organizer.organize_clips_batch(
            clips=clips,
            channel_name="test_channel"
        )

        assert result['success'] is True
        assert result['organized_count'] == 3
        assert result['failed_count'] == 0
        assert len(result['organized_clips']) == 3

    def test_batch_with_failures(self, organizer):
        clips = [
            {'file_path': '/nonexistent/clip1.mp4'},
            {'file_path': '/nonexistent/clip2.mp4'},
        ]

        result = organizer.organize_clips_batch(
            clips=clips,
            channel_name="test_channel"
        )

        assert result['failed_count'] == 2
        assert result['organized_count'] == 0


class TestManifestGeneration:
    """Test manifest.json generation."""

    def test_generate_manifest(self, organizer):
        folder_path = organizer.create_dated_folder("test_channel", datetime.now())

        clips = [
            {
                'filename': 'clip1.mp4',
                'new_path': str(folder_path / 'clip1.mp4'),
                'metadata': {'duration': 30}
            }
        ]

        manifest_path = organizer.generate_manifest(
            folder_path=folder_path,
            clips=clips,
            channel_name="test_channel",
            task_metadata={'task_id': 'test-123'}
        )

        assert manifest_path.exists()

        # Read and verify manifest
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        assert manifest['version'] == '1.0'
        assert manifest['channel_name'] == 'test_channel'
        assert manifest['total_clips'] == 1
        assert len(manifest['clips']) == 1

    def test_manifest_merge(self, organizer):
        folder_path = organizer.create_dated_folder("test_channel", datetime.now())

        # Generate first manifest
        clips1 = [{'filename': 'clip1.mp4', 'new_path': str(folder_path / 'clip1.mp4')}]
        organizer.generate_manifest(folder_path, clips1, "test_channel")

        # Generate second manifest (should merge)
        clips2 = [{'filename': 'clip2.mp4', 'new_path': str(folder_path / 'clip2.mp4')}]
        manifest_path = organizer.generate_manifest(folder_path, clips2, "test_channel")

        # Read merged manifest
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        assert manifest['total_clips'] == 2
        assert 'updated_at' in manifest


class TestFolderCleanup:
    """Test old folder cleanup."""

    def test_cleanup_old_folders(self, organizer):
        # Create old folder (40 days ago)
        old_date = datetime.now() - timedelta(days=40)
        old_folder = organizer.create_dated_folder("old_channel", old_date)

        # Create new folder (10 days ago)
        new_date = datetime.now() - timedelta(days=10)
        new_folder = organizer.create_dated_folder("new_channel", new_date)

        # Run cleanup (retention: 30 days)
        result = organizer.cleanup_old_folders(dry_run=False)

        assert result['success'] is True
        assert result['deleted_count'] == 1
        assert result['kept_count'] == 1
        assert not old_folder.exists()
        assert new_folder.exists()

    def test_cleanup_dry_run(self, organizer):
        # Create old folder
        old_date = datetime.now() - timedelta(days=40)
        old_folder = organizer.create_dated_folder("old_channel", old_date)

        # Run dry run
        result = organizer.cleanup_old_folders(dry_run=True)

        assert result['dry_run'] is True
        assert result['deleted_count'] == 1
        assert old_folder.exists()  # Should still exist in dry run


class TestFolderStatistics:
    """Test folder statistics."""

    def test_get_folder_statistics(self, organizer, temp_clips_dir):
        # Create folders with clips
        channel1_folder = organizer.create_dated_folder("channel1", datetime.now())
        channel2_folder = organizer.create_dated_folder("channel2", datetime.now())

        # Create clips
        (channel1_folder / "clip1.mp4").write_text("data")
        (channel1_folder / "clip2.mp4").write_text("data")
        (channel2_folder / "clip3.mp4").write_text("data")

        stats = organizer.get_folder_statistics()

        assert stats['total_channels'] == 2
        assert stats['total_folders'] == 2
        assert stats['total_clips'] == 3
        assert 'channel1' in stats['channels']
        assert 'channel2' in stats['channels']
        assert stats['channels']['channel1']['clips'] == 2


class TestFolderListing:
    """Test folder listing."""

    def test_list_all_folders(self, organizer):
        # Create multiple folders
        organizer.create_dated_folder("channel1", datetime(2025, 11, 10))
        organizer.create_dated_folder("channel1", datetime(2025, 11, 9))
        organizer.create_dated_folder("channel2", datetime(2025, 11, 10))

        folders = organizer.list_folders()

        assert len(folders) == 3
        # Should be sorted by date descending
        assert folders[0]['date'] >= folders[1]['date']

    def test_list_by_channel(self, organizer):
        organizer.create_dated_folder("channel1", datetime(2025, 11, 10))
        organizer.create_dated_folder("channel2", datetime(2025, 11, 10))

        folders = organizer.list_folders(channel_name="channel1")

        assert len(folders) == 1
        assert folders[0]['channel'] == "channel1"

    def test_list_by_date_range(self, organizer):
        organizer.create_dated_folder("channel1", datetime(2025, 11, 1))
        organizer.create_dated_folder("channel1", datetime(2025, 11, 10))
        organizer.create_dated_folder("channel1", datetime(2025, 11, 20))

        folders = organizer.list_folders(
            date_from=datetime(2025, 11, 5),
            date_to=datetime(2025, 11, 15)
        )

        assert len(folders) == 1
        assert folders[0]['date'] == "2025-11-10"


class TestMatrixClipsIntegration:
    """Test integration with matrix processing."""

    def test_organize_matrix_clips(self, temp_clips_dir):
        # Create sample clips
        clip_files = []
        for i in range(3):
            clip_path = Path(temp_clips_dir) / f"clip_{i}.mp4"
            clip_path.write_text(f"data {i}")
            clip_files.append(str(clip_path))

        # Mock matrix result
        matrix_result = {
            'success': True,
            'variations': [
                {'file_path': clip_files[0], 'duration': 30},
                {'file_path': clip_files[1], 'duration': 35},
                {'file_path': clip_files[2], 'duration': 40},
            ]
        }

        # Mock video metadata
        video_metadata = {
            'uploader': 'Test Channel',
            'title': 'Test Video'
        }

        # Organize
        result = organize_matrix_clips(
            matrix_result=matrix_result,
            channel_name="",  # Should extract from metadata
            video_metadata=video_metadata,
            task_metadata={'task_id': 'test-123'},
            retention_days=30
        )

        assert result['success'] is True
        assert result['channel_name'] == "test_channel"
        assert result['organized_count'] == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
