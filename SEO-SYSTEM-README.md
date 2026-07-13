# Parlevu SEO Content Engine

Automated local-SEO blog system: 120 queued posts targeting Maryland, Virginia,
and Washington DC, published one per day by a scheduled task.

## How it works

```
content-calendar.json          120 post briefs (keyword, state/city, date, status)
        │
tools/publish_next.py          daily: picks the next due post, then →
├─ tools/gen_image.py          unique hero image (Pollinations.ai, free, no key;
│                              falls back to curated Unsplash URLs)
├─ tools/generate_post.py      post body (local Ollama llama3.2, free; falls back
│                              to a built-in original writer — never fails)
├─ inserts card into blog.html, regenerates sitemap.xml
└─ git commit + push, mirrors changed files to upload-queue/
```

Every post: 2000–3000 characters, question-style H2s, FAQ accordion,
Article + FAQPage + RealEstateAgent JSON-LD, mid-article + end CTAs
(phone, contact form, Book-a-Call), internal links to its state hub page.

Hub pages (silo tops): `sell-house-fast-maryland.html`, `-virginia.html`,
`-washington-dc.html`. Plus `sitemap.xml` + `robots.txt`.

## Daily cron

A Claude scheduled task (`daily-blog-publish`) runs at 9:00 AM and executes
`python -B tools/publish_next.py`. It runs while the Claude desktop app is
open; if the machine/app was off, it catches up on next launch (publish_next
publishes the oldest overdue post first — run it multiple times to catch up
fully).

## Common operations

| Do this | Command (from repo root) |
|---|---|
| Publish next due post now | `python -B tools/publish_next.py` |
| Preview what would publish | `python -B tools/publish_next.py --dry-run` |
| Publish a specific slug | `python -B tools/publish_next.py --slug foreclosure-md` |
| Publish without git push | `python -B tools/publish_next.py --no-push` |
| Regenerate one post's HTML | `python -B tools/generate_post.py <slug>` |
| Refill/extend the queue | edit topic lists in `tools/build_calendar.py`, then `python tools/build_calendar.py` (published entries are preserved) |
| Rebuild hub pages | `python tools/build_hubs.py` |

## Deployment last mile

`publish_next.py` pushes to GitHub AND copies changed files to `upload-queue/`.
If the live host (parlevugloballlc.com) doesn't auto-pull from GitHub, upload
the contents of `upload-queue/` via cPanel/FTP, then clear the folder.

## Content originality

Competitor sites were analyzed for topics/keywords only (see
`research/competitor-analysis.md`). All generated copy is original — Ollama
writes from a brief, and the fallback writer uses parameterized original text.
Nothing is copied from any competitor.

## Known constraints (2026-07-12)

- Ollama needs ~2 GB free RAM to load llama3.2; when the machine is
  memory-starved it returns HTTP 500 and the pipeline automatically uses the
  built-in writer. Free RAM/disk to get AI-written variety back.
- One-time off-site tasks still to do manually: submit sitemap.xml in Google
  Search Console, keep Google Business Profile active, build NAP citations.
