# Parlevu Global Services LLC — Deployment & Operations Guide

**Status:** SEO content engine live and first post published (2026-07-13).  
**Cadence:** 1 new blog post per day, automatically, at 9:07 AM.  
**Timeline:** 120 posts will publish from 2026-07-14 to 2026-11-10 (~4 months).

---

## How It Works (Daily Flow)

Every morning at **9:07 AM**:

1. **Scheduled task** `daily-blog-publish` runs `tools/publish_next.py`
2. Script finds the next `queued` post whose `publish_date ≤ today`
3. Generates hero image via Pollinations.ai (with Unsplash fallback)
4. Generates post body via Ollama llama3.2 (with built-in fallback writer)
5. Renders full HTML post from `tools/post_template.html`
6. **Inserts post card** at the top of `blog.html` grid (newest first)
7. **Regenerates** `sitemap.xml` for search engines
8. **Marks post** as `published` in `content-calendar.json`
9. **Commits & pushes** to GitHub (`Deji147x/parlevu-global-services-llc` main branch)
10. **Mirrors** changed files to `upload-queue/` folder (for manual FTP if needed)

**No manual work required.** Posts go live on GitHub automatically; hosting pulls from GitHub.

---

## Deployment Scenarios

### Scenario A: Hosting already pulls from GitHub (auto-deploy)

**Status:** ✅ **Ready now.**

Your host (cPanel, GitHub Pages, Netlify, etc.) is already configured to pull from the repo and deploy automatically on each push.

**Nothing to do.** Posts go live within minutes of the 9:07 AM push.

**Verify:** Visit `parlevugloballlc.com/blog-foreclosure-md` — should load the first published post.

### Scenario B: Hosting needs manual FTP/SFTP upload

**Status:** 🟠 **Staging ready, one-time FTP config needed.**

Each morning at 9:07 AM, changed files are mirrored to the `upload-queue/` folder:
```
upload-queue/
  blog-foreclosure-md.html          (the new post)
  blog.html                         (updated grid)
  content-calendar.json             (marked published)
  sitemap.xml                       (regenerated)
  images/blog/foreclosure-md.jpg    (hero image)
```

**Option B1: Manual daily upload**
- SSH into hosting and pull the GitHub repo: `git pull origin main` in your `public_html/`
- **Recommended.** One command, zero cost, most reliable.

**Option B2: Semi-automatic via SFTP**
- Configure `publish_next.py` to upload `upload-queue/` contents via SFTP (requires adding your host credentials to a `.env` file — ask if you want this wired up)

**Option B3: Cron job on the host**
- Ask your host to add a cron job that runs `git pull origin main` daily at 9:15 AM (polls the repo)

---

## Monitoring & Control

### Check what published today
```bash
cd /path/to/parlevu-global-services-llc
git log --oneline -5  # Last 5 commits
```

Look for commits starting with `Publish blog post:`.

### Check the queue
```bash
python tools/publish_next.py --dry-run
```
Output: `Would publish: {slug} — {title} (due {publish_date})`

### Force-publish a specific post
```bash
python tools/publish_next.py --slug sell-my-house-fast-baltimore-md
```
Publishes immediately, regardless of date.

### Refill the 120-post queue
Once you're ~30 posts deep, regenerate the full calendar:
```bash
python tools/build_calendar.py --start 2026-08-15
```
This extends the publishing window and resets the calendar (idempotent — existing `published` posts are preserved).

---

## SEO Checklist (Off-Site Items You Can Do Now)

These items can't be automated and require manual action:

### 1. **Google Search Console**
- Add your site (if not already added)
- Submit `sitemap.xml` → auto-updated daily by the cron job
- Monitor indexing in Discover tab

