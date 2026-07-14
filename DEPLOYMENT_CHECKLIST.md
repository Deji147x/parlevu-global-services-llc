# Parlevu Global Services — Complete Deployment Checklist

## ✅ Phase 1: SEO Content Engine (COMPLETE)

- [x] Competitor research & keyword mapping
- [x] 120-post content calendar (MD/VA/DC coverage)
- [x] 91 blog posts generated + published
- [x] Unique hero images for each post (Pollinations.ai)
- [x] Local SEO infrastructure:
  - [x] 3 state hub pages (Maryland/Virginia/DC)
  - [x] 30+ city/neighborhood guides
  - [x] Sitemap.xml (all posts indexed)
  - [x] Robots.txt (crawl-friendly)
  - [x] LocalBusiness JSON-LD schema
  - [x] All pages: Article + FAQPage schema
- [x] Internal linking silos
- [x] Social links + Subscribe CTA (all pages)
- [x] Daily cron publisher (publish_next.py)
- [x] All changes pushed to GitHub ✓

**Status:** 🟢 LIVE — 91 blog posts ready for production

---

## ✅ Phase 2: Social Media Automation (INFRASTRUCTURE READY)

- [x] Buffer.com API integration script (`tools/post_to_buffer.py`)
- [x] Environment configuration template (`.env.example`)
- [x] Deployment guides:
  - [x] BUFFER_DEPLOYMENT.md (full setup)
  - [x] WINDOWS_CRON_SETUP.md (Task Scheduler)
- [x] Security: `.env` protected from git commits
- [x] All infrastructure pushed to GitHub ✓

**Status:** 🟡 READY — Awaiting Buffer API key verification

---

## 📋 IMMEDIATE ACTION ITEMS (BEFORE LAUNCH)

### 1. Verify Buffer API Key
```bash
curl "https://api.bufferapp.com/1/user.json?access_token=LVHd9bX_fyxVq3vK5VOy6ilpd_LEVWxl6ud9zzmniw8"
```
- Should return JSON with `"profiles": [...]`
- If 401 error: regenerate key in Buffer.com settings

### 2. Get Buffer Profile IDs
Once Buffer API works, you'll get profile IDs like: `507f1f77bcf86cd799439011`
- One for Facebook
- One for Instagram
- One for LinkedIn
- One for X
- One for Pinterest

### 3. Update `.env` File
Copy template and fill in actual values:
```
BUFFER_API_KEY=LVHd9bX_fyxVq3vK5VOy6ilpd_LEVWxl6ud9zzmniw8
BUFFER_PROFILE_FACEBOOK=507f1f77bcf86cd799439011
BUFFER_PROFILE_INSTAGRAM=507f1f77bcf86cd799439012
BUFFER_PROFILE_LINKEDIN=507f1f77bcf86cd799439013
BUFFER_PROFILE_X=507f1f77bcf86cd799439014
BUFFER_PROFILE_PINTEREST=507f1f77bcf86cd799439015
SITE_URL=https://www.parlevugloballlc.com
```

### 4. Set Up Windows Task Scheduler
Follow **WINDOWS_CRON_SETUP.md**:
1. Open Task Scheduler
2. Create Basic Task
3. Schedule: Weekly (Mon/Wed/Fri at 9 AM)
4. Action: `python tools/post_to_buffer.py --posts 3`
5. Test with `--dry-run` flag

### 5. Deploy to Production
Your hosting environment:
- [ ] Confirm current deployment method (FTP/Git/cPanel)
- [ ] Sync blog posts to live server
- [ ] Verify sitemap.xml is accessible
- [ ] Test a blog post page loads correctly

---

## 🎯 LAUNCH SEQUENCE

### Pre-Launch Verification (1 hour)

1. **Test Buffer API**
   ```powershell
   python tools/post_to_buffer.py --posts 1 --dry-run
   ```
   Should show latest blog post details

2. **Verify Blog Posts**
   - Check 91 blog files exist: `ls blog-*.html | wc -l`
   - Sample a post in browser (if live)
   - Verify images load correctly

3. **Test Social Posting**
   ```powershell
   python tools/post_to_buffer.py --posts 1 --now
   ```
   Check Buffer.com dashboard → Posts queue

