# Folder Organization System Architecture

## System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                         SupoClip Backend                                │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                     Matrix Processing Pipeline                          │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │  1. Video Download & Transcription                        │          │
│  │     • YouTube URL → yt-dlp download                       │          │
│  │     • MLX Whisper → word-level timing                     │          │
│  └───────────────────────┬──────────────────────────────────┘          │
│                          │                                               │
│  ┌──────────────────────▼──────────────────────────────────┐          │
│  │  2. AI Council Deliberation                              │          │
│  │     • 5 models analyze transcript                        │          │
│  │     • Select 3-7 base clips                              │          │
│  │     • Consensus-based selection                          │          │
│  └───────────────────────┬──────────────────────────────────┘          │
│                          │                                               │
│  ┌──────────────────────▼──────────────────────────────────┐          │
│  │  3. Matrix Variation Generation                          │          │
│  │     • 3 temporal variations (base, +4s, +35s)            │          │
│  │     • 3 canvas styles (original, flipped, blurry_bg)     │          │
│  │     • Apply watermarks, titles, music, captions          │          │
│  │     • Generate 9 variations per base clip                │          │
│  └───────────────────────┬──────────────────────────────────┘          │
│                          │                                               │
│  ┌──────────────────────▼──────────────────────────────────┐          │
│  │  4. Folder Organization (NEW)                            │          │
│  │     • Extract channel from video metadata                │          │
│  │     • Create dated folder structure                      │          │
│  │     • Move clips to organized locations                  │          │
│  │     • Generate manifest.json                             │          │
│  └──────────────────────────────────────────────────────────┘          │
│                                                                          │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                   Folder Organization Components                        │
└────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐         ┌──────────────────────────┐
│   FolderOrganizer       │         │  Video Metadata          │
│   (Core Class)          │◄────────│  (YouTube Info)          │
│                         │         │                          │
│  • Channel extraction   │         │  • uploader              │
│  • Name sanitization    │         │  • title                 │
│  • Folder creation      │         │  • url                   │
│  • Manifest generation  │         │  • duration              │
│  • Cleanup management   │         └──────────────────────────┘
└────────┬────────────────┘
         │
         ├─────────────────────────────────────────────────────┐
         │                                                       │
         ▼                                                       ▼
┌────────────────────────┐                        ┌─────────────────────┐
│  Channel Name          │                        │  Dated Folders      │
│  Sanitization          │                        │  Creation           │
│                        │                        │                     │
│  Input:                │                        │  Structure:         │
│  "Joe Rogan"           │                        │  /clips/            │
│                        │                        │    joe_rogan/       │
│  Output:               │                        │      2025-11-10/    │
│  "joe_rogan_experience"│                        │        manifest.json│
└────────────────────────┘                        │        clips...     │
                                                   └─────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                        Integration Points                               │
└────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│  Matrix Worker       │
│  Integration         │
│                      │
│  Original:           │
│  process_clip_matrix()│
│                      │
│  Enhanced:           │
│  process_clip_       │
│  matrix_with_        │
│  organization()      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐         ┌─────────────────────────┐
│  Automatic           │         │  Manual Organization    │
│  Organization        │         │  (Existing Clips)       │
│                      │         │                         │
│  • During processing │         │  organize_task_clips()  │
│  • Metadata-driven   │         │                         │
│  • Zero manual work  │         │  • CLI tool             │
└──────────────────────┘         │  • API endpoint         │
                                  └─────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                         Data Flow                                       │
└────────────────────────────────────────────────────────────────────────┘

YouTube URL
    │
    ▼
┌─────────────────┐
│ get_youtube_    │────► Video Metadata
│ video_info()    │        • uploader: "Joe Rogan Experience"
└─────────────────┘        • title: "Episode #2000"
    │                      • url: "https://youtube.com/..."
    │
    ▼
┌─────────────────┐
│ Create Source   │────► Database
│                 │        sources table:
│ source.         │        • id: "src-123"
│ channel_name    │        • channel_name: "Joe Rogan Experience"
└─────────────────┘        • url: "https://..."
    │
    │
    ▼
┌─────────────────┐
│ Matrix          │────► Clip Files
│ Processing      │        /temp/matrix/task-456/
└─────────────────┘        • clip_0000_base_original.mp4
    │                      • clip_0001_plus4s_flipped.mp4
    │                      • ...
    ▼
┌─────────────────┐
│ Folder          │────► Organized Structure
│ Organization    │        /clips/
└─────────────────┘        └── joe_rogan_experience/
    │                           └── 2025-11-10/
    │                               ├── manifest.json
    │                               ├── clip_0000_base_original.mp4
    │                               └── ...
    ▼
