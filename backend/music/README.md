# Music Library System

The SupoClip music system provides intelligent background music selection for generated video clips. This directory contains the music library manifest and will hold the actual audio files.

## Directory Structure

```
backend/music/
├── README.md          # This file
├── songs.json         # Music library manifest (40 songs)
└── [music files]      # Add your .mp3 files here
```

## Quick Start: Adding Music Files

### Step 1: Obtain Music Files

You need 40 royalty-free music tracks. Recommended sources:

- **Epidemic Sound** - Premium subscription service
- **Artlist** - High-quality royalty-free music
- **AudioJungle** - Purchase individual tracks
- **Pixabay Music** - Free royalty-free music
- **YouTube Audio Library** - Free music for creators
- **FreeMusicArchive** - Creative Commons music
- **Incompetech** - Free music by Kevin MacLeod

**IMPORTANT:** Ensure you have proper licensing for commercial use if running a hosted version.

### Step 2: Name Your Files

Music files must match the filenames in `songs.json`. The manifest includes 5 categories:

**Category Breakdown:**
- **Energetic** (10 songs): `energetic_01.mp3` through `energetic_10.mp3`
  - High energy, 135-160 BPM
  - Use for: Action, workouts, hype moments, fast content

- **Chill** (10 songs): `chill_01.mp3` through `chill_10.mp3`
  - Low energy, 65-88 BPM
  - Use for: Talking head, explanations, vlogs, tutorials

- **Cinematic** (10 songs): `cinematic_01.mp3` through `cinematic_10.mp3`
  - Medium-high energy, 85-125 BPM
  - Use for: Achievements, storytelling, emotional moments

- **Trap** (5 songs): `trap_01.mp3` through `trap_05.mp3`
  - High energy, 135-155 BPM
  - Use for: Trends, challenges, street culture, flex content

- **Ambient** (5 songs): `ambient_01.mp3` through `ambient_05.mp3`
  - Low energy, 50-68 BPM
  - Use for: Meditation, artistic content, mystery, deep thoughts

### Step 3: Copy Files to Directory

```bash
# From your local machine
cd /path/to/your/music/collection

# Copy files to backend/music/
cp energetic_01.mp3 energetic_02.mp3 ... /home/user/supoclip/backend/music/
cp chill_01.mp3 chill_02.mp3 ... /home/user/supoclip/backend/music/
cp cinematic_01.mp3 cinematic_02.mp3 ... /home/user/supoclip/backend/music/
cp trap_01.mp3 trap_02.mp3 ... /home/user/supoclip/backend/music/
cp ambient_01.mp3 ambient_02.mp3 ... /home/user/supoclip/backend/music/
```

### Step 4: Update Docker Volume (if using Docker)

The Docker container maps `/app/music/` to `backend/music/`. If you're running via Docker Compose, ensure your `docker-compose.yml` includes:

```yaml
backend:
  volumes:
    - ./backend/music:/app/music
```

Then restart:

```bash
docker-compose down
docker-compose up -d
```

### Step 5: Verify Setup

```bash
# Check files are present
ls -lh /home/user/supoclip/backend/music/*.mp3

# Should show 40 MP3 files
```

## Customizing the Music Library

### Editing songs.json

The manifest file structure:

```json
{
  "version": "1.0",
  "last_updated": "2025-11-10",
  "songs": [
    {
      "id": 1,
      "filename": "energetic_01.mp3",
      "path": "/app/music/energetic_01.mp3",
      "vibe": "Energetic and motivating",
      "context": "Action sequences, workout content, high-energy moments",
      "energy": "high",
      "bpm": 140,
      "color": "#FF6B6B"
    }
  ]
}
```

**Field Descriptions:**

- `id` - Unique integer identifier (1-40)
- `filename` - Actual filename in backend/music/
- `path` - Docker container path (always `/app/music/{filename}`)
- `vibe` - Short description of the music feel
- `context` - When to use this track (shown in UI)
- `energy` - `"low"`, `"medium"`, or `"high"`
- `bpm` - Beats per minute (50-160 range)
- `color` - Hex color for UI visualization

### Adding Custom Songs

To replace a song:

1. Edit `songs.json` and update the entry
2. Add the new MP3 file with the specified filename
3. Restart backend: `docker-compose restart backend`

Example:

```json
{
  "id": 1,
  "filename": "my_custom_track.mp3",
  "path": "/app/music/my_custom_track.mp3",
  "vibe": "Funky and groovy",
  "context": "Dance videos, parties, celebrations",
  "energy": "high",
  "bpm": 125,
  "color": "#9B59B6"
}
```

### Expanding Beyond 40 Songs

To add more songs:

1. Add new entries to `songs.json` with unique IDs (41, 42, ...)
2. Add the corresponding MP3 files
3. The system automatically loads all songs from the manifest

No code changes needed!

## How the Music System Works

### Selection Process

1. **Initialization**: MusicSwapper loads all 40 songs from `songs.json`
2. **Available Pool**: Maintains a pool of unused songs
3. **Selection**: User or system selects a song by ID
4. **Removal**: Selected song is removed from available pool
5. **Auto-Reset**: When pool is exhausted, all 40 songs become available again

