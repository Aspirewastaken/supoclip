"""
Main calendar integration module providing base classes and interfaces.

This module provides the core calendar integration functionality for scheduling
posts to various calendar services (Google Calendar, iCloud Calendar, etc.).
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class CalendarProvider(str, Enum):
    """Supported calendar providers"""
    GOOGLE = "google"
    ICLOUD = "icloud"
    CALDAV = "caldav"


class ScheduledPost(BaseModel):
    """Model for a scheduled post event"""
    id: Optional[str] = None
    clip_id: str
    task_id: str
    user_id: str
    scheduled_time: datetime
    title: str
    description: Optional[str] = None
    clip_url: Optional[str] = None
    clip_metadata: Dict[str, Any] = Field(default_factory=dict)
    calendar_event_id: Optional[str] = None
    calendar_provider: CalendarProvider
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CalendarEvent(BaseModel):
    """Generic calendar event model"""
    event_id: str
    summary: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CalendarIntegration(ABC):
    """
    Abstract base class for calendar integrations.

    All calendar providers (Google, iCloud, etc.) should implement this interface.
    """

    def __init__(self, user_id: str, credentials: Optional[Dict[str, Any]] = None):
        """
        Initialize calendar integration.

        Args:
            user_id: User ID for this calendar integration
            credentials: Provider-specific credentials (tokens, passwords, etc.)
        """
        self.user_id = user_id
        self.credentials = credentials or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the calendar provider.

        Returns:
            bool: True if authentication successful, False otherwise
        """
        pass

    @abstractmethod
    async def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a calendar event.

        Args:
            title: Event title/summary
            start_time: Event start time
            end_time: Event end time (defaults to start_time + 5 minutes)
            description: Event description/notes
            metadata: Additional metadata to attach to the event

        Returns:
            str: Event ID from the calendar provider
        """
        pass

    @abstractmethod
    async def update_event(
        self,
        event_id: str,
        title: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update an existing calendar event.

        Args:
            event_id: Event ID to update
            title: New title (optional)
            start_time: New start time (optional)
            end_time: New end time (optional)
            description: New description (optional)
            metadata: New metadata (optional)

        Returns:
            bool: True if update successful, False otherwise
        """
        pass

    @abstractmethod
    async def delete_event(self, event_id: str) -> bool:
        """
        Delete a calendar event.

        Args:
            event_id: Event ID to delete

        Returns:
            bool: True if deletion successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """
        Get a specific calendar event.

        Args:
            event_id: Event ID to retrieve

        Returns:
            CalendarEvent if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[CalendarEvent]:
        """
        List calendar events within a date range.

        Args:
            start_date: Start of date range (defaults to now)
            end_date: End of date range (defaults to 30 days from start)
            limit: Maximum number of events to return

        Returns:
            List of CalendarEvent objects
        """
        pass

    async def schedule_post(
        self,
        clip_id: str,
        task_id: str,
        scheduled_time: datetime,
        clip_metadata: Dict[str, Any],
    ) -> ScheduledPost:
        """
        Schedule a post by creating a calendar event.

        Args:
            clip_id: ID of the clip to schedule
            task_id: ID of the task that generated the clip
            scheduled_time: When to publish the clip
            clip_metadata: Metadata about the clip (filename, duration, etc.)

        Returns:
            ScheduledPost object with calendar event details
        """
        self.logger.info(f"Scheduling post for clip {clip_id} at {scheduled_time}")

        # Create event title and description
        title = f"Post Clip: {clip_metadata.get('filename', 'Untitled')}"
        description = self._build_event_description(clip_id, task_id, clip_metadata)

        # Default to 5-minute event duration
        end_time = scheduled_time + timedelta(minutes=5)

        # Create metadata to attach to event
        event_metadata = {
            "clip_id": clip_id,
            "task_id": task_id,
            "user_id": self.user_id,
            "scheduled_by": "supoclip",
            **clip_metadata,
        }

        # Create the calendar event
        event_id = await self.create_event(
            title=title,
            start_time=scheduled_time,
            end_time=end_time,
            description=description,
            metadata=event_metadata,
        )

        # Create ScheduledPost object
        scheduled_post = ScheduledPost(
            clip_id=clip_id,
            task_id=task_id,
            user_id=self.user_id,
            scheduled_time=scheduled_time,
            title=title,
            description=description,
            clip_metadata=clip_metadata,
            calendar_event_id=event_id,
            calendar_provider=self.get_provider(),
        )

        self.logger.info(f"Successfully scheduled post with event ID: {event_id}")
        return scheduled_post

    @abstractmethod
    def get_provider(self) -> CalendarProvider:
        """
        Get the calendar provider type.

        Returns:
            CalendarProvider enum value
        """
        pass

    def _build_event_description(
        self, clip_id: str, task_id: str, clip_metadata: Dict[str, Any]
    ) -> str:
        """
        Build a formatted event description with clip details.

        Args:
            clip_id: Clip ID
            task_id: Task ID
            clip_metadata: Clip metadata

        Returns:
            Formatted description string
        """
        lines = ["📹 SupoClip - Scheduled Post", ""]

        # Add clip details
        if "filename" in clip_metadata:
            lines.append(f"Filename: {clip_metadata['filename']}")

        if "duration" in clip_metadata:
            duration = clip_metadata["duration"]
            lines.append(f"Duration: {duration:.1f}s")

        if "start_time" in clip_metadata and "end_time" in clip_metadata:
            lines.append(
                f"Original Timestamp: {clip_metadata['start_time']} - {clip_metadata['end_time']}"
            )

        if "relevance_score" in clip_metadata:
            score = clip_metadata["relevance_score"]
            lines.append(f"AI Relevance Score: {score:.2f}")

        if "text" in clip_metadata:
            text = clip_metadata["text"]
            if text:
                lines.append("")
                lines.append("Transcript:")
                lines.append(text[:500] + ("..." if len(text) > 500 else ""))

        # Add IDs for reference
        lines.append("")
        lines.append(f"Clip ID: {clip_id}")
        lines.append(f"Task ID: {task_id}")

        return "\n".join(lines)

    @staticmethod
    def get_calendar_integration(
        provider: CalendarProvider,
        user_id: str,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> "CalendarIntegration":
        """
        Factory method to create the appropriate calendar integration instance.

        Args:
            provider: Calendar provider type
            user_id: User ID
            credentials: Provider-specific credentials

        Returns:
            CalendarIntegration instance for the specified provider

        Raises:
            ValueError: If provider is not supported
        """
        if provider == CalendarProvider.GOOGLE:
            from .google_calendar import GoogleCalendarIntegration
            return GoogleCalendarIntegration(user_id, credentials)
        elif provider in (CalendarProvider.ICLOUD, CalendarProvider.CALDAV):
            from .caldav_calendar import CalDAVCalendarIntegration
            return CalDAVCalendarIntegration(user_id, credentials)
        else:
            raise ValueError(f"Unsupported calendar provider: {provider}")
