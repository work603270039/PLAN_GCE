from datetime import datetime, timedelta, timezone
from gcal_api import get_service, list_events

svc = get_service()
tz  = timezone.utc            # możesz użyć lokalnej Europe/Warsaw

time_min = datetime.now(tz)
time_max = time_min + timedelta(days=2)

events = list_events(svc, time_min, time_max,
                     calendar_id="ecadwojtczak@gmail.com")

print("Zdarzeń:", len(events))
for e in events:
    print("-", e["summary"],
          e["start"].get("dateTime") or e["start"].get("date"))
