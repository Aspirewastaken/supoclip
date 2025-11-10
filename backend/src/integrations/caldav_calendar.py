"""
CalDAV calendar integration for iCloud Calendar and other CalDAV servers.

This module provides integration with CalDAV-based calendar services
like iCloud Calendar, Nextcloud, etc.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import uuid
import caldav
from caldav.elements import dav, cdav
from icalendar import Calendar as ICalendar, Event as ICalEvent
import pytz

from .calendar import CalendarIntegration, CalendarProvider, CalendarEvent

logger = logging.getLogger(__name__)


class CalDAVCalendarIntegration(CalendarIntegration):
    """
    CalDAV calendar integration for iCloud and other CalDAV servers.

    Supports:
    - iCloud Calendar
    - Nextcloud Calendar
    - Any CalDAV-compliant server
    """

    # iCloud CalDAV server URL
    ICLOUD_CALDAV_URL = "https://caldav.icloud.com"

    def __init__(self, user_id: str, credentials: Optional[Dict[str, Any]] = None):
        """
        Initialize CalDAV calendar integration.

        Args:
            user_id: User ID
            credentials: Dictionary containing CalDAV credentials
                - url: CalDAV server URL (e.g., https://caldav.icloud.com)
                - username: CalDAV username (e.g., Apple ID for iCloud)
                - password: CalDAV password (app-specific password for iCloud)
                - calendar_name: Optional calendar name to use (defaults to primary)
        """
        super().__init__(user_id, credentials)
        self.client = None
        self.principal = None
        self.calendar = None

    async def authenticate(self) -> bool:
        """
        Authenticate with CalDAV server.

        Returns:
            bool: True if authentication successful
        """
        try:
            if not self.credentials:
                self.logger.error("No credentials provided for CalDAV")
                return False

            url = self.credentials.get("url", self.ICLOUD_CALDAV_URL)
            username = self.credentials.get("username")
            password = self.credentials.get("password")

            if not username or not password:
                self.logger.error("Missing username or password for CalDAV")
                return False

            # Create CalDAV client
            self.client = caldav.DAVClient(
                url=url,
                username=username,
                password=password,
            )

            # Get principal (user account)
            self.principal = self.client.principal()

            # Get calendars
            calendars = self.principal.calendars()

            if not calendars:
                self.logger.error("No calendars found for CalDAV user")
                return False

            # Select calendar
            calendar_name = self.credentials.get("calendar_name")
            if calendar_name:
                # Find calendar by name
                self.calendar = next(
                    (cal for cal in calendars if cal.name == calendar_name), None
                )
                if not self.calendar:
                    self.logger.warning(
                        f"Calendar '{calendar_name}' not found, using first calendar"
                    )
                    self.calendar = calendars[0]
            else:
                # Use first calendar
                self.calendar = calendars[0]

            self.logger.info(
                f"Successfully authenticated with CalDAV server, using calendar: {self.calendar.name}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to authenticate with CalDAV server: {e}")
            return False

    async def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a CalDAV calendar event.

        Args:
            title: Event title
            start_time: Event start time
            end_time: Event end time (defaults to start_time + 5 minutes)
            description: Event description
            metadata: Additional metadata (stored in event description)

        Returns:
            str: Event UID

        Raises:
            RuntimeError: If not authenticated or event creation fails
        """
        if not self.calendar:
            if not await self.authenticate():
                raise RuntimeError("Not authenticated with CalDAV server")

        if not end_time:
            end_time = start_time + timedelta(minutes=5)

        try:
            # Create iCalendar event
            cal = ICalendar()
            event = ICalEvent()

            # Generate unique ID
            event_uid = str(uuid.uuid4())

            event.add("uid", event_uid)
            event.add("summary", title)
            event.add("dtstart", start_time)
            event.add("dtend", end_time)
            event.add("dtstamp", datetime.utcnow())

            # Add description with metadata
            full_description = description or ""
            if metadata:
                full_description += "\n\n" + self._format_metadata(metadata)

            event.add("description", full_description)

            # Add to calendar
            cal.add_component(event)

            # Save event to CalDAV server
            self.calendar.save_event(cal.to_ical().decode("utf-8"))

            self.logger.info(f"Created CalDAV event: {event_uid}")
            return event_uid

        except Exception as e:
            self.logger.error(f"Failed to create CalDAV event: {e}")
            raise RuntimeError(f"Failed to create event: {e}")

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
        Update a CalDAV calendar event.

        Args:
            event_id: Event UID
            title: New title (optional)
            start_time: New start time (optional)
            end_time: New end time (optional)
            description: New description (optional)
            metadata: New metadata (optional)

        Returns:
            bool: True if update successful
        """
        if not self.calendar:
            if not await self.authenticate():
                return False

        try:
            # Find event by UID
            events = self.calendar.search(uid=event_id)

            if not events:
                self.logger.error(f"Event not found: {event_id}")
                return False

            event_obj = events[0]

            # Get event data
            ical = ICalendar.from_ical(event_obj.data)
            event = None
            for component in ical.walk():
                if component.name == "VEVENT":
                    event = component
                    break

            if not event:
                self.logger.error(f"Invalid event data for: {event_id}")
                return False

            # Update fields
            if title:
                event["summary"] = title
            if start_time:
                event["dtstart"] = start_time
            if end_time:
                event["dtend"] = end_time
            if description is not None:
                full_description = description
                if metadata:
                    full_description += "\n\n" + self._format_metadata(metadata)
                event["description"] = full_description

            # Update timestamp
            event["dtstamp"] = datetime.utcnow()

            # Save updated event
            event_obj.data = ical.to_ical()
            event_obj.save()

            self.logger.info(f"Updated CalDAV event: {event_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update CalDAV event: {e}")
            return False

    async def delete_event(self, event_id: str) -> bool:
        """
        Delete a CalDAV calendar event.

        Args:
            event_id: Event UID

        Returns:
            bool: True if deletion successful
        """
        if not self.calendar:
            if not await self.authenticate():
                return False

        try:
            # Find event by UID
            events = self.calendar.search(uid=event_id)

            if not events:
                self.logger.error(f"Event not found: {event_id}")
                return False

            # Delete event
            events[0].delete()

            self.logger.info(f"Deleted CalDAV event: {event_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete CalDAV event: {e}")
            return False

    async def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """
        Get a specific CalDAV calendar event.

        Args:
            event_id: Event UID

        Returns:
            CalendarEvent if found, None otherwise
        """
        if not self.calendar:
            if not await self.authenticate():
                return None

        try:
            # Find event by UID
            events = self.calendar.search(uid=event_id)

            if not events:
                return None

            event_obj = events[0]
            return self._parse_caldav_event(event_obj)

        except Exception as e:
            self.logger.error(f"Failed to get CalDAV event: {e}")
            return None

    async def list_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[CalendarEvent]:
        """
        List CalDAV calendar events within a date range.

        Args:
            start_date: Start of date range (defaults to now)
            end_date: End of date range (defaults to 30 days from start)
            limit: Maximum number of events to return

        Returns:
            List of CalendarEvent objects
        """
        if not self.calendar:
            if not await self.authenticate():
                return []

        if not start_date:
            start_date = datetime.utcnow()
        if not end_date:
            end_date = start_date + timedelta(days=30)

        try:
            # Search for events in date range
            events = self.calendar.date_search(start=start_date, end=end_date)

            # Parse and limit results
            parsed_events = []
            for event_obj in events[:limit]:
                try:
                    parsed_event = self._parse_caldav_event(event_obj)
                    if parsed_event:
                        parsed_events.append(parsed_event)
                except Exception as e:
                    self.logger.warning(f"Failed to parse event: {e}")
                    continue

            return parsed_events

        except Exception as e:
            self.logger.error(f"Failed to list CalDAV events: {e}")
            return []

    def get_provider(self) -> CalendarProvider:
        """Get the calendar provider type."""
        # Determine provider based on URL
        url = self.credentials.get("url", "")
        if "icloud.com" in url:
            return CalendarProvider.ICLOUD
        return CalendarProvider.CALDAV

    def _parse_caldav_event(self, event_obj) -> Optional[CalendarEvent]:
        """
        Parse a CalDAV event into a CalendarEvent object.

        Args:
            event_obj: CalDAV event object

        Returns:
            CalendarEvent object or None if parsing fails
        """
        try:
            ical = ICalendar.from_ical(event_obj.data)

            for component in ical.walk():
                if component.name == "VEVENT":
                    event_id = str(component.get("uid"))
                    summary = str(component.get("summary", ""))
                    description = str(component.get("description", ""))

                    # Parse dates
                    start = component.get("dtstart").dt
                    end = component.get("dtend").dt

                    # Convert to datetime if needed
                    if isinstance(start, datetime):
                        start_time = start
                    else:
                        start_time = datetime.combine(
                            start, datetime.min.time()
                        ).replace(tzinfo=pytz.UTC)

                    if isinstance(end, datetime):
                        end_time = end
                    else:
                        end_time = datetime.combine(end, datetime.min.time()).replace(
                            tzinfo=pytz.UTC
                        )

                    # Extract metadata from description
                    metadata = self._extract_metadata(description)

                    return CalendarEvent(
                        event_id=event_id,
                        summary=summary,
                        description=description,
                        start_time=start_time,
                        end_time=end_time,
                        metadata=metadata,
                    )

            return None

        except Exception as e:
            self.logger.error(f"Failed to parse CalDAV event: {e}")
            return None

    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        Format metadata as text for inclusion in event description.

        Args:
            metadata: Metadata dictionary

        Returns:
            Formatted metadata string
        """
        lines = ["--- Metadata ---"]
        for key, value in metadata.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def _extract_metadata(self, description: str) -> Dict[str, Any]:
        """
        Extract metadata from event description.

        Args:
            description: Event description

        Returns:
            Metadata dictionary
        """
        metadata = {}

        if "--- Metadata ---" not in description:
            return metadata

        # Extract metadata section
        parts = description.split("--- Metadata ---")
        if len(parts) < 2:
            return metadata

        metadata_text = parts[1].strip()
        for line in metadata_text.split("\n"):
            if ": " in line:
                key, value = line.split(": ", 1)
                metadata[key.strip()] = value.strip()

        return metadata
