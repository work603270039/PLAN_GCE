import logger
    run_id = logger.new_run_id()
    trace = [f"run {run_id} start",
             f"list_events => {len(all_ev)} ev",
import datetime as dt, pytz
from collections import defaultdict
    logger.log_run_snapshot("snapshot_before", {"run": run_id, "events": snap_before})
    logger.log_run_snapshot("actions",        {"run": run_id, "list": actions})
    logger.log_run_snapshot("snapshot_after", {"run": run_id, "events": snap_after})
    logger.log_run_snapshot("trace",          {"run": run_id, "steps": trace})
    logger.log_run_snapshot("plan",           {"run": run_id, **plan})
    print(f"[run {run_id}] Akcje: {len(actions)}")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logger.LOGGER.exception("fatal error", {"error": str(e)})
        raise

```
from gcal_api import get_service, list_events, list_events_multi, update_event_time, create_event
from utils import parse_tags
from vendo_api import save_snapshot
from scheduler import schedule

tz=pytz.timezone(TIMEZONE)
iso_dt=dt.datetime.fromisoformat

def range_dates(b,f):
    today=dt.date.today()
    return today-dt.timedelta(days=b), today+dt.timedelta(days=f)

def tasks_from_events(events):
    tasks=[]
    for ev in events:
        desc=ev.get('description','') or ''
        tags=parse_tags(desc)
        if not tags['vendo']: continue
        tasks.append({
            **tags,
            'event_id':ev.get('id'),
            'summary':ev.get('summary',''),
            'description':desc,
            'start': ev['start'].get('dateTime'),
            'end':   ev['end'].get('dateTime')
        })
    return tasks

def run():
    svc=get_service()
    start,end=range_dates(LOG_BACK_DAYS,LOG_FORWARD_DAYS)
    tmin=tz.localize(dt.datetime.combine(start, dt.time.min))
    tmax=tz.localize(dt.datetime.combine(end, dt.time.max))

    all_ev=list_events(svc,tmin,tmax)
    vendo=[e for e in all_ev if '#vendo' in ((e.get('description') or '').lower())]
    other_events=list_events_multi(svc,BUSY_CALENDARS,tmin,tmax)
    others=[e for e in other_events if '#vendo' not in ((e.get('description') or '').lower())]

    tasks=tasks_from_events(vendo)
    save_snapshot(tasks)

    busy=defaultdict(list)  # dummy
    scheduled,_=schedule(tasks,busy)

    actions=[]
    for t,s,e in scheduled:
        print('Would schedule',t['summary'],s,'-',e)
    logger.write_run_log([],actions,[])
    print('Done')

if __name__=='__main__':
    run()
    
    
    
setx OPENAI_API_KEY "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" /M
