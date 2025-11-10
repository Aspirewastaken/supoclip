from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, CheckConstraint, ARRAY, Boolean, Float, Integer, Text, text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import uuid
import json

from .database import Base

def generate_uuid_string():
    """Generate a UUID as a string for compatibility with Prisma"""
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_string)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    emailVerified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), default=func.now())

    # Additional fields for backend compatibility
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Role and billing fields
    role: Mapped[str] = mapped_column(String(20), server_default=text("'free'"), nullable=False)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subscription_status: Mapped[str] = mapped_column(String(20), server_default=text("'inactive'"), nullable=False)
    subscription_current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Default font preferences
    default_font_family: Mapped[Optional[str]] = mapped_column(String(100), server_default=text("'TikTokSans-Regular'"), nullable=True)
    default_font_size: Mapped[Optional[int]] = mapped_column(Integer, server_default=text("'24'"), nullable=True)
    default_font_color: Mapped[Optional[str]] = mapped_column(String(7), server_default=text("'#FFFFFF'"), nullable=True)

    # Add check constraint for role and subscription_status
    __table_args__ = (
        CheckConstraint("role IN ('free', 'pro', 'admin')", name="check_user_role"),
        CheckConstraint("subscription_status IN ('active', 'inactive', 'canceled', 'past_due')", name="check_subscription_status"),
    )

    # Relationships
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    usage_tracking: Mapped[List["UsageTracking"]] = relationship("UsageTracking", back_populates="user", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_string)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    generated_clips_ids: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(36)), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default=text("'pending'"), nullable=False)

    # Font customization fields
    font_family: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, server_default=text("'TikTokSans-Regular'"))
    font_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, server_default=text("'24'"))
    font_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True, server_default=text("'#FFFFFF'"))  # Hex color code

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tasks")
    source: Mapped[Optional["Source"]] = relationship("Source", back_populates="tasks")
    generated_clips: Mapped[List["GeneratedClip"]] = relationship("GeneratedClip", back_populates="task", cascade="all, delete-orphan")

class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_string)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)  # Source URL
    channel_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Channel/uploader name
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Add check constraint for type enum
    __table_args__ = (
        CheckConstraint("type IN ('youtube', 'video_url')", name="check_source_type"),
    )

    # Relationships - Source can have multiple tasks
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="source")

    def decide_source_type(self, source_url: str) -> str:
      """Decide which type of source this is."""
      if "youtube" in source_url:
        return "youtube"
      else:
        return "video_url"

class GeneratedClip(Base):
    __tablename__ = "generated_clips"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_string)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    cdn_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)  # CDN URL if uploaded
    start_time: Mapped[str] = mapped_column(String(20), nullable=False)  # MM:SS format
    end_time: Mapped[str] = mapped_column(String(20), nullable=False)    # MM:SS format
    duration: Mapped[float] = mapped_column(Float, nullable=False)       # Duration in seconds
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)     # Transcript text for this clip
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # AI reasoning for selection
    clip_order: Mapped[int] = mapped_column(Integer, nullable=False)     # Order within the task
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="generated_clips")