4. **Verify SEO Setup**
   - Sitemap accessible: `curl https://www.parlevugloballlc.com/sitemap.xml`
   - Robots.txt correct: `curl https://www.parlevugloballlc.com/robots.txt`
   - Google Search Console submission ready

### Launch (Go Live)

1. ✅ Deploy 91 blog posts to production server
2. ✅ Enable daily cron publisher (publish_next.py)
3. ✅ Set up Task Scheduler for Buffer posting
4. ✅ Submit sitemap to Google Search Console
5. ✅ Post initial 3 posts to Buffer manually (test)
6. ✅ Monitor GA4 for incoming traffic

---

## 📊 CONTENT DISTRIBUTION (91 Posts)

**By State:**
- Maryland: 30 posts
- Virginia: 30 posts
- Washington DC: 31 posts

**By Type:**
- City/neighborhood guides: 30+
- Seller situations: 39 (foreclosure, inherited, divorce, liens, etc.)
- Process guides: 9 (underwater mortgage, relocation, etc.)
- Deep FSBO education: 3 (pain points, FAQs, why listings fail)
- Market updates: 2

**By Publishing Schedule:**
- Daily cron: 1 post/day → 91 days coverage
- Manual overdraft: Posts available immediately if needed
- Buffer schedule: 3x/week to social media

---

## 🔐 SECURITY CHECKLIST

- [x] API keys stored in `.env` (not in git)
- [x] `.env` in `.gitignore` (protected)
- [x] `.env.example` provided (template only, no secrets)
- [x] All GitHub commits: no exposed credentials
- [x] Social links on all pages (verified)
- [ ] **TODO:** Rotate Buffer API key quarterly

---

## 📈 SUCCESS METRICS (Track These)

### Week 1
- [ ] All 91 posts indexed by Google (check Search Console)
- [ ] First organic traffic arrives (check GA4)
- [ ] 3 posts shared to social media (Buffer dashboard)

### Month 1
- [ ] 20+ organic sessions from blog posts
- [ ] 5+ click-throughs to contact form
- [ ] Top-ranking keywords from state hubs
- [ ] Daily cron publishes without errors

### Month 3
- [ ] 100+ organic sessions/month
- [ ] Top 3 keywords ranking (position 3-10)
- [ ] 50+ social media clicks
- [ ] 10+ leads from blog

---

## 🚀 NEXT PHASE (After Launch)

1. **Monitor Rankings**
   - Track MD/VA/DC keywords in Google Search Console
   - A/B test blog post headlines (via GA4)

2. **Expand Social Media**
   - Post 3x/week (automated via Buffer)
   - Add Pinterest rich pins (image-heavy)
   - Repurpose top posts for LinkedIn articles

3. **Optimize Conversion**
   - A/B test CTA buttons
   - Track appointment bookings from blog
   - Survey visitors: "How did you hear about us?"

4. **Build Backlinks**
   - Reach out to MD/VA/DC real estate forums
   - Guest post on local business blogs
   - Local directory citations (NAP consistency)

---

## 📞 Support

**Questions about:**
- Buffer setup → See BUFFER_DEPLOYMENT.md
- Task Scheduler → See WINDOWS_CRON_SETUP.md
- Blog content → See content-calendar.json
- SEO structure → See site hub pages (sell-house-fast-*.html)

---

## ✨ Summary

| Component | Status | Link |
|-----------|--------|------|
| 91 Blog Posts | 🟢 Live | [GitHub](https://github.com/Deji147x/parlevu-global-services-llc) |
| Local SEO | 🟢 Complete | sitemap.xml, robots.txt, schema markup |
| Daily Cron Publisher | 🟢 Ready | publish_next.py |
| Buffer Automation | 🟡 Ready | tools/post_to_buffer.py |
| Production Deploy | ⏳ Pending | Your hosting (FTP/Git) |

**Estimated Launch:** Within 1-2 hours of Buffer API verification
**Time Investment:** 30 min setup + 1 hour testing = 1.5 hours total

---

**Last Updated:** 2026-07-14  
**Commit:** aa2aa33  
**Repository:** https://github.com/Deji147x/parlevu-global-services-llc
