"""
MISSING SQLAlchemy MODELS for Social Media Integration
Add these models to backend/src/models.py

These models correspond to the tables created in:
- migrations/002_social_media_integrations.sql
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Text, ARRAY, CheckConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from .database import Base


class SocialMediaAccount(Base):
    """OAuth credentials for social media platforms"""
    __tablename__ = "social_media_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_string)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    platform_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    platform_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # OAuth credentials (should be encrypted in production)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Platform-specific metadata
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, server_default=text("'{}'"))

    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Check constraint for platform
    __table_args__ = (
        CheckConstraint("platform IN ('tiktok', 'instagram', 'youtube', 'twitter')", name="check_social_platform"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="social_media_accounts")
    post_attempts: Mapped[List["PostAttempt"]] = relationship("PostAttempt", back_populates="social_media_account", cascade="all, delete-orphan")


class SocialScheduledPost(Base):
    """
    Scheduled posts for social media platforms
    NOTE: Renamed from 'scheduled_posts' to 'social_scheduled_posts' to avoid conflict with calendar table
    """
    __tablename__ = "social_scheduled_posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_string)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    clip_id: Mapped[str] = mapped_column(String(36), ForeignKey("generated_clips.id", ondelete="CASCADE"), nullable=False)

    # Publishing details
    platforms: Mapped[List[str]] = mapped_column(ARRAY(String(20)), nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Post content
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hashtags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)

    # Post configuration per platform
    platform_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, server_default=text("'{}'"))

    # Status tracking
    status: Mapped[str] = mapped_column(String(20), server_default=text("'scheduled'"), nullable=False)

    # Retry configuration
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    retry_delay_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Check constraint for status
    __table_args__ = (
        CheckConstraint("status IN ('scheduled', 'processing', 'completed', 'failed', 'cancelled')", name="check_social_scheduled_post_status"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="social_scheduled_posts")
    clip: Mapped["GeneratedClip"] = relationship("GeneratedClip", backref="social_scheduled_posts")
    post_attempts: Mapped[List["PostAttempt"]] = relationship("PostAttempt", back_populates="scheduled_post", cascade="all, delete-orphan")


class PostAttempt(Base):
    """Individual posting attempts to social media platforms"""
    __tablename__ = "post_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid_string)
    scheduled_post_id: Mapped[str] = mapped_column(String(36), ForeignKey("social_scheduled_posts.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    social_media_account_id: Mapped[str] = mapped_column(String(36), ForeignKey("social_media_accounts.id", ondelete="CASCADE"), nullable=False)

    # Attempt details
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default=text("'pending'"), nullable=False)

    # Response from platform
    platform_post_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    platform_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Check constraints
    __table_args__ = (
        CheckConstraint("platform IN ('tiktok', 'instagram', 'youtube', 'twitter')", name="check_post_attempt_platform"),
        CheckConstraint("status IN ('pending', 'processing', 'success', 'failed')", name="check_post_attempt_status"),
    )

    # Relationships
    scheduled_post: Mapped["SocialScheduledPost"] = relationship("SocialScheduledPost", back_populates="post_attempts")
    social_media_account: Mapped["SocialMediaAccount"] = relationship("SocialMediaAccount", back_populates="post_attempts")


# UPDATE EXISTING USER MODEL
# Add this relationship to the User class in models.py:
"""
class User(Base):
    # ... existing fields ...

    # Add these relationships:
    social_media_accounts: Mapped[List["SocialMediaAccount"]] = relationship("SocialMediaAccount", back_populates="user", cascade="all, delete-orphan")
    social_scheduled_posts: Mapped[List["SocialScheduledPost"]] = relationship("SocialScheduledPost", back_populates="user", cascade="all, delete-orphan")
"""

# UPDATE EXISTING GENERATEDCLIP MODEL
# Add this relationship to the GeneratedClip class in models.py:
"""
class GeneratedClip(Base):
    # ... existing fields ...

    # Add this relationship:
    social_scheduled_posts: Mapped[List["SocialScheduledPost"]] = relationship("SocialScheduledPost", back_populates="clip", cascade="all, delete-orphan")
"""