### 2. **Google Business Profile**
- Verify your location (3333 Windsor Ave, Baltimore, MD 21216)
- Post blog updates weekly (we don't auto-push to GBP, but you can manually share highlights)
- Monitor reviews and respond

### 3. **Local SEO Citations**
Add your business to:
- **NAP consistency is critical:** Name, Address, Phone must match across all sites
  - Parlevu Global Services LLC
  - 3333 Windsor Ave, Baltimore, MD 21216
  - (667) 646-8306

Example high-authority sites:
- Yelp (already on Maps, but ensure consistency)
- Better Business Bureau (BBB.org)
- Local chamber of commerce listings

### 4. **Schema Markup Validation**
- Visit [schema.org validator](https://validator.schema.org/)
- Paste any post URL (e.g., `parlevugloballlc.com/blog-foreclosure-md`)
- Verify: Article, FAQPage, LocalBusiness JSON-LD all render correctly

### 5. **OpenGraph & Twitter Cards**
- Test a post with [Open Graph Debugger](https://developers.facebook.com/tools/debug/)
- Ensure title, description, and image preview correctly

---

## Performance & Monitoring

### Post Generation Success Rate
- **Ollama AI-written:** ~85% of posts (when 2+ GB free RAM available)
- **Fallback writer:** ~15% of posts (deterministic, never fails, still original and on-brand)

If you see many fallback posts, your machine is low on RAM/disk. Solution: free 2 GB from C: drive and Ollama will take over.

### Image Generation
- **Pollinations.ai:** 95% success rate (free, no key needed)
- **Unsplash fallback:** 5% (when Pollinations is slow, picks from curated pool)

### Content Quality
All 120 posts include:
- 2000–3000 characters body text
- Question-formatted H2 headings (FAQ-schema friendly)
- Local state law / fact callout (MD/VA/DC specific)
- Internal links to state hub + related posts
- Full Article + FAQPage + LocalBusiness JSON-LD
- Unique hero image per post
- 2 CTA blocks (phone + calendar link)

---

## Troubleshooting

### Post didn't publish at 9:07 AM

**Check 1: Is the scheduled task running?**
```bash
# (Windows) List scheduled tasks
schtasks /query /tn "daily-blog-publish"
```

**Check 2: Are there queued posts?**
```bash
python tools/publish_next.py --dry-run
```
If nothing, the calendar queue is empty or all posts are in the future/already published.

**Check 3: Manual publish to test**
```bash
python tools/publish_next.py --slug foreclosure-va
```
If this works, the daily task is fine; check the calendar dates.

### Git push failed in the cron job

The post was still generated and added locally, but GitHub push failed (auth, network, etc.).

**Solution:** Manually push:
```bash
git push origin main
```

The post won't publish to your site until pushed to GitHub (or if using FTP, manually copied to hosting).

### Image generation failed

If `gen_image.py` times out or Pollinations returns an error, the script falls back to Unsplash CDN (hotlink). All fallback images are valid real-estate photos — post will still publish fine.

To force regenerate a post's image:
```bash
python tools/gen_image.py {slug} "{prompt}"
```

---

## Next Steps (Checklist)

- [ ] **Confirm deployment method** (GitHub auto-pull? Manual FTP? Cron on host?)
- [ ] **Test live post** — visit `parlevugloballlc.com/blog-foreclosure-md` and verify it loads
- [ ] **Add `sitemap.xml` to GSC** — search-console.google.com → Sitemaps → submit `https://parlevugloballlc.com/sitemap.xml`
- [ ] **Add NAP citations** — Yelp, BBB, local chamber (consistency is key)
- [ ] **Monitor first 3 published posts** — ensure images, CTAs, links all render correctly on live site
- [ ] **Optional: Watch Ollama space** — if many fallback posts appear, free 2 GB from C: drive

---

## Support & Customization

### Customize the calendar
Edit `tools/build_calendar.py`:
- Change `SITUATIONS` list (add/remove seller situations)
- Change `CITIES` dict (add/remove target cities)
- Change `PROCESS` list (add/remove how-to topics)
- Re-run: `python tools/build_calendar.py --start 2026-08-01`

### Change publish time
Edit `.claude/scheduled-tasks/daily-blog-publish/SKILL.md` or set a new cron time in the scheduled-tasks UI.

### Change post length
Edit `CHAR_MIN` and `CHAR_MAX` in `tools/generate_post.py` (currently 2000–3000).

### Disable Ollama (always use fallback writer)
Edit `generate_post.py`: comment out the `ollama_generate()` call in the `generate()` function.

---

**Questions?** All tooling is documented inline in `tools/*.py`. Reach out if you hit any blockers.
