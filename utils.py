import re

def parse_tags(desc: str):
    """Zwraca słownik tagów #vendo, #time, #priority, #due, #done"""
    desc_low=desc.lower()
    tags={
        "vendo": "#vendo" in desc_low,
        "done":  "#done"  in desc_low,
        "priority": None,
        "time": None,
        "due": None,
    }
    m=re.search(r"#priority(\d+)", desc_low)
    if m: tags["priority"]=int(m.group(1))
    m=re.search(r"#time:?\s*(\d+(?:\.\d+)?h|\d+min)", desc_low)
    if m: tags["time"]=m.group(1)
    m=re.search(r"#due(\d{4}-\d{2}-\d{2})", desc_low)
    if m: tags["due"]=m.group(1)
    return tags

def round_minutes(minutes, slot=5):
    return ((minutes+slot-1)//slot)*slot