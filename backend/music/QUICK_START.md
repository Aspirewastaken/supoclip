# Quick Start: Adding Music to SupoClip

## 1. Download 40 Royalty-Free Music Tracks

Choose from these sources:

- **Epidemic Sound** (subscription)
- **Artlist** (subscription)
- **Pixabay Music** (free)
- **YouTube Audio Library** (free)
- **Incompetech** (free)

## 2. Rename Files to Match Manifest

You need exactly these filenames:

### Energetic (10 files) - High Energy, 135-160 BPM
```
energetic_01.mp3  energetic_02.mp3  energetic_03.mp3  energetic_04.mp3  energetic_05.mp3
energetic_06.mp3  energetic_07.mp3  energetic_08.mp3  energetic_09.mp3  energetic_10.mp3
```
**Use for**: Action, workouts, hype, fast-paced content

### Chill (10 files) - Low Energy, 65-88 BPM
```
chill_01.mp3  chill_02.mp3  chill_03.mp3  chill_04.mp3  chill_05.mp3
chill_06.mp3  chill_07.mp3  chill_08.mp3  chill_09.mp3  chill_10.mp3
```
**Use for**: Talking heads, explanations, vlogs, tutorials

### Cinematic (10 files) - Medium-High Energy, 85-125 BPM
```
cinematic_01.mp3  cinematic_02.mp3  cinematic_03.mp3  cinematic_04.mp3  cinematic_05.mp3
cinematic_06.mp3  cinematic_07.mp3  cinematic_08.mp3  cinematic_09.mp3  cinematic_10.mp3
```
**Use for**: Achievements, storytelling, emotional moments

### Trap (5 files) - High Energy, 135-155 BPM
```
trap_01.mp3  trap_02.mp3  trap_03.mp3  trap_04.mp3  trap_05.mp3
```
**Use for**: Trends, challenges, street culture

### Ambient (5 files) - Low Energy, 50-68 BPM
```
ambient_01.mp3  ambient_02.mp3  ambient_03.mp3  ambient_04.mp3  ambient_05.mp3
```
**Use for**: Meditation, artistic content, mystery

## 3. Copy Files to Directory

```bash
cd /path/to/your/downloaded/music

# Copy all files at once
cp *.mp3 /home/user/supoclip/backend/music/
```

Or individually:
```bash
cp energetic_*.mp3 /home/user/supoclip/backend/music/
cp chill_*.mp3 /home/user/supoclip/backend/music/
cp cinematic_*.mp3 /home/user/supoclip/backend/music/
cp trap_*.mp3 /home/user/supoclip/backend/music/
cp ambient_*.mp3 /home/user/supoclip/backend/music/
```

## 4. Verify Setup

```bash
# Should show 40 MP3 files + 4 other files
ls /home/user/supoclip/backend/music/ | wc -l
# Expected output: 44

# Check MP3 count
ls /home/user/supoclip/backend/music/*.mp3 | wc -l
# Expected output: 40
```

## 5. Restart Backend (if using Docker)

```bash
cd /home/user/supoclip
docker-compose restart backend

# Check logs to confirm music loaded
docker-compose logs backend | grep "Loaded.*songs"
# Expected: "Loaded 40 songs from /app/backend/music/songs.json"
```

## 6. Test in Python

```bash
cd /home/user/supoclip/backend
python3 music/example_usage.py
```

You should see:
```
Loaded 40 songs total
Available in pool: 40
```

## Done!

Your music library is ready. The system will:
- Automatically select music for clips
- Remove songs from pool after use
- Auto-reset when all 40 are used
- Filter by energy level, BPM, vibe

## Need Help?

- Full docs: `backend/music/README.md`
- Example code: `backend/music/example_usage.py`
- Manifest: `backend/music/songs.json`

## Customization

To change song metadata (vibe, context, BPM):
1. Edit `backend/music/songs.json`
2. Restart backend
3. Changes take effect immediately

## File Format Requirements

- **Format**: MP3 (preferred)
- **Bitrate**: 192 kbps or higher
- **Sample Rate**: 44.1 kHz or 48 kHz
- **Channels**: Stereo
- **Duration**: 2-5 minutes minimum

## Converting Files

If your music is in WAV or other formats:

```bash
# Single file
ffmpeg -i input.wav -b:a 192k -ar 44100 energetic_01.mp3

# Batch convert
for f in *.wav; do ffmpeg -i "$f" -b:a 192k "${f%.wav}.mp3"; done
```

---

**Next Steps**: See `README.md` for advanced usage, troubleshooting, and API integration.
