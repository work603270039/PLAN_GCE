import datetime as dt, pytz
from utils import round_minutes
from collections import defaultdict

tz=pytz.timezone("Europe/Warsaw")

def schedule(tasks, busy):
    """Bardzo prosty scheduler: idzie dzień po dniu 8-16 slot 5 min"""
    scheduled=[]
    late=0
    cur=tz.localize(dt.datetime.combine(dt.date.today(), dt.time(8)))
    for t in tasks:
        duration=60  # default 1h
        s=cur
        e=s+dt.timedelta(minutes=duration)
        scheduled.append((t,s,e))
        cur=e
    return scheduled, late