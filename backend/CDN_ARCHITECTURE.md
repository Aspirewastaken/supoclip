# SupoClip CDN Architecture

Visual guide to the CDN integration architecture.

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SupoClip CDN System                          │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   Frontend   │
│  (Next.js)   │
└──────┬───────┘
       │ POST /start (video URL)
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Backend (FastAPI)                            │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Video Processing Pipeline                                  │    │
│  │  1. Download video                                          │    │
│  │  2. Generate transcript (AssemblyAI)                        │    │
│  │  3. AI analysis (identify viral segments)                   │    │
│  │  4. Create clips with transitions                           │    │
│  └───────────────────────┬────────────────────────────────────┘    │
│                          │                                           │
│                          ▼                                           │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  CDN Integration (NEW)                                      │    │
│  │  • upload_clips_batch() - Parallel upload to CDN           │    │
│  │  • Store CDN URLs in database                               │    │
│  │  • Return CDN URLs to frontend                              │    │
│  └───────────┬────────────────────────────────────────────────┘    │
│              │                                                       │
└──────────────┼───────────────────────────────────────────────────────┘
               │
               ▼ Parallel upload (async)
┌─────────────────────────────────────────────────────────────────────┐
│                      CDN Provider Layer                              │
├─────────────────────┬─────────────────────┬─────────────────────────┤
│  AWS CloudFront     │  Cloudflare R2      │  Bunny CDN             │
│  ┌──────────────┐   │  ┌──────────────┐   │  ┌──────────────┐      │
│  │ S3 Backend   │   │  │ R2 Storage   │   │  │Bunny Storage │      │
│  │ (clips/)     │   │  │ (clips/)     │   │  │ (clips/)     │      │
│  └──────────────┘   │  └──────────────┘   │  └──────────────┘      │
│         │            │         │            │         │              │
│         ▼            │         ▼            │         ▼              │
│  ┌──────────────┐   │  ┌──────────────┐   │  ┌──────────────┐      │
│  │ CloudFront   │   │  │   R2 CDN     │   │  │  Pull Zone   │      │
│  │ Distribution │   │  │(CF Network)  │   │  │  (114 PoPs)  │      │
│  │ (400+ PoPs)  │   │  │ (250+ PoPs)  │   │  └──────────────┘      │
│  └──────────────┘   │  └──────────────┘   │                         │
└─────────────────────┴─────────────────────┴─────────────────────────┘
               │                 │                  │
               └─────────────────┼──────────────────┘
                                 │
                                 ▼
                    ┌──────────────────────┐
                    │  Global Edge Network │
                    │  • Low latency       │
                    │  • High bandwidth    │
                    │  • DDoS protection   │
                    └──────────────────────┘
                                 │
                                 ▼
                          ┌────────────┐
                          │ End Users  │
                          │ (Viewers)  │
                          └────────────┘
