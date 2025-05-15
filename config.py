```python
"""Global settings for the application."""

# Timezone setting
TIMEZONE = "Europe/Warsaw"

# OAuth scope for full access to Google Calendar
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Color codes for task statuses
COLOR_OVERDUE = "11"  # Color for overdue tasks
COLOR_DONE = "8"      # Color for completed tasks
COLOR_NORMAL = "5"    # Color for normal tasks

# Log horizon settings
LOG_BACK_DAYS = 10    # Number of days to look back in logs
LOG_FORWARD_DAYS = 20  # Number of days to look forward in logs

# Number of days to freeze manually arranged vendor tasks
FREEZE_DAYS = 1

# List of calendars that block time slots
BUSY_CALENDARS = [
    "primary",
    "work603270039@gmail.com",
    "ecadwojtczak@gmail.com"
]

# Default calendar ID for saving vendor tasks
CALENDAR_ID = "primary"
```