class CalendarCredential(Base):
    """Store calendar credentials for users"""
    __tablename__ = "calendar_credentials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_string)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)  # 'google', 'icloud', 'caldav'

    # OAuth credentials (for Google Calendar)
    access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # CalDAV credentials (for iCloud and other CalDAV servers)
    caldav_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    caldav_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    caldav_password: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Should be encrypted in production
    calendar_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Additional metadata
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Check constraint for provider
    __table_args__ = (
        CheckConstraint("provider IN ('google', 'icloud', 'caldav')", name="check_calendar_provider"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="calendar_credentials")


class ScheduledPost(Base):
    """Store scheduled posts linked to calendar events"""
    __tablename__ = "scheduled_posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_string)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    clip_id: Mapped[str] = mapped_column(String(36), ForeignKey("generated_clips.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    calendar_credential_id: Mapped[str] = mapped_column(String(36), ForeignKey("calendar_credentials.id", ondelete="CASCADE"), nullable=False)

    # Calendar event details
    calendar_event_id: Mapped[str] = mapped_column(String(500), nullable=False)  # Event ID from calendar provider
    calendar_provider: Mapped[str] = mapped_column(String(20), nullable=False)

    # Scheduling details
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(String(20), server_default=text("'scheduled'"), nullable=False)
    # Status can be: 'scheduled', 'published', 'failed', 'cancelled'

    # Post metadata
    clip_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Check constraint for status and provider
    __table_args__ = (
        CheckConstraint("status IN ('scheduled', 'published', 'failed', 'cancelled')", name="check_scheduled_post_status"),
        CheckConstraint("calendar_provider IN ('google', 'icloud', 'caldav')", name="check_scheduled_post_provider"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="scheduled_posts")
    clip: Mapped["GeneratedClip"] = relationship("GeneratedClip", backref="scheduled_posts")
    task: Mapped["Task"] = relationship("Task", backref="scheduled_posts")
    calendar_credential: Mapped["CalendarCredential"] = relationship("CalendarCredential", backref="scheduled_posts")


class ClipViews(Base):
    """Track view metrics for clips across different social media platforms"""
    __tablename__ = "clip_views"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_string)
    clip_id: Mapped[str] = mapped_column(String(36), ForeignKey("generated_clips.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # tiktok, youtube_shorts, instagram_reels, etc.
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shares: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    date: Mapped[date] = mapped_column(Date, server_default=func.current_date(), nullable=False)  # Date when metrics were recorded
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Add check constraints
    __table_args__ = (
        CheckConstraint("views >= 0", name="check_clip_views_views"),
        CheckConstraint("likes >= 0", name="check_clip_views_likes"),
        CheckConstraint("comments >= 0", name="check_clip_views_comments"),
        CheckConstraint("shares >= 0", name="check_clip_views_shares"),
    )

    # Relationships
    clip: Mapped["GeneratedClip"] = relationship("GeneratedClip", backref="clip_views")


class ClipPerformance(Base):
    """Track engagement and watch metrics for clips"""
    __tablename__ = "clip_performance"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_string)
    clip_id: Mapped[str] = mapped_column(String(36), ForeignKey("generated_clips.id", ondelete="CASCADE"), nullable=False, unique=True)
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # Percentage (0-100)
    watch_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # Average watch time in seconds
    retention_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # Percentage (0-100)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Add check constraints
    __table_args__ = (
        CheckConstraint("engagement_rate >= 0 AND engagement_rate <= 100", name="check_clip_performance_engagement_rate"),
        CheckConstraint("watch_time >= 0", name="check_clip_performance_watch_time"),
        CheckConstraint("retention_rate >= 0 AND retention_rate <= 100", name="check_clip_performance_retention_rate"),
    )

    # Relationships
    clip: Mapped["GeneratedClip"] = relationship("GeneratedClip", backref="performance", uselist=False)


class Webhook(Base):
    """Store webhook configurations for task notifications"""
    __tablename__ = "webhooks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_string)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    events: Mapped[List[str]] = mapped_column(ARRAY(Text), nullable=False, server_default=text("'{}'"))
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", backref="webhooks")
    deliveries: Mapped[List["WebhookDelivery"]] = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    """Track webhook delivery attempts and status"""
    __tablename__ = "webhook_deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_string)
    webhook_id: Mapped[str] = mapped_column(String(36), ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pending'"))
    response_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Add check constraint for status
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'success', 'failed')", name="check_webhook_delivery_status"),
    )

    # Relationships
    webhook: Mapped["Webhook"] = relationship("Webhook", back_populates="deliveries")


class UsageTracking(Base):
    """Track monthly usage for quota enforcement"""
    __tablename__ = "usage_tracking"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_string)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    clips_generated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Add check constraints
    __table_args__ = (
        CheckConstraint("month >= 1 AND month <= 12", name="check_usage_tracking_month"),
        CheckConstraint("year >= 2020", name="check_usage_tracking_year"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="usage_tracking")


class Experiment(Base):
    """A/B testing experiments for clip variations"""
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_string)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    variations: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'[]'"))
    status: Mapped[str] = mapped_column(String(20), server_default=text("'running'"), nullable=False)
    winner_variation_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    confidence_threshold: Mapped[float] = mapped_column(Float, server_default=text("'0.95'"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Check constraints
    __table_args__ = (
        CheckConstraint("status IN ('running', 'paused', 'completed')", name="check_experiment_status"),
        CheckConstraint("confidence_threshold >= 0 AND confidence_threshold <= 1", name="check_confidence_threshold"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="experiments")
    results: Mapped[List["ExperimentResult"]] = relationship("ExperimentResult", back_populates="experiment", cascade="all, delete-orphan")


class ExperimentResult(Base):
    """Metrics for each variation in an A/B test"""
    __tablename__ = "experiment_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_string)
    experiment_id: Mapped[str] = mapped_column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    variation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    clip_id: Mapped[str] = mapped_column(String(36), ForeignKey("generated_clips.id", ondelete="CASCADE"), nullable=False)

    # Engagement metrics
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shares: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Calculated rates
    click_through_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    conversion_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Watch metrics
    avg_watch_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    watch_completion_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Check constraints
    __table_args__ = (
        CheckConstraint("views >= 0", name="check_experiment_result_views"),
        CheckConstraint("clicks >= 0", name="check_experiment_result_clicks"),
        CheckConstraint("conversions >= 0", name="check_experiment_result_conversions"),
        CheckConstraint("shares >= 0", name="check_experiment_result_shares"),
        CheckConstraint("likes >= 0", name="check_experiment_result_likes"),
        CheckConstraint("comments >= 0", name="check_experiment_result_comments"),
        CheckConstraint("click_through_rate >= 0 AND click_through_rate <= 1", name="check_ctr"),
        CheckConstraint("conversion_rate >= 0 AND conversion_rate <= 1", name="check_conversion_rate"),
        CheckConstraint("engagement_rate >= 0 AND engagement_rate <= 1", name="check_engagement_rate"),
        CheckConstraint("avg_watch_time >= 0", name="check_avg_watch_time"),
        CheckConstraint("watch_completion_rate >= 0 AND watch_completion_rate <= 1", name="check_completion_rate"),
    )

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="results")
    clip: Mapped["GeneratedClip"] = relationship("GeneratedClip", backref="experiment_results")
