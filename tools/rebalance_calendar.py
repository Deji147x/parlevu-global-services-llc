#!/usr/bin/env python3
"""Even out the queue: fill empty slots from days carrying surplus posts.

publish_next.py takes ONE post per run whose status is queued and whose
publish_date is on or before today. So a date holding three posts does not
publish three -- it publishes one and the surplus silently shifts everything
behind it later, while an empty date breaks the daily cadence outright.

This moves surplus posts into empty slots. It only rewrites publish_date,
which memory records as a queue position rather than a real publication date
(published_on is the real one, stamped at publish time). No content changes,
no status changes, and a .bak is written first.
"""
import json, shutil, sys
from collections import Counter, defaultdict
from datetime import date, timedelta
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CAL = 'content-calendar.json'
START, END = date(2026, 9, 1), date(2026, 12, 12)

shutil.copy(CAL, CAL + '.bak')
doc = json.load(open(CAL, encoding='utf-8'))
rows = doc['posts'] if isinstance(doc, dict) else doc

# The wrapper documents cadence as "1-2 posts/day (service posts) Oct 27 - ...",
# so dates carrying two posts are intentional and must be left alone. Only
# dates carrying THREE are surplus, and only down to two.
q = [r for r in rows if r.get('status') == 'queued']


def slot(r):
    return str(r.get('publish_date'))[:10]


counts = Counter(slot(r) for r in q)
have = set(counts)

empty = []
cur = START
while cur <= END:
    if cur.isoformat() not in have:
        empty.append(cur.isoformat())
    cur += timedelta(days=1)

# Surplus is only the THIRD post on a date -- two per day is the stated
# cadence and stays untouched. Latest dates are raided first so the near-term
# schedule is disturbed as little as possible.
by_date = defaultdict(list)
for r in q:
    by_date[slot(r)].append(r)
surplus = []
for d in sorted(by_date, reverse=True):
    surplus.extend(by_date[d][2:])

print('queued posts   : %d' % len(q))
print('empty slots    : %d  %s' % (len(empty), ', '.join(empty[:6])))
print('surplus posts  : %d  (on %d overloaded dates)'
      % (len(surplus), sum(1 for d, n in counts.items() if n > 1)))
print()

moved = 0
for tgt in empty:
    if not surplus:
        break
    r = surplus.pop(0)
    old = slot(r)
    r['publish_date'] = tgt
    moved += 1
    print('  %s -> %s   %s' % (old, tgt, str(r.get('primary_keyword'))[:46]))

json.dump(doc, open(CAL, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

# verify
rows2 = doc['posts'] if isinstance(doc, dict) else doc
q2 = [r for r in rows2 if r.get('status') == 'queued']
c2 = Counter(str(r.get('publish_date'))[:10] for r in q2)
still_empty = []
cur = START
while cur <= END:
    if cur.isoformat() not in c2:
        still_empty.append(cur.isoformat())
    cur += timedelta(days=1)

print('\nmoved %d post(s)' % moved)
print('empty slots remaining : %d' % len(still_empty))
print('dates with 3+ posts    : %d  (2/day is intended)' % sum(1 for n in c2.values() if n > 2))
print('queued total unchanged: %s' % (len(q2) == len(q)))
print('.bak written to %s.bak' % CAL)
