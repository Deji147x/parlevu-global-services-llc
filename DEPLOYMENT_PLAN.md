# Parlevu Global Services — Content Engine Deployment Plan

**Date:** 2026-07-13  
**Live URLs:** https://github.com/Deji147x/parlevu-global-services-llc (main branch)

---

## What's Live Right Now

### 120-Post Scheduled Queue
- **Status:** Active
- **Cadence:** 1 post/day starting 2026-07-14 (tomorrow at 9:07 AM)
- **Automation:** Scheduled task `daily-blog-publish` runs at 9:07 AM daily via Claude Code
- **What it does:** Picks next queued post → generates content + image → updates blog.html grid → commits + pushes to GitHub
- **Duration:** 120 days (4 months), ending 2026-11-10

### 8 High-Value DMV Batch Posts (Published Today)
- **We Buy Houses Baltimore Fast**
- **Cash Offer Baltimore Maryland**
- **Cash Home Buyers DC**
- **Sell House Arlington Virginia**
- **Baltimore House Buyers (Any Condition)**
- **Sell House Fast Alexandria**
- **Sell Inherited House Maryland**
- **Fair Cash Offer DC Distressed**

Each post includes:
- ✅ Original Parlevu voice (direct, no-fluff, action-oriented)
- ✅ Unique Pollinations.ai images (1200×630, relevant to topic)
- ✅ Deep SEO keywords (primary + 3 secondary each)
- ✅ Article + FAQPage + LocalBusiness JSON-LD schema
- ✅ CTA: calendar link + "Book a Free Consultation" button
- ✅ Internal links: to services, about, contact
- ✅ Social footer: Facebook, Instagram, LinkedIn, X, Pinterest
- ✅ Local state facts: MD/VA/DC disclosure rules, foreclosure timelines, tax implications

---

## Deployment Checklist

### Phase 1: Website Syncing (If not auto-deployed)
- [ ] **Confirm how the live site pulls updates:**
  - Option A: cPanel Git auto-pull from GitHub (most likely)
  - Option B: Manual FTP upload from upload-queue/
  - Option C: GitHub Actions webhook → auto-deploy
  - **Action:** Verify which method your hosting uses. If auto-pull enabled, no action needed. If manual, download files from `upload-queue/` via FTP weekly.

### Phase 2: Google My Business (GMB) Posts
- [ ] **Post to GMB within 48 hours of blog publish for maximum freshness signal**
  - Use **GMB_DEPLOYMENT_GUIDE.md** (3 options: manual, CSV, or API)
  - Priority order in guide (highest local intent first)
  - Posts show in Google Search 3-pack + business card
  - Recommended: Post 2-3 per week to keep feed active

### Phase 3: Search Console & Sitemap
- [ ] **Submit sitemap.xml to Google Search Console**
  - URL: https://www.parlevugloballlc.com/sitemap.xml
  - Sitemap auto-regenerates daily via `publish_next.py`
  - Already includes all 120 posts as they're published

### Phase 4: Schema Validation
- [ ] **Validate JSON-LD schema on a sample post**
  - Use https://schema.org/validator
  - Check: Article, FAQPage, LocalBusiness markup
  - Should all be green ✓

### Phase 5: Ongoing Monitoring
- [ ] **Google Analytics 4:** Track which blog posts drive sessions and conversions
- [ ] **Search Console:** Monitor new blog URLs for indexing status (should see 1 new URL/day)
- [ ] **Organic rankings:** Use Ahrefs or free tools to track keyword positions (posts target long-tail, should rank within 2-3 weeks)

---

## Content Calendar

### Tomorrow (2026-07-14)
- **9:07 AM:** Cron publishes `inherited-probate-md.html`
- **Manual:** Post to GMB (if doing manual sync)

### Week 1 (2026-07-14 to 2026-07-20)
- Publish: 7 posts (balanced MD/VA/DC)
- Categories: Inherited property, foreclosure, process guides
- GMB sync: Post 2-3 to GMB (optional but recommended)

### Month 1 (July full month)
- Publish: 31 posts
- All major seller situations covered (inherited, foreclosure, divorce, liens, fire/water, hoarder, etc.)
- Expected: first Google rankings for long-tail keywords by end of month

### Month 2-4 (Aug-Oct)
- Publish: 89 remaining posts
- City pages, comparisons, market updates
- Expected: organic traffic climb as posts age and accumulate backlinks

---

