"""
Analytics API routes for tracking clip performance and metrics
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func
import logging

from ...database import get_db
from ...models import ClipViews, ClipPerformance, GeneratedClip

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


# Pydantic models for request/response
class ViewMetricsRequest(BaseModel):
    """Request model for recording view metrics"""
    clip_id: str = Field(..., description="ID of the clip")
    platform: str = Field(..., description="Platform where clip was posted (e.g., tiktok, youtube_shorts, instagram_reels)")
    views: int = Field(default=0, ge=0, description="Number of views")
    likes: int = Field(default=0, ge=0, description="Number of likes")
    comments: int = Field(default=0, ge=0, description="Number of comments")
    shares: int = Field(default=0, ge=0, description="Number of shares")
    date: Optional[date] = Field(default=None, description="Date when metrics were recorded (defaults to today)")

    @validator('platform')
    def validate_platform(cls, v):
        """Validate platform name"""
        valid_platforms = ['tiktok', 'youtube_shorts', 'instagram_reels', 'facebook', 'twitter', 'linkedin']
        if v.lower() not in valid_platforms:
            raise ValueError(f"Platform must be one of: {', '.join(valid_platforms)}")
        return v.lower()


class PerformanceMetricsRequest(BaseModel):
    """Request model for recording performance metrics"""
    clip_id: str = Field(..., description="ID of the clip")
    engagement_rate: float = Field(default=0.0, ge=0.0, le=100.0, description="Engagement rate as percentage (0-100)")
    watch_time: float = Field(default=0.0, ge=0.0, description="Average watch time in seconds")
    retention_rate: float = Field(default=0.0, ge=0.0, le=100.0, description="Retention rate as percentage (0-100)")


class RecordMetricsRequest(BaseModel):
    """Combined request model for recording all metrics"""
    view_metrics: Optional[ViewMetricsRequest] = Field(default=None, description="View metrics to record")
    performance_metrics: Optional[PerformanceMetricsRequest] = Field(default=None, description="Performance metrics to record")


class ClipPerformanceResponse(BaseModel):
    """Response model for clip performance"""
    clip_id: str
    clip_filename: str
    clip_duration: float
    total_views: int
    total_likes: int
    total_comments: int
    total_shares: int
    avg_engagement_rate: float
    avg_watch_time: float
    avg_retention_rate: float
    platforms: List[str]
    view_metrics_by_platform: Dict[str, Dict[str, Any]]
    created_at: str
    last_updated: str


class DashboardStatsResponse(BaseModel):
    """Response model for dashboard statistics"""
    total_clips: int
    total_clips_with_metrics: int
    total_views: int
    total_likes: int
    total_comments: int
    total_shares: int
    total_engagements: int
    avg_engagement_rate: float
    avg_watch_time: float
    avg_retention_rate: float
    top_performing_clips: List[Dict[str, Any]]
    platform_breakdown: Dict[str, Dict[str, Any]]


@router.post("/record", status_code=201)
async def record_metrics(
    request: RecordMetricsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Record analytics metrics for a clip

    This endpoint allows recording view metrics (views, likes, comments, shares by platform)
    and/or performance metrics (engagement rate, watch time, retention rate).

    You can record both types of metrics in a single request or just one type.
    """
    try:
        logger.info(f"📊 Recording analytics metrics")

        # Validate that at least one type of metrics is provided
        if not request.view_metrics and not request.performance_metrics:
            raise HTTPException(
                status_code=400,
                detail="At least one of view_metrics or performance_metrics must be provided"
            )

        results = {}

        # Record view metrics if provided
        if request.view_metrics:
            vm = request.view_metrics

            # Verify clip exists
            clip_check = await db.execute(
                text("SELECT id FROM generated_clips WHERE id = :clip_id"),
                {"clip_id": vm.clip_id}
            )
            if not clip_check.fetchone():
                raise HTTPException(status_code=404, detail=f"Clip {vm.clip_id} not found")

            # Use provided date or default to today
            record_date = vm.date or date.today()

            # Check if a record already exists for this clip/platform/date
            existing_record = await db.execute(
                text("""
                    SELECT id FROM clip_views
                    WHERE clip_id = :clip_id AND platform = :platform AND date = :date
                """),
                {"clip_id": vm.clip_id, "platform": vm.platform, "date": record_date}
            )
            existing = existing_record.fetchone()

            if existing:
                # Update existing record
                await db.execute(
                    text("""
                        UPDATE clip_views
                        SET views = :views, likes = :likes, comments = :comments,
                            shares = :shares, updated_at = NOW()
                        WHERE id = :id
                    """),
                    {
                        "id": existing.id,
                        "views": vm.views,
                        "likes": vm.likes,
                        "comments": vm.comments,
                        "shares": vm.shares
                    }
                )
                await db.commit()
                logger.info(f"✅ Updated view metrics for clip {vm.clip_id} on {vm.platform} for {record_date}")
                results["view_metrics"] = {"status": "updated", "id": existing.id}
            else:
                # Create new record
                clip_view = ClipViews(
                    clip_id=vm.clip_id,
                    platform=vm.platform,
                    views=vm.views,
                    likes=vm.likes,
                    comments=vm.comments,
                    shares=vm.shares,
                    date=record_date
                )
                db.add(clip_view)
                await db.flush()
                await db.commit()
                logger.info(f"✅ Recorded view metrics for clip {vm.clip_id} on {vm.platform} for {record_date}")
                results["view_metrics"] = {"status": "created", "id": clip_view.id}

        # Record performance metrics if provided
        if request.performance_metrics:
            pm = request.performance_metrics

            # Verify clip exists
            clip_check = await db.execute(
                text("SELECT id FROM generated_clips WHERE id = :clip_id"),
                {"clip_id": pm.clip_id}
            )
            if not clip_check.fetchone():
                raise HTTPException(status_code=404, detail=f"Clip {pm.clip_id} not found")

            # Check if performance record already exists
            existing_performance = await db.execute(
                text("SELECT id FROM clip_performance WHERE clip_id = :clip_id"),
                {"clip_id": pm.clip_id}
            )
            existing = existing_performance.fetchone()

            if existing:
                # Update existing performance record
                await db.execute(
                    text("""
                        UPDATE clip_performance
                        SET engagement_rate = :engagement_rate, watch_time = :watch_time,
                            retention_rate = :retention_rate, updated_at = NOW()
                        WHERE id = :id
                    """),
                    {
                        "id": existing.id,
                        "engagement_rate": pm.engagement_rate,
                        "watch_time": pm.watch_time,
                        "retention_rate": pm.retention_rate
                    }
                )
                await db.commit()
                logger.info(f"✅ Updated performance metrics for clip {pm.clip_id}")
                results["performance_metrics"] = {"status": "updated", "id": existing.id}
            else:
                # Create new performance record
                clip_performance = ClipPerformance(
                    clip_id=pm.clip_id,
                    engagement_rate=pm.engagement_rate,
                    watch_time=pm.watch_time,
                    retention_rate=pm.retention_rate
                )
                db.add(clip_performance)
                await db.flush()
                await db.commit()
                logger.info(f"✅ Recorded performance metrics for clip {pm.clip_id}")
                results["performance_metrics"] = {"status": "created", "id": clip_performance.id}

        return {
            "message": "Metrics recorded successfully",
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error recording metrics: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error recording metrics: {str(e)}")


@router.get("/clip/{clip_id}", response_model=ClipPerformanceResponse)
async def get_clip_performance(
    clip_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive performance metrics for a specific clip

    Returns view metrics across all platforms, performance metrics,
    and aggregated statistics for the clip.
    """
    try:
        logger.info(f"📊 Fetching performance for clip {clip_id}")

        # Verify clip exists and get clip details
        clip_result = await db.execute(
            text("""
                SELECT id, filename, duration, created_at
                FROM generated_clips
                WHERE id = :clip_id
            """),
            {"clip_id": clip_id}
        )
        clip = clip_result.fetchone()
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")

        # Get all view metrics for this clip
        view_metrics_result = await db.execute(
            text("""
                SELECT platform, views, likes, comments, shares, date, updated_at
                FROM clip_views
                WHERE clip_id = :clip_id
                ORDER BY date DESC
            """),
            {"clip_id": clip_id}
        )
        view_metrics = view_metrics_result.fetchall()

        # Get performance metrics
        performance_result = await db.execute(
            text("""
                SELECT engagement_rate, watch_time, retention_rate, updated_at
                FROM clip_performance
                WHERE clip_id = :clip_id
            """),
            {"clip_id": clip_id}
        )
        performance = performance_result.fetchone()

        # Aggregate view metrics
        total_views = sum(vm.views for vm in view_metrics)
        total_likes = sum(vm.likes for vm in view_metrics)
        total_comments = sum(vm.comments for vm in view_metrics)
        total_shares = sum(vm.shares for vm in view_metrics)

        # Get unique platforms
        platforms = list(set(vm.platform for vm in view_metrics))

        # Group metrics by platform (latest for each platform)
        view_metrics_by_platform = {}
        for vm in view_metrics:
            if vm.platform not in view_metrics_by_platform:
                view_metrics_by_platform[vm.platform] = {
                    "views": vm.views,
                    "likes": vm.likes,
                    "comments": vm.comments,
                    "shares": vm.shares,
                    "date": vm.date.isoformat(),
                    "last_updated": vm.updated_at.isoformat()
                }

        # Get performance metrics or defaults
        avg_engagement_rate = performance.engagement_rate if performance else 0.0
        avg_watch_time = performance.watch_time if performance else 0.0
        avg_retention_rate = performance.retention_rate if performance else 0.0
        last_updated = performance.updated_at.isoformat() if performance else clip.created_at.isoformat()

        return ClipPerformanceResponse(
            clip_id=clip.id,
            clip_filename=clip.filename,
            clip_duration=clip.duration,
            total_views=total_views,
            total_likes=total_likes,
            total_comments=total_comments,
            total_shares=total_shares,
            avg_engagement_rate=avg_engagement_rate,
            avg_watch_time=avg_watch_time,
            avg_retention_rate=avg_retention_rate,
            platforms=platforms,
            view_metrics_by_platform=view_metrics_by_platform,
            created_at=clip.created_at.isoformat(),
            last_updated=last_updated
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching clip performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching clip performance: {str(e)}")


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    user_id: Optional[str] = None,
    task_id: Optional[str] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Get aggregated analytics dashboard statistics

    Returns overall performance metrics, top performing clips, and platform breakdown.

    Query parameters:
    - user_id: Filter by user (optional)
    - task_id: Filter by specific task (optional)
    - limit: Number of top performing clips to return (default: 10)
    """
    try:
        logger.info(f"📊 Fetching dashboard stats (user_id={user_id}, task_id={task_id})")

        # Build WHERE clause based on filters
        where_clauses = []
        params = {"limit": limit}

        if user_id:
            where_clauses.append("t.user_id = :user_id")
            params["user_id"] = user_id

        if task_id:
            where_clauses.append("gc.task_id = :task_id")
            params["task_id"] = task_id

        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # Get total clips count
        total_clips_result = await db.execute(
            text(f"""
                SELECT COUNT(DISTINCT gc.id) as count
                FROM generated_clips gc
                LEFT JOIN tasks t ON gc.task_id = t.id
                {where_clause}
            """),
            params
        )
        total_clips = total_clips_result.fetchone().count

        # Get clips with metrics count
        clips_with_metrics_result = await db.execute(
            text(f"""
                SELECT COUNT(DISTINCT gc.id) as count
                FROM generated_clips gc
                LEFT JOIN tasks t ON gc.task_id = t.id
                LEFT JOIN clip_views cv ON gc.id = cv.clip_id
                {where_clause}
                AND cv.id IS NOT NULL
            """),
            params
        )
        total_clips_with_metrics = clips_with_metrics_result.fetchone().count

        # Get aggregated view metrics
        aggregated_views_result = await db.execute(
            text(f"""
                SELECT
                    COALESCE(SUM(cv.views), 0) as total_views,
                    COALESCE(SUM(cv.likes), 0) as total_likes,
                    COALESCE(SUM(cv.comments), 0) as total_comments,
                    COALESCE(SUM(cv.shares), 0) as total_shares
                FROM clip_views cv
                JOIN generated_clips gc ON cv.clip_id = gc.id
                LEFT JOIN tasks t ON gc.task_id = t.id
                {where_clause}
            """),
            params
        )
        agg_views = aggregated_views_result.fetchone()

        total_views = agg_views.total_views or 0
        total_likes = agg_views.total_likes or 0
        total_comments = agg_views.total_comments or 0
        total_shares = agg_views.total_shares or 0
        total_engagements = total_likes + total_comments + total_shares

        # Get average performance metrics
        avg_performance_result = await db.execute(
            text(f"""
                SELECT
                    COALESCE(AVG(cp.engagement_rate), 0.0) as avg_engagement_rate,
                    COALESCE(AVG(cp.watch_time), 0.0) as avg_watch_time,
                    COALESCE(AVG(cp.retention_rate), 0.0) as avg_retention_rate
                FROM clip_performance cp
                JOIN generated_clips gc ON cp.clip_id = gc.id
                LEFT JOIN tasks t ON gc.task_id = t.id
                {where_clause}
            """),
            params
        )
        avg_perf = avg_performance_result.fetchone()

        avg_engagement_rate = float(avg_perf.avg_engagement_rate or 0.0)
        avg_watch_time = float(avg_perf.avg_watch_time or 0.0)
        avg_retention_rate = float(avg_perf.avg_retention_rate or 0.0)

        # Get top performing clips
        top_clips_result = await db.execute(
            text(f"""
                SELECT
                    gc.id,
                    gc.filename,
                    gc.duration,
                    gc.relevance_score,
                    COALESCE(SUM(cv.views), 0) as total_views,
                    COALESCE(SUM(cv.likes), 0) as total_likes,
                    COALESCE(SUM(cv.comments), 0) as total_comments,
                    COALESCE(SUM(cv.shares), 0) as total_shares,
                    COALESCE(cp.engagement_rate, 0.0) as engagement_rate,
                    COALESCE(cp.retention_rate, 0.0) as retention_rate
                FROM generated_clips gc
                LEFT JOIN tasks t ON gc.task_id = t.id
                LEFT JOIN clip_views cv ON gc.id = cv.clip_id
                LEFT JOIN clip_performance cp ON gc.id = cp.clip_id
                {where_clause}
                GROUP BY gc.id, gc.filename, gc.duration, gc.relevance_score, cp.engagement_rate, cp.retention_rate
                ORDER BY total_views DESC, engagement_rate DESC
                LIMIT :limit
            """),
            params
        )
        top_clips = top_clips_result.fetchall()

        top_performing_clips = [
            {
                "clip_id": clip.id,
                "filename": clip.filename,
                "duration": clip.duration,
                "relevance_score": clip.relevance_score,
                "total_views": clip.total_views,
                "total_likes": clip.total_likes,
                "total_comments": clip.total_comments,
                "total_shares": clip.total_shares,
                "engagement_rate": float(clip.engagement_rate),
                "retention_rate": float(clip.retention_rate),
                "video_url": f"/clips/{clip.filename}"
            }
            for clip in top_clips
        ]

        # Get platform breakdown
        platform_breakdown_result = await db.execute(
            text(f"""
                SELECT
                    cv.platform,
                    COUNT(DISTINCT cv.clip_id) as clips_count,
                    COALESCE(SUM(cv.views), 0) as total_views,
                    COALESCE(SUM(cv.likes), 0) as total_likes,
                    COALESCE(SUM(cv.comments), 0) as total_comments,
                    COALESCE(SUM(cv.shares), 0) as total_shares
                FROM clip_views cv
                JOIN generated_clips gc ON cv.clip_id = gc.id
                LEFT JOIN tasks t ON gc.task_id = t.id
                {where_clause}
                GROUP BY cv.platform
                ORDER BY total_views DESC
            """),
            params
        )
        platform_breakdown_rows = platform_breakdown_result.fetchall()

        platform_breakdown = {}
        for row in platform_breakdown_rows:
            platform_breakdown[row.platform] = {
                "clips_count": row.clips_count,
                "total_views": row.total_views,
                "total_likes": row.total_likes,
                "total_comments": row.total_comments,
                "total_shares": row.total_shares,
                "total_engagements": row.total_likes + row.total_comments + row.total_shares
            }

        return DashboardStatsResponse(
            total_clips=total_clips,
            total_clips_with_metrics=total_clips_with_metrics,
            total_views=total_views,
            total_likes=total_likes,
            total_comments=total_comments,
            total_shares=total_shares,
            total_engagements=total_engagements,
            avg_engagement_rate=avg_engagement_rate,
            avg_watch_time=avg_watch_time,
            avg_retention_rate=avg_retention_rate,
            top_performing_clips=top_performing_clips,
            platform_breakdown=platform_breakdown
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")
