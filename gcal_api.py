```python
"""Google Calendar helper (stubbed for offline testing)"""

import datetime as dt
import os
import json
from typing import List, Dict
from config import CALENDAR_ID, TIMEZONE, SCOPES

# Attempt to import Google API client libraries
try:
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.errors import HttpError

    CRED_FILE = 'credentials.json'
    TOKEN_FILE = 'token.json'

    def _auth():
        """Authenticate and return the Google Calendar service."""
        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CRED_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())
        
        return build('calendar', 'v3', credentials=creds)

    _SERVICE = _auth()
except Exception as e:
    print('[warn] Google API not available, using mock service:', e)
    _SERVICE = None

def get_service():
    """Return the Google Calendar service instance."""
    return _SERVICE

def list_events(service, tmin: dt.datetime, tmax: dt.datetime, query: str = None, calendar_id: str = CALENDAR_ID) -> List[Dict]:
    """List events in the specified time range from the given calendar.

    Args:
        service: The Google Calendar service instance.
        tmin: The minimum time for the events.
        tmax: The maximum time for the events.
        query: Optional search query for filtering events.
        calendar_id: The ID of the calendar to list events from.

    Returns:
        A list of events.
    """
    if service is None:
        return []  # offline stub
    
    events = []
    page = None
    
    while True:
        resp = service.events().list(
            calendarId=calendar_id,
            timeMin=tmin.isoformat(),
            timeMax=tmax.isoformat(),
            singleEvents=True,
            orderBy='startTime',
            q=query,
            pageToken=page
        ).execute()
        
        events.extend(resp.get('items', []))
        page = resp.get('nextPageToken')
        
        if not page:
            break
    
    return events

def safe_list(service, cid: str, tmin: dt.datetime, tmax: dt.datetime, query: str = None) -> List[Dict]:
    """Safely list events from a calendar, handling exceptions.

    Args:
        service: The Google Calendar service instance.
        cid: The calendar ID to list events from.
        tmin: The minimum time for the events.
        tmax: The maximum time for the events.
        query: Optional search query for filtering events.

    Returns:
        A list of events or an empty list if an error occurs.
    """
    try:
        return list_events(service, tmin, tmax, query, cid)
    except Exception as e:
        print('[warn] skip calendar', cid, e)
        return []

def list_events_multi(service, cal_ids: List[str], tmin: dt.datetime, tmax: dt.datetime, query: str = None) -> List[Dict]:
    """List events from multiple calendars.

    Args:
        service: The Google Calendar service instance.
        cal_ids: A list of calendar IDs to list events from.
        tmin: The minimum time for the events.
        tmax: The maximum time for the events.
        query: Optional search query for filtering events.

    Returns:
        A list of events from all specified calendars.
    """
    out = []
    for cid in cal_ids:
        out.extend(safe_list(service, cid, tmin, tmax, query))
    return out

def update_event_time(service, ev_id: str, start_dt: dt.datetime, end_dt: dt.datetime,
                      color_id: str = None, description: str = None, calendar_id: str = CALENDAR_ID):
    """Update the time of an existing event.

    Args:
        service: The Google Calendar service instance.
        ev_id: The ID of the event to update.
        start_dt: The new start datetime for the event.
        end_dt: The new end datetime for the event.
        color_id: Optional color ID for the event.
        description: Optional description for the event.
        calendar_id: The ID of the calendar containing the event.
    """
    if service is None:
        return
    
    body = {
        "start": {"dateTime": start_dt.isoformat(), "timeZone": TIMEZONE},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": TIMEZONE}
    }
    
    if color_id:
        body["colorId"] = color_id
    if description is not None:
        body["description"] = description
    
    service.events().patch(calendarId=calendar_id, eventId=ev_id, body=body).execute()

def create_event(service, summary: str, start_dt: dt.datetime, end_dt: dt.datetime, color_id: str, description: str = '', calendar_id: str = CALENDAR_ID) -> Dict:
    """Create a new event in the calendar.

    Args:
        service: The Google Calendar service instance.
        summary: The summary of the event.
        start_dt: The start datetime for the event.
        end_dt: The end datetime for the event.
        color_id: The color ID for the event.
        description: Optional description for the event.
        calendar_id: The ID of the calendar to create the event in.

    Returns:
        The created event.
    """
    if service is None:
        return {"id": "offline"}
    
    body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": TIMEZONE},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": TIMEZONE},
        "colorId": color_id
    }
    
    return service.events().insert(calendarId=calendar_id, body=body).execute()
```