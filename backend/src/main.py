from .youtube_utils import *
from .video_utils import *
from .ai import *
from .config import Config
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path
import logging
import json
import asyncio
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/backend.log')
    ]
)

logger = logging.getLogger(__name__)
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text

from .models import User, Task, Source, GeneratedClip
from .database import init_db, close_db, get_db, AsyncSessionLocal
from .storage.integrations import upload_clips_batch, get_clip_url
from .api.routes.tasks import router as tasks_router
from .api.routes.posting_helper import router as posting_router
from .api.routes.ai_titles import router as ai_titles_router
from .api.routes.watermarks import router as watermarks_router
from .api.routes.analytics import router as analytics_router
from .api.routes.calendar import router as calendar_router
from .api.routes.quota import router as quota_router
from .api.routes.billing import router as billing_router
from .api.routes.experiments import router as experiments_router
from .api.routes.thumbnails import router as thumbnails_router
from .webhooks.routes import router as webhooks_router
from .api.routes.performance import router as performance_router
from .api.routes.social_media import router as social_media_router

config = Config()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        yield
    finally:
        await close_db()

app = FastAPI(
    title="SupoClip API",
    description="""
# SupoClip API

An AI-powered video clipping tool that transforms long-form content into viral short clips.

## Features

- **🎬 Video Processing**: Upload videos or provide YouTube URLs for automatic clipping
- **🤖 AI Analysis**: Intelligent transcript analysis to identify viral segments
- **🎨 Customization**: Custom fonts, subtitles, and transitions
- **📊 Analytics**: Track clip performance across platforms
- **📅 Scheduling**: Calendar integration for content scheduling
- **💡 AI Titles**: Generate platform-optimized viral titles

## Authentication

All endpoints (except root and health checks) require authentication via the `user_id` header:

```
user_id: your-user-uuid
```

## Rate Limiting

- Video processing: 10 requests per hour per user
- Other endpoints: 100 requests per minute per user

## Support

- Documentation: https://supoclip.com/docs
- GitHub: https://github.com/yourusername/supoclip
- Issues: https://github.com/yourusername/supoclip/issues
    """,
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "SupoClip Support",
        "url": "https://supoclip.com",
        "email": "support@supoclip.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Local development server"
        },
        {
            "url": "https://api.supoclip.com",
            "description": "Production server"
        }
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(tasks_router)
app.include_router(posting_router)
app.include_router(ai_titles_router)
app.include_router(watermarks_router)
app.include_router(analytics_router)
app.include_router(calendar_router)
app.include_router(quota_router)
app.include_router(billing_router)
app.include_router(experiments_router)
app.include_router(thumbnails_router)
app.include_router(webhooks_router)
app.include_router(performance_router)
app.include_router(social_media_router)

# Mount static files for serving clips
clips_dir = Path(config.temp_dir) / "clips"
clips_dir.mkdir(parents=True, exist_ok=True)
app.mount("/clips", StaticFiles(directory=str(clips_dir)), name="clips")

# Mount static files for serving thumbnails
thumbnails_dir = Path(config.temp_dir) / "thumbnails"
thumbnails_dir.mkdir(parents=True, exist_ok=True)
app.mount("/thumbnails", StaticFiles(directory=str(thumbnails_dir)), name="thumbnails")

@app.get(
    "/",
    summary="API Root",
    description="Get basic API information and links to documentation",
    tags=["Core"],
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": {
                        "message": "This is the SupoClip FastAPI-based API. Visit /docs for the API documentation.",
                        "version": "1.0.0",
                        "docs": "/docs",
                        "health": "/health/db"
                    }
                }
            }
        }
    }
)
def read_root():
    return {
        "message": "This is the SupoClip FastAPI-based API. Visit /docs for the API documentation.",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health/db"
    }

