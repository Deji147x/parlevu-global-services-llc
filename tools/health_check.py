"""Report whether the publishing pipeline is actually healthy.

Every failure this repo has hit was already recorded somewhere - a WARNING in a
run log, a missing log file, a commit that never left the machine. The problem
was never missing information, it was that nobody reads logs daily. This prints
one summary and exits non-zero when something needs attention, so it can be
scheduled or glanced at.

Usage:  python tools/health_check.py [--days 14]
Exit:   0 all clear, 1 one or more problems found
"""
import argparse
import datetime
import glob
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOGS = REPO / "logs"
TASK = "Parlevu-PublishNext"

OK, WARN, BAD = "ok", "warn", "PROBLEM"


def git(*args):
    r = subprocess.run(["git", "-C", str(REPO), *args],
                       capture_output=True, text=True)
    return r.stdout.strip()


def powershell(script):
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", script],
                           capture_output=True, text=True, timeout=60)
        return r.stdout.strip()
    except Exception:
        return ""


def check_task():
    """Scheduled task: did it run, did it succeed, will it catch up."""
    out = powershell(
        "$i=Get-ScheduledTaskInfo -TaskName '%s';"
        "$t=Get-ScheduledTask -TaskName '%s';"
        "Write-Output ($i.LastRunTime.ToString('yyyy-MM-dd HH:mm'));"
        "Write-Output $i.LastTaskResult;"
        "Write-Output $t.Settings.StartWhenAvailable" % (TASK, TASK))
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    if len(lines) < 3:
        return [(WARN, "scheduled task", "could not read task state")]
    last, result, swa = lines[0], lines[1], lines[2].lower()
    rows = []
    rows.append((OK if result == "0" else BAD,
                 "last run", "%s (result %s)" % (last, result)))
    rows.append((OK if swa == "true" else BAD, "StartWhenAvailable",
                 swa + ("" if swa == "true" else " - a missed morning is skipped, not caught up")))
    return rows


def check_logs(days):
    """Missing run logs, push failures, engine and image fallbacks."""
    today = datetime.date.today()
    window = [today - datetime.timedelta(days=i) for i in range(days)]
    missing = [d.isoformat() for d in window
               if not (LOGS / ("publish-%s.log" % d.isoformat())).exists()]
    text = ""
    last_push_fail = None
    for d in window:
        f = LOGS / ("publish-%s.log" % d.isoformat())
        if not f.exists():
            continue
        body = io.open(f, encoding="utf-8", errors="replace").read()
        text += body
        if "git push failed" in body:
            if last_push_fail is None or d > last_push_fail:
                last_push_fail = d
    push_fail = text.count("git push failed")
    fallback = len(re.findall(r"fallback engine", text))
    ollama = len(re.findall(r"ollama engine", text))
    img = text.count("IMAGE FALLBACK")

    # A count alone cries wolf: failures already fixed keep reporting until they
    # age out of the window. What matters is whether one happened recently.
    if not push_fail:
        push_row = (OK, "push failures", "none in last %d days" % days)
    else:
        age = (today - last_push_fail).days
        detail = "%d in last %d days, most recent %s (%s)" % (
            push_fail, days, last_push_fail.isoformat(),
            "today" if age == 0 else "%d days ago" % age)
        push_row = (BAD if age <= 2 else WARN, "push failures", detail)

    rows = [
        push_row,
        (WARN if missing else OK, "days with no run",
         ", ".join(missing) if missing else "none"),
        (WARN if fallback else OK, "template-written posts",
         "%d of %d (Ollama wrote %d)" % (fallback, fallback + ollama, ollama)),
        (WARN if img else OK, "stock-image fallbacks", str(img)),
    ]
    return rows


def check_git():
    git("fetch", "github")
    ahead = git("rev-list", "--count", "github/main..HEAD") or "0"
    dirty = len([l for l in git("status", "--porcelain").splitlines() if l.strip()])
    return [
        (BAD if ahead != "0" else OK, "unpushed commits",
         ahead + (" - not live" if ahead != "0" else "")),
        (WARN if dirty else OK, "uncommitted files", str(dirty)),
    ]


def check_queue():
    cal = json.load(io.open(REPO / "content-calendar.json", encoding="utf-8"))
    today = datetime.date.today().isoformat()
    queued = [p for p in cal["posts"] if p.get("status") == "queued"]
    overdue = [p for p in queued if p["publish_date"] <= today]
    runway = max((p["publish_date"] for p in queued), default="-")
    soon = (datetime.date.fromisoformat(runway) - datetime.date.today()).days if queued else 0
    return [
        (WARN if overdue else OK, "overdue posts",
         "%d%s" % (len(overdue), " (" + overdue[0]["slug"] + " oldest)" if overdue else "")),
        (WARN if soon < 21 else OK, "queue runway",
         "%d posts, through %s" % (len(queued), runway)),
    ]


def check_images():
    stock = []
    for f in glob.glob(str(REPO / "blog-*.html")):
        h = io.open(f, encoding="utf-8", errors="replace").read()
        if re.search(r'<img[^>]+src="https://images\.unsplash', h):
            stock.append(os.path.basename(f))
    return [(WARN if stock else OK, "posts on stock images",
             "%d%s" % (len(stock), " - run tools/backfill_images.py" if stock else ""))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14, help="log window to examine")
    args = ap.parse_args()

    rows = []
    for fn in (check_task, check_git, check_queue, check_images):
        rows += fn()
    rows += check_logs(args.days)

    print("Parlevu publishing health  -  %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("-" * 64)
    for state, label, detail in rows:
        mark = {OK: "  ok  ", WARN: " warn ", BAD: " FAIL "}[state]
        print("[%s] %-24s %s" % (mark, label, detail))
    print("-" * 64)

    problems = [r for r in rows if r[0] == BAD]
    warns = [r for r in rows if r[0] == WARN]
    if problems:
        print("%d problem(s) need attention: %s" % (len(problems), ", ".join(r[1] for r in problems)))
    elif warns:
        print("%d warning(s): %s" % (len(warns), ", ".join(r[1] for r in warns)))
    else:
        print("All clear.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