### API Integration

The music system is accessed via:

```python
from src.music.swapper import MusicSwapper, add_music_to_video

# Initialize
swapper = MusicSwapper()

# Get available songs
available = swapper.get_available_songs()

# Select by ID
song = swapper.select_song(song_id=15)

# Select random
song = swapper.select_random_song()

# Filter by energy
high_energy = swapper.get_songs_by_energy("high")

# Filter by BPM range
dance_tracks = swapper.get_songs_by_bpm_range(120, 140)

# Add music to video
add_music_to_video(
    video_path="clip.mp4",
    music_path=song.path,
    output_path="clip_with_music.mp4",
    music_volume=0.3
)
```

### State Persistence

Music selection state can be saved/loaded:

```python
# Save current pool state
swapper.save_state("/tmp/music_state.json")

# Load previous state
swapper.load_state("/tmp/music_state.json")
```

This prevents song repetition across sessions.

## Audio Format Requirements

### Recommended Specifications

- **Format**: MP3 (preferred) or AAC
- **Bitrate**: 192 kbps or higher
- **Sample Rate**: 44.1 kHz or 48 kHz
- **Channels**: Stereo
- **Duration**: 2-5 minutes minimum (loops if needed)

### Converting Files

If you have files in other formats:

```bash
# Convert WAV to MP3
ffmpeg -i input.wav -b:a 192k -ar 44100 output.mp3

# Convert M4A to MP3
ffmpeg -i input.m4a -b:a 192k -ar 44100 output.mp3

# Batch convert
for f in *.wav; do ffmpeg -i "$f" -b:a 192k "${f%.wav}.mp3"; done
```

### Normalizing Audio Levels

To ensure consistent volume across all tracks:

```bash
# Normalize to -16 LUFS (standard for social media)
ffmpeg -i input.mp3 -af loudnorm=I=-16:TP=-1.5:LRA=11 output.mp3
```

## Troubleshooting

### Issue: "Music library JSON not found"

**Solution**: Ensure `backend/music/songs.json` exists. Check path in logs.

### Issue: "No such file: /app/music/energetic_01.mp3"

**Solutions**:
1. Verify MP3 file exists in `backend/music/`
2. Check filename matches exactly (case-sensitive)
3. Restart Docker container if using Docker
4. Verify volume mount in docker-compose.yml

### Issue: No audio in output video

**Solutions**:
1. Check music file is valid: `ffmpeg -i energetic_01.mp3`
2. Verify music volume isn't set to 0
3. Check FFmpeg logs for audio mixing errors
4. Ensure input video has audio track

### Issue: Music cuts off too early

**Solution**: Music loops automatically based on video duration. Use longer tracks (3-5 min) for better loops.

## Color Coding Reference

The `color` field provides visual categorization in the UI:

- **Red (#FF6B6B)**: High energy, intense
- **Teal (#4ECDC4)**: Chill, relaxed
- **Yellow (#FFD93D)**: Cinematic, dramatic
- **Pink (#F38181)**: Trap, urban
- **Purple (#AA96DA)**: Ambient, atmospheric

These colors help users quickly identify music moods when selecting tracks.

## License Compliance

### For Self-Hosted Users

You are responsible for obtaining proper music licenses. Options:

1. **Subscription Services**: Epidemic Sound, Artlist (unlimited use)
2. **Per-Track Licensing**: AudioJungle, PremiumBeat
3. **Creative Commons**: Ensure attribution if required
4. **Public Domain**: 100% free, no restrictions

### For Commercial Use

If running a hosted SupoClip service:

- Get commercial licenses for all tracks
- Consider Music Licensing Agreements (Synchronization Rights)
- Keep license documentation
- Attribute artists if required by license

**Disclaimer**: SupoClip does not provide music files. Users must source and license music independently.

## Best Practices

### Curating Your Library

1. **Variety**: Mix different styles within each category
2. **Quality**: Use high-quality recordings (avoid compression artifacts)
3. **Loopability**: Choose tracks that loop seamlessly
4. **Relevance**: Match songs to your typical content genres
5. **Testing**: Preview each track with real clips before deploying

### Naming Convention

Stick to the established pattern:
- `{category}_{number}.mp3`
- Zero-padded numbers (01, 02, etc.)
- Lowercase filenames
- No spaces or special characters

### BPM Guidelines

- **Slow**: 50-80 BPM (meditation, serious topics)
- **Medium**: 80-110 BPM (talking, explanations)
- **Upbeat**: 110-140 BPM (lifestyle, moderate energy)
- **Fast**: 140-160 BPM (action, sports, hype)

## Future Enhancements

Planned features:

- AI-based automatic song selection based on clip content
- Genre tags (electronic, hip-hop, rock, classical)
- Mood analysis (happy, sad, tense, peaceful)
- Seasonal themes (summer, winter, holiday)
- User-uploaded custom libraries per account
- Real-time audio ducking (lower music during speech)

## Support

For questions or issues:

1. Check the troubleshooting section above
2. Review backend logs: `docker-compose logs backend`
3. Open GitHub issue with details
4. Include: OS, Docker version, error messages

---

**Last Updated**: November 10, 2025
**Version**: 1.0
