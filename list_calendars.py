```python
# list_calendars.py

from __future__ import print_function
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Zakresy uprawnień do odczytu kalendarza
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Nazwy plików z danymi uwierzytelniającymi
CRED_FILE = "credentials.json"  # Plik z Google Cloud
TOKEN_FILE = "token.json"        # Plik z tokenem, zapisany po pierwszym uruchomieniu

def get_service():
    """Uzyskuje usługę API kalendarza Google.

    Sprawdza, czy istnieje zapisany token uwierzytelniający. Jeśli nie, przeprowadza
    proces logowania i zapisuje nowy token.

    Returns:
        googleapiclient.discovery.Resource: Zbudowana usługa API kalendarza.
    """
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Sprawdzenie ważności tokenu
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CRED_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Zapisanie tokenu do pliku
        with open(TOKEN_FILE, "w") as token_file:
            token_file.write(creds.to_json())
    
    return build("calendar", "v3", credentials=creds)

def main():
    """Główna funkcja programu, która wyświetla listę kalendarzy użytkownika."""
    service = get_service()
    calendars = service.calendarList().list().execute().get("items", [])
    
    # Wyświetlenie kalendarzy
    for cal in calendars:
        summary = cal.get("summary")
        cal_id = cal.get("id")
        primary = cal.get("primary", False)
        print(f"{'*' if primary else ' '} {summary:30s}  →  {cal_id}")

if __name__ == "__main__":
    main()
```