┌─────────────────┐
│ Manifest        │────► metadata.json
│ Generation      │        {
└─────────────────┘          "channel_name": "joe_rogan_experience",
                             "date": "2025-11-10",
                             "total_clips": 9,
                             "clips": [...]
                           }

┌────────────────────────────────────────────────────────────────────────┐
│                      API Architecture                                   │
└────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  /api/folders/statistics                             │   │
│  │  GET  → FolderOrganizer.get_folder_statistics()     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  /api/folders/list                                   │   │
│  │  GET  → FolderOrganizer.list_folders()              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  /api/folders/cleanup                                │   │
│  │  POST → FolderOrganizer.cleanup_old_folders()       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  /api/folders/organize                               │   │
│  │  POST → organize_task_clips()                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                    Database Schema                                      │
└────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│  sources                                                       │
├───────────────────────────────────────────────────────────────┤
│  id              VARCHAR(36)   PRIMARY KEY                    │
│  type            VARCHAR(20)   NOT NULL                       │
│  title           VARCHAR(500)  NOT NULL                       │
│  url             VARCHAR(1000) (NEW)                          │
│  channel_name    VARCHAR(255)  (NEW) ◄── Used for organization│
│  created_at      TIMESTAMP                                     │
│  updated_at      TIMESTAMP                                     │
└───────────────────────────────────────────────────────────────┘
                    │
                    │ FK source_id
                    │
                    ▼
┌───────────────────────────────────────────────────────────────┐
│  tasks                                                         │
├───────────────────────────────────────────────────────────────┤
│  id              VARCHAR(36)   PRIMARY KEY                    │
│  user_id         VARCHAR(36)   FK → users                     │
│  source_id       VARCHAR(36)   FK → sources                   │
│  status          VARCHAR(20)                                   │
│  ...                                                           │
└───────────────────────────────────────────────────────────────┘
                    │
                    │ FK task_id
                    │
                    ▼
┌───────────────────────────────────────────────────────────────┐
│  generated_clips                                               │
├───────────────────────────────────────────────────────────────┤
│  id              VARCHAR(36)   PRIMARY KEY                    │
│  task_id         VARCHAR(36)   FK → tasks                     │
│  filename        VARCHAR(255)                                  │
│  file_path       VARCHAR(500)  ◄── Organized path             │
│  ...                                                           │
└───────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                    File System Layout                                   │
└────────────────────────────────────────────────────────────────────────┘

/clips/                                    (TEMP_DIR/clips/)
│
├── joe_rogan_experience/                  (channel folder)
│   │
│   ├── 2025-11-10/                        (dated folder)
│   │   ├── manifest.json                  (metadata)
│   │   ├── 0000_base_original_hook.mp4    (variation 1)
│   │   ├── 0000_base_flipped_hook.mp4     (variation 2)
│   │   ├── 0000_base_blurry_bg_hook.mp4   (variation 3)
│   │   ├── 0000_plus4s_original_hook.mp4  (variation 4)
│   │   ├── ...                             (9 total per clip)
│   │   └── 0001_base_original_story.mp4
│   │
│   ├── 2025-11-09/
│   │   └── ...
│   │
│   └── 2025-11-08/
│       └── ...
│
├── lex_fridman_podcast/
│   └── ...
│
└── unknown_channel/                       (fallback for no metadata)
    └── ...

┌────────────────────────────────────────────────────────────────────────┐
│                    Manifest Format                                      │
└────────────────────────────────────────────────────────────────────────┘

manifest.json (per dated folder):
{
  "version": "1.0",
  "channel_name": "joe_rogan_experience",
  "folder": "/clips/joe_rogan_experience/2025-11-10",
  "created_at": "2025-11-10T14:30:00",
  "updated_at": "2025-11-10T15:45:00",
  "total_clips": 9,

  "clips": [
    {
      "original_path": "/temp/matrix/task-123/clip_0000.mp4",
      "new_path": "/clips/joe_rogan_experience/2025-11-10/clip_0000.mp4",
      "filename": "clip_0000_base_original.mp4",
      "channel_name": "joe_rogan_experience",
      "date": "2025-11-10",

      "metadata": {
        "clip_index": 0,
        "base_title": "Hook about AI",
        "temporal_type": "base",
        "canvas_style": "original",
        "duration": 30.5,
        "start_time": 120.0,
        "end_time": 150.5,
        "engagement_score": 0.85,
        "category": "hook"
      }
    },
    ...
  ],

  "task_metadata": {
    "task_id": "task-123",
    "user_id": "user-456",
    "video_path": "/temp/video.mp4",
    "base_clips_count": 5
  }
}