## Key URLs

| Resource | URL |
|----------|-----|
| **Website** | https://www.parlevugloballlc.com |
| **GitHub Repo** | https://github.com/Deji147x/parlevu-global-services-llc |
| **Blog Index** | /blog.html (links to all 128 posts: 7 existing + 120 scheduled + 8 DMV batch + 3 hub pages) |
| **State Hubs** | /sell-house-fast-maryland.html, /-virginia.html, /-washington-dc.html |
| **Sitemap** | /sitemap.xml (regenerated daily) |
| **Google My Business** | https://business.google.com (manual post entry point) |
| **Search Console** | https://search.google.com/search-console (for indexing monitoring) |

---

## Tech Stack

| Component | Tool | Notes |
|-----------|------|-------|
| **Content Authoring** | Claude AI (Sonnet 5) + Ollama llama3.2 fallback | Original writing, no plagiarism |
| **Image Generation** | Pollinations.ai API (free, no key) + Unsplash fallback | 1200×630 JPEGs, unique per post |
| **Publishing** | Python scripts (publish_next.py) | Automated via daily cron |
| **Scheduling** | Claude Code scheduled-tasks (daily at 9:07 AM) | No external dependencies |
| **Version Control** | GitHub (Deji147x/parlevu-global-services-llc) | All posts + config tracked |
| **Hosting** | Apache (parlevugloballlc.com) | Static HTML, .htaccess rules (HTTPS, cache, etc.) |

---

## Reusable (Non-Destructive)

All scripts are **reusable and idempotent:**

- **Refill the queue:** `python tools/build_calendar.py --start 2026-11-11` generates new 120-post batch
- **Regenerate hubs:** `python tools/build_hubs.py` (overwrites state hub pages safely)
- **Dry-run next publish:** `python tools/publish_next.py --dry-run` (no changes)
- **Force publish specific post:** `python tools/publish_next.py --slug foreclosure-va` (publish out of schedule)

---

## Metrics to Track (30, 60, 90 days)

### Google Search Console
- Impressions (how many times you show in search results)
- CTR (click-through rate)
- Average position (where you rank)
- Clicks to your site

### Google Analytics 4
- Sessions from organic search
- Pages/session (blog engagement)
- Conversion rate (visitors → leads via contact form or call)

### Target KPIs
- **By day 30:** 10-20 posts ranked in Google top 100 (any position)
- **By day 60:** 5-10 posts in top 50 (positions 1-50)
- **By day 90:** 20-30 posts in top 20 for their target keywords

---

## What to Do If Something Breaks

**Cron not publishing posts at 9:07 AM?**
- Check Claude Code scheduled-tasks list: `daily-blog-publish` should show "enabled" and next run time
- Manually trigger: `python tools/publish_next.py` (will publish the due post immediately)
- Reschedule: Edit the scheduled task to pick a new time if 9:07 AM doesn't fit

**Images not loading on published posts?**
- Pollinations.ai API intermittently times out; fallback uses Unsplash stock
- Check `images/blog/` folder for the image file
- If missing, regenerate: `python tools/gen_image.py <slug> "<prompt>"`

**Blog.html grid not updating?**
- Manually run: `python tools/publish_next.py --slug <slug>` to force republish
- Verify `blog.html` was committed to GitHub

**Posts not ranking in Google after 2-3 weeks?**
- Check Search Console → Coverage → ensure posts are "Indexed"
- If not indexed: submit sitemap.xml or request indexing for specific URLs
- Check for robots.txt blocks (ours allows everything except /upload-queue/ and /tools/)

---

## Success Criteria (3-Month View)

✅ **120 blog posts live on parlevugloballlc.com**  
✅ **~30 posts ranked on first page of Google for target keywords**  
✅ **Organic traffic to blog increases by 300-500%**  
✅ **Contact form submissions increase (trackable in GA4)**  
✅ **GMB profile stays active with 2-3 new posts/week**  
✅ **No manual content creation required (fully automated daily)**

---

## Questions? Next Steps

1. **Verify hosting deployment:** Confirm if GitHub auto-pulls or needs manual FTP
2. **Set GMB reminder:** Post 2-3 DMV batch posts to GMB this week
3. **Monitor:** Check Search Console and GA4 weekly starting next Monday
4. **Scale:** After month 1, optionally add more thematic batches (divorce sales, probate, etc.)

**Contact:** deji47.ajishe@gmail.com
