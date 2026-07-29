#!/usr/bin/env python3
import json
from datetime import date
today = date.today().isoformat()
cal = json.loads(open('content-calendar.json').read())
due = [p for p in cal['posts'] if p.get('publish_date') == today]
print(f'Due today ({today}): {len(due)} posts')
for p in due[:5]:
    status = p.get('status', 'unknown')
    title = p['title'][:60]
    print(f'  [{status}] {p["slug"]}: {title}')