```

## Video Processing Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Video Processing with CDN                         │
└─────────────────────────────────────────────────────────────────────┘

1. User Submits Video
   ┌──────────┐
   │  Video   │ (YouTube URL or Upload)
   └────┬─────┘
        │
        ▼
2. AI Processing
   ┌────────────────┐
   │  Transcribe    │ AssemblyAI (word-level timing)
   └────┬───────────┘
        │
        ▼
   ┌────────────────┐
   │  AI Analysis   │ Identify viral segments (10-45s)
   └────┬───────────┘
        │
        ▼
3. Clip Generation
   ┌────────────────┐
   │ Create Clips   │ MoviePy (9:16 with subtitles)
   └────┬───────────┘
        │
        ▼
   ┌────────────────────────────────────────────┐
   │ Local Storage: /tmp/clips/                 │
   │ • clip_1_10.5_25.3.mp4                     │
   │ • clip_2_45.2_78.9.mp4                     │
   │ • clip_3_120.1_155.7.mp4                   │
   └────┬───────────────────────────────────────┘
        │
        ▼
4. CDN Upload (NEW - Parallel) ☁️
   ┌────────────────────────────────────────────┐
   │ upload_clips_batch()                       │
   │                                             │
   │ ┌─────────┐  ┌─────────┐  ┌─────────┐     │
   │ │ Clip 1  │  │ Clip 2  │  │ Clip 3  │     │
   │ └────┬────┘  └────┬────┘  └────┬────┘     │
   │      │            │            │           │
   │      └────────────┼────────────┘           │
   │                   │ (parallel uploads)     │
   └───────────────────┼────────────────────────┘
                       │
                       ▼
   ┌────────────────────────────────────────────┐
   │ CDN Provider (CloudFront/R2/Bunny)         │
   │                                             │
   │ clips/                                      │
   │ ├── task-123/                              │
   │ │   ├── clip_1_10.5_25.3.mp4              │
   │ │   ├── clip_2_45.2_78.9.mp4              │
   │ │   └── clip_3_120.1_155.7.mp4            │
   └───────────────────┬────────────────────────┘
                       │
                       ▼
5. Database Update
   ┌────────────────────────────────────────────┐
   │ PostgreSQL: generated_clips table          │
   │                                             │
   │ id | filename | file_path | cdn_url        │
   │────┼──────────┼───────────┼───────────────│
   │ 1  | clip_1..│ /tmp/...  │ https://cdn..  │
   │ 2  | clip_2..│ /tmp/...  │ https://cdn..  │
   │ 3  | clip_3..│ /tmp/...  │ https://cdn..  │
   └───────────────────┬────────────────────────┘
                       │
                       ▼
6. API Response
   ┌────────────────────────────────────────────┐
   │ {                                           │
   │   "clips": [                                │
   │     {                                       │
   │       "filename": "clip_1.mp4",            │
   │       "video_url": "https://cdn.../clip_1" │
   │     }                                       │
   │   ]                                         │
   │ }                                           │
   └────┬───────────────────────────────────────┘
        │
        ▼
   ┌──────────┐
   │ Frontend │ Plays video from CDN
   └──────────┘
```

## URL Resolution Strategy

```
┌─────────────────────────────────────────────────────────────────────┐
│                 Smart URL with Fallback Chain                        │
└─────────────────────────────────────────────────────────────────────┘

Frontend requests clip URL:
GET /tasks/task-123/clips

Backend resolves URL (priority order):

1. Database CDN URL (fastest)
   ┌──────────────────────────────────┐
   │ SELECT cdn_url FROM clips        │
   │ WHERE id = 'clip-123'            │
   └──────┬───────────────────────────┘
          │
          ├─ IF cdn_url exists:
          │  └─► Return: https://cdn.example.com/clips/task-123/clip_1.mp4
          │
          └─ IF cdn_url is NULL:
                       │
                       ▼
2. Generate CDN URL (if provider configured)
   ┌──────────────────────────────────┐
   │ provider = get_cdn_provider()    │
   │ IF provider.is_enabled():        │
   │   return provider.get_url(...)   │
   └──────┬───────────────────────────┘
          │
          ├─ IF CDN enabled:
          │  └─► Return: https://cdn.example.com/clips/task-123/clip_1.mp4
          │
          └─ IF CDN disabled:
                       │
                       ▼
3. Direct Serving (fallback)
   ┌──────────────────────────────────┐
   │ Return local file path           │
   └──────┬───────────────────────────┘
          │
          └─► Return: /clips/clip_1.mp4 (served by FastAPI)

Result: Frontend always gets a working URL!
```

## CDN Provider Architecture

### AWS CloudFront

```
┌────────────────────────────────────────────────────────────────────┐
│                      AWS CloudFront Flow                            │
└────────────────────────────────────────────────────────────────────┘

Upload:
SupoClip → boto3.s3.upload_file() → S3 Bucket → CloudFront

Request:
User → CloudFront Edge (nearest) → [Cache?]
                                      │
                        ┌─────────────┴────────────┐
                        │                          │
                   Yes (HIT)                   No (MISS)
                        │                          │
                        ▼                          ▼
                  Return cached              Fetch from S3
                                                   │
                                                   ▼
                                             Cache + Return

Features:
• 400+ edge locations
• Signed URLs (RSA private key)
• Cache invalidation (CloudFront API)
• Origin Access Control (secure S3 access)
```

### Cloudflare R2

```
┌────────────────────────────────────────────────────────────────────┐
│                     Cloudflare R2 Flow                              │
└────────────────────────────────────────────────────────────────────┘

Upload:
SupoClip → boto3 (S3-compatible) → R2 Storage → Cloudflare CDN

Request:
User → CF Edge (nearest) → [Cache?]
                              │
                ┌─────────────┴────────────┐
                │                          │
           Yes (HIT)                   No (MISS)
                │                          │
                ▼                          ▼
          Return cached              Fetch from R2
                                           │
                                           ▼
                                     Cache + Return

Features:
• 250+ edge locations (Cloudflare network)
• Zero egress fees (game-changer!)
• Presigned URLs (S3-compatible)
• Custom domain support
• Cache purge via Cloudflare API
```