@app.get(
    "/health/db",
    summary="Database Health Check",
    description="Check if the database is accessible and responding",
    tags=["Core"],
    responses={
        200: {
            "description": "Database health status",
            "content": {
                "application/json": {
                    "examples": {
                        "healthy": {
                            "summary": "Healthy database",
                            "value": {"status": "healthy", "database": "connected"}
                        },
                        "unhealthy": {
                            "summary": "Unhealthy database",
                            "value": {"status": "unhealthy", "database": "disconnected", "error": "Connection timeout"}
                        }
                    }
                }
            }
        }
    }
)
async def check_database_health(db: AsyncSession = Depends(get_db)):
    """Check database connectivity"""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.post(
    "/start",
    summary="Process Video (Synchronous)",
    description="""
Process a video and generate clips immediately (synchronous operation).

This endpoint:
1. Downloads the video (if YouTube URL) or uses uploaded file
2. Generates transcript using AssemblyAI
3. Analyzes transcript with AI to identify viral segments
4. Creates 9:16 vertical clips with subtitles and transitions
5. Returns all results immediately

**Note**: For long videos (>10 minutes), use `/start-with-progress` instead for better UX.

**Authentication**: Required via `user_id` header
    """,
    tags=["Video Processing"],
    responses={
        200: {
            "description": "Video processed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Task started successfully",
                        "task_id": "550e8400-e29b-41d4-a716-446655440000",
                        "relevant_segments": [
                            {
                                "start_time": 10.5,
                                "end_time": 25.3,
                                "text": "In this moment I reveal the secret to...",
                                "relevance_score": 95,
                                "reasoning": "Strong hook with valuable insight"
                            }
                        ],
                        "clips": [
                            {
                                "filename": "clip_1_10.5_25.3.mp4",
                                "path": "/tmp/clips/clip_1_10.5_25.3.mp4",
                                "start_time": 10.5,
                                "end_time": 25.3,
                                "duration": 14.8,
                                "text": "In this moment I reveal...",
                                "relevance_score": 95,
                                "reasoning": "Strong hook with valuable insight"
                            }
                        ],
                        "summary": "Video discusses productivity tips and life hacks",
                        "key_topics": ["productivity", "time management", "habits"]
                    }
                }
            }
        },
        400: {
            "description": "Bad request - missing or invalid parameters",
            "content": {
                "application/json": {
                    "example": {"detail": "Source URL is required"}
                }
            }
        },
        401: {
            "description": "Unauthorized - missing or invalid user_id",
            "content": {
                "application/json": {
                    "example": {"detail": "User authentication required"}
                }
            }
        },
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {"detail": "User not found"}
                }
            }
        },
        500: {
            "description": "Server error during processing",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to download video"}
                }
            }
        }
    }
)
async def start_task(request: Request):
  """Start a new task for authenticated users"""
  logger.info("🚀 Starting new task request")

  data = await request.json()
  headers = request.headers

  raw_source = data.get("source")
  user_id = headers.get("user_id")

  # Get font customization options from request
  font_options = data.get("font_options", {})
  font_family = font_options.get("font_family", "TikTokSans-Regular")
  font_size = font_options.get("font_size", 24)
  font_color = font_options.get("font_color", "#FFFFFF")

  logger.info(f"📝 Request data - URL: {raw_source.get('url') if raw_source else 'None'}, User ID: {user_id}")

  if not raw_source or not raw_source.get("url"):
    logger.error("❌ Source URL is missing")
    raise HTTPException(status_code=400, detail="Source URL is required")

  if not user_id:
    logger.error("❌ User ID is missing")
    raise HTTPException(status_code=401, detail="User authentication required")

  # Validate user_id is a valid string and user exists
  if not user_id or len(user_id.strip()) == 0:
    logger.error(f"❌ Invalid user ID format: {user_id}")
    raise HTTPException(status_code=400, detail="Invalid user ID format")

  logger.info(f"🔍 Checking if user {user_id} exists in database")
  # Check if user exists in database
  async with AsyncSessionLocal() as db:
    user_exists = await db.execute(
      text("SELECT 1 FROM users WHERE id = :user_id"),
      {"user_id": user_id}
    )
    if not user_exists.fetchone():
      logger.error(f"❌ User {user_id} not found in database")
      raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"✅ User {user_id} found in database")

    source = Source()
    source.type = source.decide_source_type(raw_source["url"])
    logger.info(f"📺 Source type detected: {source.type}")

    if source.type == "youtube":
        logger.info("🎬 Getting YouTube video title")
        source.title = get_youtube_video_title(raw_source["url"])
        if not source.title:
            logger.warning("⚠️ Could not get YouTube title, using default")
            source.title = "YouTube Video"
        logger.info(f"📝 Video title: {source.title}")
    else:
        source.title = raw_source.get("title", "Uploaded Video")
        logger.info(f"📝 Custom title: {source.title}")

    relevant_segments_json = []
    clips_info = []
    relevant_parts = None

    logger.info("💾 Saving source and creating task in database")
    async with AsyncSessionLocal() as db:
        db.add(source)
        await db.flush()
        logger.info(f"✅ Source saved with ID: {source.id}")

        task = Task(
            user_id=user_id,
            source_id=source.id,
            generated_clips_ids=None,
            font_family=font_family,
            font_size=font_size,
            font_color=font_color,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        db.add(task)
        await db.commit()
        logger.info(f"✅ Task created with ID: {task.id}")

        # Determine video path based on source type
        video_path = None
        if source.type == "youtube":
            logger.info("⬇️ Starting YouTube video download")
            video_path = download_youtube_video(raw_source["url"])
            if not video_path:
                logger.error("❌ Failed to download video")
                raise HTTPException(status_code=500, detail="Failed to download video")
            logger.info(f"✅ Video downloaded to: {video_path}")
        else:
            # For uploaded videos, the URL is actually the file path
            video_path = raw_source["url"]
            logger.info(f"📁 Using uploaded video at: {video_path}")

            # Verify the uploaded file exists
            if not Path(video_path).exists():
                logger.error(f"❌ Uploaded video file not found: {video_path}")
                raise HTTPException(status_code=404, detail="Uploaded video file not found")

        # Process video (same for both YouTube and uploaded videos)
        if video_path:
            logger.info("🎤 Starting transcript generation with AssemblyAI + SRT equalization")
            transcript = get_video_transcript(video_path)
            logger.info(f"✅ AssemblyAI transcript generated with 10-char line equalization (length: {len(transcript)} characters)")

            logger.info("🤖 Starting AI analysis for relevant segments")
            relevant_parts = await get_most_relevant_parts_by_transcript(transcript)
            logger.info(f"✅ AI analysis complete - found {len(relevant_parts.most_relevant_segments)} segments")

            # Convert to JSON format for response
            logger.info("📊 Converting AI results to JSON format")
            relevant_segments_json = [
                {
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "text": segment.text,
                    "relevance_score": segment.relevance_score,
                    "reasoning": segment.reasoning
                }
                for segment in relevant_parts.most_relevant_segments
            ]
            logger.info(f"✅ Created {len(relevant_segments_json)} segment records")

            # Create clips from relevant segments with transitions and custom fonts
            logger.info("🎬 Starting video clip generation with transitions")
            clips_output_dir = Path(config.temp_dir) / "clips"
            logger.info(f"📁 Output directory: {clips_output_dir}")
            logger.info(f"🎨 Font settings - Family: {font_family}, Size: {font_size}, Color: {font_color}")
            clips_info = create_clips_with_transitions(video_path, relevant_segments_json, clips_output_dir, font_family, font_size, font_color)
            logger.info(f"✅ Generated {len(clips_info)} video clips with transitions")

            # Upload clips to CDN (if enabled)
            logger.info("☁️ Uploading clips to CDN (if configured)")
            cdn_urls = await upload_clips_batch(clips_info, task.id)
            logger.info(f"✅ CDN upload complete - {sum(1 for u in cdn_urls.values() if u)} clips uploaded")

            # Save clips to database
            logger.info("💾 Saving clips to database")
            async with AsyncSessionLocal() as db:
                clip_ids = []
                for i, clip_info in enumerate(clips_info):
                    logger.info(f"💾 Saving clip {i+1}/{len(clips_info)}: {clip_info['filename']}")
                    cdn_url = cdn_urls.get(clip_info["filename"])
                    clip_record = GeneratedClip(
                        task_id=task.id,
                        filename=clip_info["filename"],
                        file_path=clip_info["path"],
                        cdn_url=cdn_url,
                        start_time=clip_info["start_time"],
                        end_time=clip_info["end_time"],
                        duration=clip_info["duration"],
                        text=clip_info["text"],
                        relevance_score=clip_info["relevance_score"],
                        reasoning=clip_info["reasoning"],
                        clip_order=i + 1
                    )
                    db.add(clip_record)
                    await db.flush()
                    clip_ids.append(clip_record.id)
                    logger.info(f"✅ Clip {i+1} saved with ID: {clip_record.id}")

                # Update task with clip IDs
                logger.info(f"🔗 Updating task with {len(clip_ids)} clip IDs")
                task_update = await db.execute(
                    text("UPDATE tasks SET generated_clips_ids = :clip_ids WHERE id = :task_id"),
                    {"clip_ids": clip_ids, "task_id": task.id}
                )
                await db.commit()
                logger.info("✅ Task updated with clip IDs")
        else:
            logger.error("❌ No video path available for processing")
            raise HTTPException(status_code=500, detail="No video available for processing")

        logger.info(f"🎉 Task completed successfully! Task ID: {task.id}")
    logger.info(f"📊 Final results - Segments: {len(relevant_segments_json)}, Clips: {len(clips_info)}")

    return {
        "message": "Task started successfully",
        "task_id": task.id,
        "relevant_segments": relevant_segments_json,
        "clips": clips_info,
        "summary": relevant_parts.summary if relevant_parts else None,
        "key_topics": relevant_parts.key_topics if relevant_parts else None
    }

@app.post("/start-with-progress")
async def start_task_with_progress(request: Request):
    """Start a new task and return task ID for SSE tracking"""

    data = await request.json()
    headers = request.headers
    raw_source = data.get("source")
    user_id = headers.get("user_id")

    # Get font customization options from request
    font_options = data.get("font_options", {})
    font_family = font_options.get("font_family", "TikTokSans-Regular")
    font_size = font_options.get("font_size", 24)
    font_color = font_options.get("font_color", "#FFFFFF")

    logger.info(f"📝 Request data - URL: {raw_source.get('url') if raw_source else 'None'}, User ID: {user_id}")

    if not raw_source or not raw_source.get("url"):
        logger.error("❌ Source URL is missing")
        raise HTTPException(status_code=400, detail="Source URL is required")

    if not user_id:
        logger.error("❌ User ID is missing")
        raise HTTPException(status_code=401, detail="User authentication required")

    # Validate user_id and create initial task
    async with AsyncSessionLocal() as db:
        user_exists = await db.execute(
            text("SELECT 1 FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        if not user_exists.fetchone():
            logger.error(f"❌ User {user_id} not found in database")
            raise HTTPException(status_code=404, detail="User not found")

        source = Source()
        source.type = source.decide_source_type(raw_source["url"])

        # Get actual title based on source type
        if source.type == "youtube":
            try:
                source.title = get_youtube_video_title(raw_source["url"])
                if not source.title:
                    logger.warning("⚠️ Could not get YouTube title, using default")
                    source.title = "YouTube Video"
                logger.info(f"📝 YouTube video title: {source.title}")
            except Exception as e:
                logger.warning(f"⚠️ Could not get YouTube title, using default: {str(e)}")
                source.title = "YouTube Video"
        else:
            source.title = raw_source.get("title", "Uploaded Video")

        db.add(source)
        await db.flush()

        task = Task(
            user_id=user_id,
            source_id=source.id,
            generated_clips_ids=None,
            status="processing",
            font_family=font_family,
            font_size=font_size,
            font_color=font_color,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        db.add(task)
        await db.commit()

        # Start processing in background
        asyncio.create_task(process_video_task(task.id, raw_source, user_id, font_family, font_size, font_color))

        return {"task_id": task.id, "message": "Task started successfully"}

async def update_task_status(task_id: str, status: str):
    """Update task status in database"""
    async with AsyncSessionLocal() as db:
        await db.execute(
            text("UPDATE tasks SET status = :status, updated_at = NOW() WHERE id = :task_id"),
            {"status": status, "task_id": task_id}
        )
        await db.commit()

async def process_video_task(task_id: str, raw_source: dict, user_id: str, font_family: str = "TikTokSans-Regular", font_size: int = 24, font_color: str = "#FFFFFF"):
    """Background task to process video and update task status"""

    try:
        logger.info(f"🚀 Starting background processing for task {task_id}")
        await update_task_status(task_id, "processing")

        # Get source from database
        async with AsyncSessionLocal() as db:
            source_result = await db.execute(
                text("SELECT * FROM sources WHERE id IN (SELECT source_id FROM tasks WHERE id = :task_id)"),
                {"task_id": task_id}
            )
            source_data = source_result.fetchone()
            if not source_data:
                raise Exception("Source not found")

        logger.info(f"📊 Task {task_id}: Analyzing video source...")

        # Determine video path based on source type
        video_path = None
        if source_data.type == "youtube":
            logger.info(f"📊 Task {task_id}: Downloading YouTube video...")
            video_path = download_youtube_video(raw_source["url"])
            if not video_path:
                raise Exception("Failed to download video")
            logger.info(f"✅ Video downloaded to: {video_path}")
        else:
            video_path = raw_source["url"]
            if not Path(video_path).exists():
                raise Exception("Uploaded video file not found")

        # Process video
        if video_path:
            logger.info(f"📊 Task {task_id}: Generating transcript with AssemblyAI...")
            transcript = get_video_transcript(video_path)
            logger.info(f"✅ Transcript generated (length: {len(transcript)} characters)")

            logger.info(f"📊 Task {task_id}: AI analyzing content for best clips...")
            relevant_parts = await get_most_relevant_parts_by_transcript(transcript)
            logger.info(f"✅ AI analysis complete - found {len(relevant_parts.most_relevant_segments)} segments")

            # Convert to JSON format
            relevant_segments_json = [
                {
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "text": segment.text,
                    "relevance_score": segment.relevance_score,
                    "reasoning": segment.reasoning
                }
                for segment in relevant_parts.most_relevant_segments
            ]

            logger.info(f"📊 Task {task_id}: Creating {len(relevant_segments_json)} video clips with transitions...")
            clips_output_dir = Path(config.temp_dir) / "clips"
            logger.info(f"🎨 Task {task_id}: Font settings - Family: {font_family}, Size: {font_size}, Color: {font_color}")
            clips_info = create_clips_with_transitions(video_path, relevant_segments_json, clips_output_dir, font_family, font_size, font_color)
            logger.info(f"✅ Generated {len(clips_info)} video clips with transitions")

            # Upload clips to CDN (if enabled)
            logger.info(f"☁️ Task {task_id}: Uploading clips to CDN (if configured)")
            cdn_urls = await upload_clips_batch(clips_info, task_id)
            logger.info(f"✅ Task {task_id}: CDN upload complete - {sum(1 for u in cdn_urls.values() if u)} clips uploaded")

            logger.info(f"📊 Task {task_id}: Saving clips to database...")
            async with AsyncSessionLocal() as db:
                clip_ids = []
                for i, clip_info in enumerate(clips_info):
                    cdn_url = cdn_urls.get(clip_info["filename"])
                    clip_record = GeneratedClip(
                        task_id=task_id,
                        filename=clip_info["filename"],
                        file_path=clip_info["path"],
                        cdn_url=cdn_url,
                        start_time=clip_info["start_time"],
                        end_time=clip_info["end_time"],
                        duration=clip_info["duration"],
                        text=clip_info["text"],
                        relevance_score=clip_info["relevance_score"],
                        reasoning=clip_info["reasoning"],
                        clip_order=i + 1
                    )
                    db.add(clip_record)
                    await db.flush()
                    clip_ids.append(clip_record.id)

                # Update task with clip IDs
                await db.execute(
                    text("UPDATE tasks SET generated_clips_ids = :clip_ids WHERE id = :task_id"),
                    {"clip_ids": clip_ids, "task_id": task_id}
                )
                await db.commit()

        # Mark as completed
        await update_task_status(task_id, "completed")
        logger.info(f"🎉 Task {task_id} completed successfully!")

    except Exception as e:
        logger.error(f"❌ Error processing task {task_id}: {str(e)}")
        await update_task_status(task_id, "error")
        logger.error(f"📊 Task {task_id} marked as error: {str(e)}")

@app.get("/tasks/{task_id}/clips")
async def get_task_clips(task_id: str, db: AsyncSession = Depends(get_db)):
  """Get all clips for a specific task"""
  try:
    # Get task and verify it exists
    task_result = await db.execute(
      text("SELECT * FROM tasks WHERE id = :task_id"),
      {"task_id": task_id}
    )
    task = task_result.fetchone()
    if not task:
      raise HTTPException(status_code=404, detail="Task not found")

    # Get clips for this task
    clips_result = await db.execute(
      text("""
        SELECT id, filename, file_path, cdn_url, start_time, end_time, duration,
               text, relevance_score, reasoning, clip_order, created_at
        FROM generated_clips
        WHERE task_id = :task_id
        ORDER BY clip_order ASC
      """),
      {"task_id": task_id}
    )
    clips = clips_result.fetchall()

    # Convert to list of dictionaries and add serving URLs with CDN fallback
    clips_data = []
    for clip in clips:
      # Get best available URL (CDN with fallback to direct serving)
      video_url = get_clip_url(
        filename=clip.filename,
        cdn_url=clip.cdn_url if hasattr(clip, 'cdn_url') else None,
        task_id=task_id
      )

      clip_data = {
        "id": clip.id,
        "filename": clip.filename,
        "file_path": clip.file_path,
        "cdn_url": clip.cdn_url if hasattr(clip, 'cdn_url') else None,
        "start_time": clip.start_time,
        "end_time": clip.end_time,
        "duration": clip.duration,
        "text": clip.text,
        "relevance_score": clip.relevance_score,
        "reasoning": clip.reasoning,
        "clip_order": clip.clip_order,
        "created_at": clip.created_at.isoformat(),
        "video_url": video_url  # Best URL (CDN or fallback)
      }
      clips_data.append(clip_data)

    return {
      "task_id": task_id,
      "clips": clips_data,
      "total_clips": len(clips_data)
    }

  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error retrieving clips: {str(e)}")

@app.get("/tasks/{task_id}")
async def get_task_details(task_id: str, db: AsyncSession = Depends(get_db)):
  """Get task details including clips"""
  try:
    # Get task details
    task_result = await db.execute(
      text("""
        SELECT t.*, s.title as source_title, s.type as source_type
        FROM tasks t
        LEFT JOIN sources s ON t.source_id = s.id
        WHERE t.id = :task_id
      """),
      {"task_id": task_id}
    )
    task = task_result.fetchone()
    if not task:
      raise HTTPException(status_code=404, detail="Task not found")

    # Get clips count
    clips_count_result = await db.execute(
      text("SELECT COUNT(*) as count FROM generated_clips WHERE task_id = :task_id"),
      {"task_id": task_id}
    )
    clips_count = clips_count_result.fetchone().count

    task_data = {
      "id": task.id,
      "user_id": task.user_id,
      "source_id": task.source_id,
      "source_title": task.source_title,
      "source_type": task.source_type,
      "status": task.status,
      "generated_clips_ids": task.generated_clips_ids,
      "clips_count": clips_count,
      "font_family": task.font_family if hasattr(task, 'font_family') else None,
      "font_size": task.font_size if hasattr(task, 'font_size') else None,
      "font_color": task.font_color if hasattr(task, 'font_color') else None,
      "created_at": task.created_at.isoformat(),
      "updated_at": task.updated_at.isoformat()
    }

    return task_data

  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error retrieving task: {str(e)}")

@app.get(
    "/fonts",
    summary="List Available Fonts",
    description="""
Get list of all available font families for subtitle customization.

Fonts are .ttf files stored in the backend/fonts/ directory.
Use the `name` field in the `font_options.font_family` parameter when processing videos.
    """,
    tags=["Resources"],
    responses={
        200: {
            "description": "List of available fonts",
            "content": {
                "application/json": {
                    "example": {
                        "fonts": [
                            {
                                "name": "TikTokSans-Regular",
                                "display_name": "TikTok Sans Regular",
                                "file_path": "/app/fonts/TikTokSans-Regular.ttf"
                            },
                            {
                                "name": "Arial-Bold",
                                "display_name": "Arial Bold",
                                "file_path": "/app/fonts/Arial-Bold.ttf"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def get_available_fonts():
    """Get list of available fonts"""
    try:
        fonts_dir = Path(__file__).parent.parent / "fonts"
        if not fonts_dir.exists():
            return {"fonts": [], "message": "Fonts directory not found"}

        font_files = []
        for font_file in fonts_dir.glob("*.ttf"):
            font_name = font_file.stem  # Get filename without extension
            font_files.append({
                "name": font_name,
                "display_name": font_name.replace("-", " ").replace("_", " ").title(),
                "file_path": str(font_file)
            })

        logger.info(f"Found {len(font_files)} available fonts")
        return {"fonts": font_files}

    except Exception as e:
        logger.error(f"Error retrieving fonts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving fonts: {str(e)}")

@app.get("/fonts/{font_name}")
async def get_font_file(font_name: str):
    """Serve a specific font file"""
    try:
        fonts_dir = Path(__file__).parent.parent / "fonts"
        font_path = fonts_dir / f"{font_name}.ttf"

        if not font_path.exists():
            raise HTTPException(status_code=404, detail="Font not found")

        return FileResponse(
            path=str(font_path),
            media_type="font/ttf",
            headers={
                "Cache-Control": "public, max-age=31536000",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving font {font_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving font: {str(e)}")

@app.get(
    "/transitions",
    summary="List Available Transitions",
    description="""
Get list of all available transition effects for clips.

Transitions are .mp4 files that are automatically applied between clips
when using the `create_clips_with_transitions()` function.
    """,
    tags=["Resources"],
    responses={
        200: {
            "description": "List of available transitions",
            "content": {
                "application/json": {
                    "example": {
                        "transitions": [
                            {
                                "name": "swipe_left",
                                "display_name": "Swipe Left",
                                "file_path": "/app/transitions/swipe_left.mp4"
                            },
                            {
                                "name": "fade_black",
                                "display_name": "Fade Black",
                                "file_path": "/app/transitions/fade_black.mp4"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def get_available_transitions():
    """Get list of available transition effects"""
    try:
        from .video_utils import get_available_transitions
        transitions = get_available_transitions()

        transition_info = []
        for transition_path in transitions:
            transition_file = Path(transition_path)
            transition_info.append({
                "name": transition_file.stem,
                "display_name": transition_file.stem.replace("_", " ").replace("-", " ").title(),
                "file_path": transition_path
            })

        logger.info(f"Found {len(transition_info)} available transitions")
        return {"transitions": transition_info}

    except Exception as e:
        logger.error(f"Error retrieving transitions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving transitions: {str(e)}")

# endpoint to upload a video
@app.post(
    "/upload",
    summary="Upload Video File",
    description="""
Upload a video file to the server for processing.

After upload, use the returned `video_path` as the `source.url` parameter
in the `/start` or `/start-with-progress` endpoints.

**Supported formats**: MP4, MOV, AVI, MKV
**Max file size**: 500 MB
    """,
    tags=["Video Processing"],
    responses={
        200: {
            "description": "Video uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Video uploaded successfully",
                        "video_path": "/tmp/uploads/550e8400-e29b-41d4-a716-446655440000.mp4"
                    }
                }
            }
        },
        400: {
            "description": "Bad request - no file provided",
            "content": {
                "application/json": {
                    "example": {"detail": "No video file provided"}
                }
            }
        },
        500: {
            "description": "Server error during upload",
            "content": {
                "application/json": {
                    "example": {"detail": "Error uploading video: Disk full"}
                }
            }
        }
    }
)
async def upload_video(request: Request):
    """Upload a video to the server"""
    try:
        from fastapi import UploadFile, File, Form
        import aiofiles

        # Get the form data
        form_data = await request.form()
        video_file = form_data.get("video")

        if not video_file or not hasattr(video_file, 'filename'):
            raise HTTPException(status_code=400, detail="No video file provided")

        # Create uploads directory
        uploads_dir = Path(config.temp_dir) / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename to avoid conflicts
        import uuid
        file_extension = Path(video_file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        video_path = uploads_dir / unique_filename

        # Save the uploaded file
        async with aiofiles.open(video_path, 'wb') as f:
            content = await video_file.read()
            await f.write(content)

        logger.info(f"✅ Video uploaded successfully to: {video_path}")

        return {
            "message": "Video uploaded successfully",
            "video_path": str(video_path)
        }
    except Exception as e:
        logger.error(f"❌ Error uploading video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading video: {str(e)}")
