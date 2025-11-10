"""
Google Calendar integration using Google Calendar API v3.

This module provides integration with Google Calendar using OAuth 2.0 authentication.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import logging
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .calendar import CalendarIntegration, CalendarProvider, CalendarEvent

logger = logging.getLogger(__name__)


class GoogleCalendarIntegration(CalendarIntegration):
    """
    Google Calendar integration using OAuth 2.0.

    Requires OAuth 2.0 credentials with calendar scope.
    """

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(self, user_id: str, credentials: Optional[Dict[str, Any]] = None):
        """
        Initialize Google Calendar integration.

        Args:
            user_id: User ID
            credentials: Dictionary containing OAuth tokens and credentials
                - access_token: OAuth access token
                - refresh_token: OAuth refresh token
                - token_uri: Token URI (optional)
                - client_id: OAuth client ID (optional)
                - client_secret: OAuth client secret (optional)
        """
        super().__init__(user_id, credentials)
        self.service = None
        self.creds = None

    async def authenticate(self) -> bool:
        """
        Authenticate with Google Calendar API.

        Returns:
            bool: True if authentication successful
        """
        try:
            if not self.credentials:
                self.logger.error("No credentials provided for Google Calendar")
                return False

            # Create credentials object from stored tokens
            self.creds = Credentials(
                token=self.credentials.get("access_token"),
                refresh_token=self.credentials.get("refresh_token"),
                token_uri=self.credentials.get(
                    "token_uri", "https://oauth2.googleapis.com/token"
                ),
                client_id=self.credentials.get("client_id"),
                client_secret=self.credentials.get("client_secret"),
                scopes=self.SCOPES,
            )

            # Refresh token if expired
            if self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
                # Update stored credentials with new access token
                self.credentials["access_token"] = self.creds.token

            # Build the service
            self.service = build("calendar", "v3", credentials=self.creds)

            self.logger.info("Successfully authenticated with Google Calendar")
            return True

        except Exception as e:
            self.logger.error(f"Failed to authenticate with Google Calendar: {e}")
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
        Create a Google Calendar event.

        Args:
            title: Event title
            start_time: Event start time
            end_time: Event end time (defaults to start_time + 5 minutes)
            description: Event description
            metadata: Additional metadata (stored in extended properties)

        Returns:
            str: Google Calendar event ID

        Raises:
            RuntimeError: If not authenticated or event creation fails
        """
        if not self.service:
            if not await self.authenticate():
                raise RuntimeError("Not authenticated with Google Calendar")

        if not end_time:
            end_time = start_time + timedelta(minutes=5)

        # Build event object
        event = {
            "summary": title,
            "description": description or "",
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC",
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 10},
                ],
            },
        }

        # Add metadata as extended properties
        if metadata:
            event["extendedProperties"] = {
                "private": {
                    k: str(v) if not isinstance(v, str) else v
                    for k, v in metadata.items()
                }
            }

        try:
            # Create the event
            created_event = (
                self.service.events()
                .insert(calendarId="primary", body=event)
                .execute()
            )

            event_id = created_event["id"]
            self.logger.info(f"Created Google Calendar event: {event_id}")
            return event_id

        except HttpError as e:
            self.logger.error(f"Failed to create Google Calendar event: {e}")
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
        Update a Google Calendar event.

        Args:
            event_id: Google Calendar event ID
            title: New title (optional)
            start_time: New start time (optional)
            end_time: New end time (optional)
            description: New description (optional)
            metadata: New metadata (optional)

        Returns:
            bool: True if update successful
        """
        if not self.service:
            if not await self.authenticate():
                return False

        try:
            # Get existing event
            event = (
                self.service.events()
                .get(calendarId="primary", eventId=event_id)
                .execute()
            )

            # Update fields
            if title:
                event["summary"] = title
            if description is not None:
                event["description"] = description
            if start_time:
                event["start"] = {
                    "dateTime": start_time.isoformat(),
                    "timeZone": "UTC",
                }
            if end_time:
                event["end"] = {
                    "dateTime": end_time.isoformat(),
                    "timeZone": "UTC",
                }
            if metadata:
                if "extendedProperties" not in event:
                    event["extendedProperties"] = {"private": {}}
                event["extendedProperties"]["private"].update(
                    {
                        k: str(v) if not isinstance(v, str) else v
                        for k, v in metadata.items()
                    }
                )

            # Update the event
            self.service.events().update(
                calendarId="primary", eventId=event_id, body=event
            ).execute()

            self.logger.info(f"Updated Google Calendar event: {event_id}")
            return True

        except HttpError as e:
            self.logger.error(f"Failed to update Google Calendar event: {e}")
            return False

    async def delete_event(self, event_id: str) -> bool:
        """
        Delete a Google Calendar event.

        Args:
            event_id: Google Calendar event ID

        Returns:
            bool: True if deletion successful
        """
        if not self.service:
            if not await self.authenticate():
                return False

        try:
            self.service.events().delete(
                calendarId="primary", eventId=event_id
            ).execute()

            self.logger.info(f"Deleted Google Calendar event: {event_id}")
            return True

        except HttpError as e:
            self.logger.error(f"Failed to delete Google Calendar event: {e}")
            return False

    async def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """
        Get a specific Google Calendar event.

        Args:
            event_id: Google Calendar event ID

        Returns:
            CalendarEvent if found, None otherwise
        """
        if not self.service:
            if not await self.authenticate():
                return None

        try:
            event = (
                self.service.events()
                .get(calendarId="primary", eventId=event_id)
                .execute()
            )

            return self._parse_google_event(event)

        except HttpError as e:
            self.logger.error(f"Failed to get Google Calendar event: {e}")
            return None

    async def list_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[CalendarEvent]:
        """
        List Google Calendar events within a date range.

        Args:
            start_date: Start of date range (defaults to now)
            end_date: End of date range (defaults to 30 days from start)
            limit: Maximum number of events to return

        Returns:
            List of CalendarEvent objects
        """
        if not self.service:
            if not await self.authenticate():
                return []

        if not start_date:
            start_date = datetime.utcnow()
        if not end_date:
            end_date = start_date + timedelta(days=30)

        try:
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=start_date.isoformat() + "Z",
                    timeMax=end_date.isoformat() + "Z",
                    maxResults=limit,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            return [self._parse_google_event(event) for event in events]

        except HttpError as e:
            self.logger.error(f"Failed to list Google Calendar events: {e}")
            return []

    def get_provider(self) -> CalendarProvider:
        """Get the calendar provider type."""
        return CalendarProvider.GOOGLE

    def _parse_google_event(self, event: Dict[str, Any]) -> CalendarEvent:
        """
        Parse a Google Calendar event into a CalendarEvent object.

        Args:
            event: Google Calendar event dict

        Returns:
            CalendarEvent object
        """
        # Parse start and end times
        start = event["start"].get("dateTime", event["start"].get("date"))
        end = event["end"].get("dateTime", event["end"].get("date"))

        start_time = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(end.replace("Z", "+00:00"))

        # Extract metadata from extended properties
        metadata = {}
        if "extendedProperties" in event:
            metadata = event["extendedProperties"].get("private", {})

        return CalendarEvent(
            event_id=event["id"],
            summary=event.get("summary", ""),
            description=event.get("description"),
            start_time=start_time,
            end_time=end_time,
            location=event.get("location"),
            metadata=metadata,
        )

    @staticmethod
    def get_oauth_url(
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        state: Optional[str] = None,
    ) -> str:
        """
        Get OAuth authorization URL for Google Calendar.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
            state: State parameter for CSRF protection

        Returns:
            Authorization URL
        """
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=GoogleCalendarIntegration.SCOPES,
            redirect_uri=redirect_uri,
        )

        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=state,
            prompt="consent",
        )

        return auth_url

    @staticmethod
    async def exchange_code_for_tokens(
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> Dict[str, str]:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code from OAuth callback
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI

        Returns:
            Dictionary with access_token, refresh_token, etc.

        Raises:
            RuntimeError: If token exchange fails
        """
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                },
                scopes=GoogleCalendarIntegration.SCOPES,
                redirect_uri=redirect_uri,
            )

            flow.fetch_token(code=code)

            credentials = flow.credentials

            return {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
            }

        except Exception as e:
            logger.error(f"Failed to exchange code for tokens: {e}")
            raise RuntimeError(f"Token exchange failed: {e}")