### Bunny CDN

```
┌────────────────────────────────────────────────────────────────────┐
│                       Bunny CDN Flow                                │
└────────────────────────────────────────────────────────────────────┘

Upload:
SupoClip → aiohttp.put() → Bunny Storage → Pull Zone

Request:
User → Bunny Edge (nearest) → [Cache?]
                                  │
                    ┌─────────────┴────────────┐
                    │                          │
               Yes (HIT)                   No (MISS)
                    │                          │
                    ▼                          ▼
              Return cached              Fetch from Storage
                                               │
                                               ▼
                                         Cache + Return

Features:
• 114 Points of Presence
• Token authentication (SHA256)
• Pull Zone caching
• Volume zones for high traffic
• Instant cache purging
```

## Data Flow: Complete Example

```
┌─────────────────────────────────────────────────────────────────────┐
│         Example: Processing a 10-minute YouTube video               │
└─────────────────────────────────────────────────────────────────────┘

INPUT:
POST /start
{
  "source": {
    "url": "https://youtube.com/watch?v=abc123"
  }
}

PROCESSING:
[00:00:00] Download video (yt-dlp) → /tmp/abc123.mp4 (250 MB)
[00:00:30] Generate transcript (AssemblyAI) → 15,432 words
[00:01:00] AI analysis → Identify 5 viral segments
           • Segment 1: 00:15 - 00:42 (27s) - score: 95
           • Segment 2: 02:30 - 03:15 (45s) - score: 92
           • Segment 3: 05:10 - 05:38 (28s) - score: 88
           • Segment 4: 07:22 - 07:55 (33s) - score: 87
           • Segment 5: 09:01 - 09:40 (39s) - score: 85
[00:01:30] Create clips (MoviePy) → 5 clips generated
           • clip_1_15.0_42.0.mp4 (12 MB)
           • clip_2_150.0_195.0.mp4 (18 MB)
           • clip_3_310.0_338.0.mp4 (11 MB)
           • clip_4_442.0_475.0.mp4 (14 MB)
           • clip_5_541.0_580.0.mp4 (16 MB)
[00:02:00] Upload to CDN (parallel)
           Thread 1: clip_1 → CDN (3.2s) ✅
           Thread 2: clip_2 → CDN (4.1s) ✅
           Thread 3: clip_3 → CDN (2.8s) ✅
           Thread 4: clip_4 → CDN (3.5s) ✅
           Thread 5: clip_5 → CDN (3.9s) ✅
           Total CDN upload time: 4.1s (vs 17.5s sequential)
[00:02:05] Save to database → 5 records with CDN URLs

RESPONSE:
{
  "task_id": "task-123",
  "clips": [
    {
      "filename": "clip_1_15.0_42.0.mp4",
      "video_url": "https://cdn.example.com/clips/task-123/clip_1_15.0_42.0.mp4",
      "cdn_url": "https://cdn.example.com/clips/task-123/clip_1_15.0_42.0.mp4",
      "start_time": 15.0,
      "end_time": 42.0,
      "relevance_score": 95
    },
    ...
  ]
}

Total processing time: 2 minutes 5 seconds
CDN upload: 4.1 seconds (parallel) vs 17.5s (sequential) = 4.3x faster!
```

## Code Flow

