"""Publish the next due post from content-calendar.json.

Daily cron flow:
  1. Find the first queued post whose publish_date <= today.
  2. Generate its hero image (Pollinations) and content (Ollama/fallback).
  3. Write blog-{slug}.html, insert its card at the top of the blog.html grid.
  4. Regenerate sitemap.xml.
  5. Mark the calendar entry published.
  6. git add/commit/push (unless --no-push), and mirror changed files into
     upload-queue/ for hosts that need manual/FTP upload.

Reusable: refill the queue any time with tools/build_calendar.py.

Usage:  python tools/publish_next.py [--dry-run] [--no-push] [--slug SLUG]
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CAL = REPO / "content-calendar.json"
BLOG = REPO / "blog.html"
SITE = "https://www.parlevugloballlc.com"
UPLOAD_QUEUE = REPO / "upload-queue"

sys.path.insert(0, str(REPO / "tools"))
from gen_image import generate as gen_img          # noqa: E402
from generate_post import generate as gen_post, place_of  # noqa: E402


def pick_next(cal, slug=None):
    today = date.today().isoformat()
    for p in cal["posts"]:
        if slug and p["slug"] == slug:
            return p
        if not slug and p["status"] == "queued" and p["publish_date"] <= today:
            return p
    return None


def insert_blog_card(brief, hero_img):
    """Insert the new post's card right after the blog grid opens."""
    html = BLOG.read_text(encoding="utf-8")
    marker = '<div class="blog-grid">'
    if marker not in html:
        raise RuntimeError("blog-grid marker not found in blog.html")
    img_src = hero_img if hero_img.startswith("http") else hero_img
    date_human = date.today().strftime("%B %d, %Y").replace(" 0", " ")
    place = place_of(brief)
    card = f'''<div class="blog-grid">

      <!-- Post: {brief['slug']} (auto-published {date.today().isoformat()}) -->
      <div class="blog-card reveal">
        <div class="blog-card-image">
          <img decoding="async" src="{img_src}" alt="{brief['primary_keyword']} — {place}" loading="lazy" width="600" height="185"/>
        </div>
        <div class="blog-card-body">
          <div class="blog-meta">
            <span class="blog-cat">{brief['category']}</span>
            <span class="blog-date">{date_human}</span>
          </div>
          <h3>{brief['title']}</h3>
          <p>Practical guidance for {place} homeowners — what to know, what it costs, and how to sell fast for cash with no repairs or fees.</p>
          <a href="blog-{brief['slug']}.html" class="blog-more">Read More →</a>
        </div>
      </div>'''
    BLOG.write_text(html.replace(marker, card, 1), encoding="utf-8")


def regen_sitemap():
    skip = {"404.html", "thank-you.html"}
    urls = sorted(p.name for p in REPO.glob("*.html") if p.name not in skip)
    today = date.today().isoformat()
    entries = "\n".join(
        f"  <url><loc>{SITE}/{u}</loc><lastmod>{today}</lastmod>"
        f"<changefreq>{'daily' if u == 'blog.html' else 'monthly'}</changefreq>"
        f"<priority>{'1.0' if u == 'index.html' else '0.7'}</priority></url>"
        for u in urls)
    (REPO / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n</urlset>\n", encoding="utf-8")


def git(*args, check=True):
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True, check=check)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report what would publish, change nothing")
    ap.add_argument("--no-push", action="store_true", help="commit locally but do not push")
    ap.add_argument("--slug", help="publish a specific slug regardless of date")
    args = ap.parse_args()

    cal = json.loads(CAL.read_text(encoding="utf-8"))
    brief = pick_next(cal, args.slug)
    if not brief:
        print("Nothing due today — queue empty or all future-dated. "
              "Refill with tools/build_calendar.py.")
        return
    if args.dry_run:
        print(f"Would publish: {brief['slug']} — {brief['title']} "
              f"(due {brief['publish_date']})")
        return

    print(f"Publishing: {brief['slug']} — {brief['title']}")
    hero = gen_img(brief["slug"], brief["image_prompt"])
    out = gen_post(brief["slug"], hero_img=hero)
    insert_blog_card(brief, hero)
    regen_sitemap()

    brief["status"] = "published"
    brief["published_on"] = date.today().isoformat()
    CAL.write_text(json.dumps(cal, indent=2), encoding="utf-8")

    # mirror for manual-upload hosting
    UPLOAD_QUEUE.mkdir(exist_ok=True)
    for f in [out, BLOG, REPO / "sitemap.xml", CAL]:
        shutil.copy2(f, UPLOAD_QUEUE / f.name)
    if not hero.startswith("http"):
        (UPLOAD_QUEUE / "images" / "blog").mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / hero, UPLOAD_QUEUE / hero)

    git("add", "-A")
    git("commit", "-m", f"Publish blog post: {brief['title']}")
    if not args.no_push:
        r = git("push", check=False)
        if r.returncode != 0:
            print(f"WARNING: git push failed:\n{r.stderr}\n"
                  "Post is committed locally; push manually or fix remote auth.")
    print(f"Done. Live file: {out.name}  |  upload-queue/ refreshed.")


if __name__ == "__main__":
    main()
