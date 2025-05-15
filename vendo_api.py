import pathlib, json
SNAP_FILE=pathlib.Path('tasks.json')
def save_snapshot(tasks):
    SNAP_FILE.write_text(json.dumps(tasks, indent=2, ensure_ascii=False))