```python
# Simplified code flow showing CDN integration

# 1. Video processing (existing)
clips_info = create_clips_with_transitions(...)
# Returns: [
#   {"filename": "clip_1.mp4", "path": "/tmp/clips/clip_1.mp4", ...},
#   {"filename": "clip_2.mp4", "path": "/tmp/clips/clip_2.mp4", ...}
# ]

# 2. CDN upload (NEW)
cdn_urls = await upload_clips_batch(clips_info, task_id)
# Parallel upload using asyncio.gather()
# Returns: {
#   "clip_1.mp4": "https://cdn.example.com/clips/task-123/clip_1.mp4",
#   "clip_2.mp4": "https://cdn.example.com/clips/task-123/clip_2.mp4"
# }

# 3. Save to database (updated)
for clip_info in clips_info:
    cdn_url = cdn_urls.get(clip_info["filename"])
    clip_record = GeneratedClip(
        filename=clip_info["filename"],
        file_path=clip_info["path"],
        cdn_url=cdn_url,  # NEW FIELD
        ...
    )
    db.add(clip_record)
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Signed URL Generation                            │
└─────────────────────────────────────────────────────────────────────┘

Public Access (default):
User → CDN URL → Clip (no authentication)
• Use for: Public clips, social media sharing
• URL: https://cdn.example.com/clips/task-123/clip_1.mp4

Private Access (signed URLs):
User → Request signed URL → Backend generates signed URL → User downloads
       ┌──────────────────────────────────────────────────┐
       │ Signing Algorithm (varies by provider):          │
       │                                                   │
       │ CloudFront: RSA-SHA1 signature                   │
       │   signature = sign(policy, private_key)          │
       │   url = base_url + "?Policy=...&Signature=..."   │
       │                                                   │
       │ R2: S3 presigned URL (AWS SigV4)                 │
       │   signature = hmac_sha256(secret_key, ...)       │
       │   url = base_url + "?X-Amz-Signature=..."        │
       │                                                   │
       │ Bunny: Token authentication                      │
       │   token = sha256(api_key + path + expires)       │
       │   url = base_url + "?token=...&expires=..."      │
       └──────────────────────────────────────────────────┘
                              │
                              ▼
User accesses signed URL (valid for limited time, e.g., 1 hour)
• Use for: User-specific clips, premium content, temporary access
• URL: https://cdn.example.com/clips/task-123/clip_1.mp4?signature=...&expires=...

After expiration:
CDN returns 403 Forbidden → User must request new signed URL
```

## Monitoring & Observability

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Logging & Metrics                              │
└─────────────────────────────────────────────────────────────────────┘

Application Logs:
☁️  CDN operations (upload, delete, purge)
📤 Upload started
✅ Success
❌ Error
⚠️ Warning

Example:
2025-11-10 12:34:56 - INFO - ☁️ Uploading clips to CDN (if configured)
2025-11-10 12:34:57 - INFO - 📤 Uploading clip to CDN: clip_1.mp4
2025-11-10 12:34:58 - INFO - ✅ Clip uploaded to CDN: https://...
2025-11-10 12:34:59 - INFO - ✅ CDN upload complete - 5 clips uploaded

Database Metrics:
• Total clips: SELECT COUNT(*) FROM generated_clips
• CDN clips: SELECT COUNT(*) FROM generated_clips WHERE cdn_url IS NOT NULL
• Local clips: SELECT COUNT(*) FROM generated_clips WHERE cdn_url IS NULL
• Upload rate: (CDN clips / Total clips) * 100

CDN Provider Metrics (via provider dashboard):
• Bandwidth usage
• Request count
• Cache hit ratio
• Edge location performance
• Cost tracking
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Production Deployment                              │
└─────────────────────────────────────────────────────────────────────┘

Development:
┌──────────────┐
│   Local      │
│   FastAPI    │ → CDN disabled (CDN_ENABLED=false)
│   (Port 8000)│ → Direct serving: /clips/
└──────────────┘

Staging:
┌──────────────┐     ┌──────────────┐
│   FastAPI    │ →→→ │  Bunny CDN   │ (test account)
│   (Docker)   │     │  Storage     │
└──────────────┘     └──────────────┘
      ↓
┌──────────────┐
│  PostgreSQL  │ (cdn_url column)
└──────────────┘

Production:
                      ┌──────────────────┐
                      │  Load Balancer   │
                      └────────┬─────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌──────────┐     ┌──────────┐    ┌──────────┐
        │ FastAPI  │     │ FastAPI  │    │ FastAPI  │
        │ Instance │     │ Instance │    │ Instance │
        └────┬─────┘     └────┬─────┘    └────┬─────┘
             │                │               │
             └────────────────┼───────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   PostgreSQL     │
                    │   (Primary)      │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Cloudflare R2   │ (production CDN)
                    │  • Zero egress   │
                    │  • Global CDN    │
                    └──────────────────┘
```

---

**See Also**:
- Setup Guide: `/backend/CDN_SETUP_GUIDE.md`
- Code: `/backend/src/storage/cdn.py`
- Summary: `/CDN_INTEGRATION_SUMMARY.md`
