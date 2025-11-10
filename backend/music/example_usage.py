#!/usr/bin/env python3
"""
Example usage of the SupoClip Music Library System.

This demonstrates how to integrate music selection into your video processing workflow.
"""

import sys
sys.path.insert(0, '../src')

from music import MusicSwapper, Song, add_music_to_video


def main():
    """Demonstrate music system features."""

    # Initialize the music swapper
    print("=== Music Library System Demo ===\n")
    swapper = MusicSwapper()

    print(f"Loaded {len(swapper.library)} songs total")
    print(f"Available in pool: {len(swapper.available_pool)}")

    # 1. Get all available songs
    print("\n--- All Available Songs ---")
    available = swapper.get_available_songs()
    for song in available[:5]:  # Show first 5
        print(f"  [{song['id']}] {song['filename']} - {song['vibe']} ({song['energy']}, {song['bpm']} BPM)")
    print(f"  ... and {len(available) - 5} more\n")

    # 2. Filter by energy level
    print("--- High Energy Songs ---")
    high_energy = swapper.get_songs_by_energy("high")
    print(f"Found {len(high_energy)} high energy tracks:")
    for song in high_energy[:3]:
        print(f"  - {song.filename}: {song.context}")

    print("\n--- Low Energy Songs ---")
    low_energy = swapper.get_songs_by_energy("low")
    print(f"Found {len(low_energy)} low energy tracks:")
    for song in low_energy[:3]:
        print(f"  - {song.filename}: {song.context}")

    # 3. Filter by BPM range
    print("\n--- Dance-Friendly BPM (120-140) ---")
    dance_tracks = swapper.get_songs_by_bpm_range(120, 140)
    print(f"Found {len(dance_tracks)} tracks in dance BPM range:")
    for song in dance_tracks[:3]:
        print(f"  - {song.filename}: {song.bpm} BPM - {song.vibe}")

    # 4. Select specific song
    print("\n--- Selecting Specific Song ---")
    selected = swapper.select_song(song_id=1)
    if selected:
        print(f"Selected: {selected.filename}")
        print(f"  Vibe: {selected.vibe}")
        print(f"  Context: {selected.context}")
        print(f"  Energy: {selected.energy}")
        print(f"  BPM: {selected.bpm}")
        print(f"  Path: {selected.path}")
        print(f"\nRemaining songs in pool: {len(swapper.available_pool)}")

    # 5. Select random song
    print("\n--- Random Selection ---")
    random_song = swapper.select_random_song()
    print(f"Randomly selected: {random_song.filename}")
    print(f"Remaining songs in pool: {len(swapper.available_pool)}")

    # 6. Demonstrate pool exhaustion and reset
    print("\n--- Pool Management ---")
    print(f"Selecting {len(swapper.available_pool)} more songs to exhaust pool...")

    count = len(swapper.available_pool)
    for i in range(count):
        song = swapper.select_random_song()
        if i == count - 1:  # Last one
            print(f"  Selected last song: {song.filename}")

    print(f"Pool after exhaustion: {len(swapper.available_pool)} songs (auto-reset)")

    # 7. Save and load state
    print("\n--- State Persistence ---")
    state_file = "/tmp/music_swapper_state.json"
    swapper.save_state(state_file)
    print(f"Saved state to {state_file}")

    # Modify pool
    swapper.select_song(1)
    swapper.select_song(2)
    print(f"After selecting 2 songs: {len(swapper.available_pool)} available")

    # Restore previous state
    swapper.load_state(state_file)
    print(f"After loading state: {len(swapper.available_pool)} available")

    # 8. Demonstrate adding music to video
    print("\n--- Adding Music to Video ---")
    print("Example code:")
    print("""
    # Add background music to a video clip
    success = add_music_to_video(
        video_path="/tmp/clips/my_clip.mp4",
        music_path=selected.path,
        output_path="/tmp/clips/my_clip_with_music.mp4",
        music_volume=0.3  # 30% volume
    )

    if success:
        print("Music added successfully!")
    """)

    # 9. Show categorization
    print("\n--- Song Categories ---")
    categories = {
        "Energetic": [s for s in swapper.library if "energetic" in s.filename],
        "Chill": [s for s in swapper.library if "chill" in s.filename],
        "Cinematic": [s for s in swapper.library if "cinematic" in s.filename],
        "Trap": [s for s in swapper.library if "trap" in s.filename],
        "Ambient": [s for s in swapper.library if "ambient" in s.filename],
    }

    for category, songs in categories.items():
        print(f"{category}: {len(songs)} songs")
        energy_dist = {}
        for song in songs:
            energy_dist[song.energy] = energy_dist.get(song.energy, 0) + 1
        print(f"  Energy distribution: {energy_dist}")
        bpm_range = (min(s.bpm for s in songs), max(s.bpm for s in songs))
        print(f"  BPM range: {bpm_range[0]}-{bpm_range[1]}")

    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()