┌────────────────────────────────────────────────────────────────────────┐
│                    Background Tasks                                     │
└────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  ARQ Worker (Background Jobs)                                │
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Scheduled: Daily at 2 AM                          │     │
│  │  Task: cleanup_old_clip_folders()                  │     │
│  │                                                     │     │
│  │  1. Calculate cutoff date (now - retention_days)   │     │
│  │  2. Scan all channel folders                       │     │
│  │  3. Delete folders older than cutoff               │     │
│  │  4. Log results                                    │     │
│  └────────────────────────────────────────────────────┘     │
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │  On-Demand: Via API or CLI                         │     │
│  │  Task: get_folder_statistics()                     │     │
│  │                                                     │     │
│  │  Returns:                                          │     │
│  │  • Total channels                                  │     │
│  │  • Total folders                                   │     │
│  │  • Total clips                                     │     │
│  │  • Per-channel breakdown                           │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                    CLI Tool Structure                                   │
└────────────────────────────────────────────────────────────────────────┘

folder_organizer_cli.py
│
├── stats              → Show folder statistics
├── list               → List organized folders
│   ├── --channel      → Filter by channel
│   ├── --from-date    → Date range start
│   ├── --to-date      → Date range end
│   └── --limit        → Max results
│
├── cleanup            → Cleanup old folders
│   ├── --retention-days → Retention period
│   └── --dry-run      → Simulate only
│
├── organize-task      → Organize existing task
│   ├── task_id        → Required task ID
│   └── --channel      → Override channel
│
├── channels           → List all channels
│
└── manifest           → Show folder manifest
    ├── channel_name   → Required channel
    ├── date           → Required date (YYYY-MM-DD)
    └── --verbose      → Show clip details

┌────────────────────────────────────────────────────────────────────────┐
│                    Processing Flow Example                              │
└────────────────────────────────────────────────────────────────────────┘

USER: Upload YouTube URL
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ 1. Download & Extract Metadata                          │
│    • yt-dlp downloads video                             │
│    • Extract: uploader = "Joe Rogan Experience"         │
│    • Store in sources.channel_name                      │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Transcribe & Analyze                                 │
│    • MLX Whisper → word-level timing                    │
│    • AI Council → select clips                          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Generate Matrix Variations                           │
│    • Create 9 variations per base clip                  │
│    • Apply effects (watermarks, music, etc.)            │
│    • Save to /temp/matrix/task-123/                     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Organize Clips (AUTOMATIC)                           │
│    • Extract channel: "joe_rogan_experience"            │
│    • Create folder: /clips/joe_rogan_experience/2025-11-10/│
│    • Move clips to organized location                   │
│    • Generate manifest.json                             │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 5. User Can Access Organized Clips                      │
│    • Browse by channel                                  │
│    • Browse by date                                     │
│    • View manifest metadata                             │
└─────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                    Cleanup Flow                                         │
└────────────────────────────────────────────────────────────────────────┘

SCHEDULED: Daily at 2 AM
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Calculate Cutoff Date                                   │
│ • Now: 2025-11-10                                       │
│ • Retention: 30 days                                    │
│ • Cutoff: 2025-10-11                                    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Scan All Folders                                        │
│ • /clips/joe_rogan_experience/2025-10-05 (DELETE)      │
│ • /clips/joe_rogan_experience/2025-11-01 (KEEP)        │
│ • /clips/lex_fridman/2025-10-08 (DELETE)               │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Delete Old Folders                                      │
│ • shutil.rmtree() each old folder                       │
│ • Log deletion                                          │
│ • Track results                                         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Report Results                                          │
│ • Deleted: 5 folders                                    │
│ • Kept: 42 folders                                      │
│ • Errors: 0                                             │
└─────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                    Error Handling                                       │
└────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Scenario: Channel Name Extraction Fails                │
│                                                         │
│ Input: video_metadata = None                           │
│ Result: channel_name = "unknown_channel"               │
│                                                         │
│ Impact: Clips still organized, just in fallback folder │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Scenario: File Move Fails                              │
│                                                         │
│ Try: shutil.move()                                      │
│ Fallback: shutil.copy2()                                │
│ Log: Warning about copy instead of move                │
│                                                         │
│ Impact: Clip still organized, may use more disk space  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Scenario: Organization Fails Completely                │
│                                                         │
│ • Matrix processing completes successfully             │
│ • Organization error caught and logged                 │
│ • Clips remain in /temp/matrix/ location               │
│ • Task marked as completed with warning                │
│                                                         │
│ Impact: Clips available but not organized              │
│ Recovery: Use CLI to manually organize later           │
└─────────────────────────────────────────────────────────┘

This architecture provides a robust, scalable solution for organizing
SupoClip clips with minimal manual intervention while maintaining
flexibility for custom workflows.
