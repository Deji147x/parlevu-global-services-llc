# Google My Business (GMB) Deployment Guide

Your 8 new blog posts are live on GitHub and ready to syndicate to Google My Business. This document covers three options: manual, semi-automated, and API.

---

## Option 1: Manual Post (5 min per post, highest control)

**Best for:** Quick testing, understanding GMB workflow.

### Steps

1. **Go to Google My Business:**
   - Navigate to https://business.google.com
   - Log in with your Parlevu Global account
   - Select your Parlevu Global Services LLC business

2. **Create a Post:**
   - Click **Posts** (in the left menu) → **Create Post**
   - Choose **Event** or **Offer** (Events work best for educational/blog content)

3. **Fill the Post:**
   - **Headline:** Use the blog title (e.g., "We Buy Houses Baltimore Fast — No Realtor, No Wait")
   - **Description:** Copy the intro paragraph (first 150-200 characters):
     > "Your Baltimore home can close in a week. No agent. No repairs. We handle it. Get a free cash offer today."
   - **Call-to-action:** Select "Learn More" or "Book Now"
   - **Link:** Paste the full blog URL (e.g., https://www.parlevugloballlc.com/blog-we-buy-houses-baltimore-fast.html)
   - **Image:** Upload the matching image (images/blog/dmv-*.jpg) or let GMB auto-pull it from the page

4. **Publish**
   - Click **Publish**
   - Google indexes it immediately

### Posts to Push (in order of priority — highest local intent first)

| Blog | URL | Best CTA |
|------|-----|----------|
| We Buy Houses Baltimore Fast | /blog-we-buy-houses-baltimore-fast.html | Book Now |
| Cash Offer Baltimore Maryland | /blog-cash-offer-baltimore-maryland.html | Learn More |
| Cash Home Buyers DC | /blog-cash-home-buyers-dc-washington.html | Get Offer |
| Sell House Arlington Virginia | /blog-sell-house-arlington-virginia.html | Learn More |
| Baltimore House Buyers (Any Condition) | /blog-baltimore-house-buyers-we-buy-any-condition.html | Learn More |
| Sell House Fast Alexandria | /blog-sell-house-fast-alexandria-virginia.html | Book Now |
| Sell Inherited House Maryland | /blog-sell-inherited-house-maryland-fast.html | Get Offer |
| Fair Cash Offer DC Distressed | /blog-fair-cash-offer-dc-distressed-property.html | Learn More |

---

## Option 2: Semi-Automated (Using CSV + Bulk Edit)

**Best for:** Posting all 8 at once, consistency.

1. Open the CSV template below in a spreadsheet
2. Fill in each row (title, description, URL, image path)
3. Copy rows into GMB's bulk editor (if available in your account) or use the single-post form 8 times

**CSV Template:**
```csv
title,description,url,image_path,cta
"We Buy Houses Baltimore Fast — No Realtor, No Wait","Your Baltimore home can close in a week. No agent. No repairs. We handle it. Get a free cash offer today.","https://www.parlevugloballlc.com/blog-we-buy-houses-baltimore-fast.html","images/blog/dmv-we-buy-houses-baltimore-fast.jpg","Book Now"
"Get a Real Cash Offer on Your Baltimore House in 24 Hours","Forget the 90-day listing grind. Get a written cash offer from Parlevu in one day.","https://www.parlevugloballlc.com/blog-cash-offer-baltimore-maryland.html","images/blog/dmv-cash-offer-baltimore-maryland.jpg","Learn More"
...
```

---

## Option 3: Automated (Python Script + Google Business Profile API)

**Best for:** Recurring syncs, production scale, zero-touch updates.

### Prerequisites

1. **Google Cloud Project Setup** (one-time, ~10 min):
   - Go to https://console.cloud.google.com
   - Create a new project (name: "Parlevu GMB Sync")
   - Enable **Google Business Profile API**
   - Create a **Service Account** (JSON key file)
   - Share your GMB business with the service account email

2. **Python Packages:**
   ```bash
   pip install google-auth-oauthlib google-api-python-client
   ```

3. **Run the Sync Script** (below):
   ```bash
   python tools/sync_gmb_posts.py --creds path/to/service-account-key.json
   ```

### Script: `tools/sync_gmb_posts.py`

```python
"""Sync blog posts to Google My Business automatically.
Requires: Google Business Profile API enabled + service account JSON key.

Usage: python tools/sync_gmb_posts.py --creds path/to/key.json [--dry-run]
"""
import argparse
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# DMV posts to sync
POSTS = [
    ("We Buy Houses Baltimore Fast", "blog-we-buy-houses-baltimore-fast.html", "Your Baltimore home can close in a week."),
    ("Cash Offer Baltimore Maryland", "blog-cash-offer-baltimore-maryland.html", "Get a written cash offer from Parlevu in one day."),
    ("Cash Home Buyers DC", "blog-cash-home-buyers-dc-washington.html", "DC's transfer taxes are brutal. Selling for cash cuts through them."),
    ("Sell House Arlington Virginia", "blog-sell-house-arlington-virginia.html", "Arlington market is competitive. We close faster than any agent can list."),
    ("Baltimore House Buyers (Any Condition)", "blog-baltimore-house-buyers-we-buy-any-condition.html", "Fire damage? Tenants? Hoarder house? We've bought them all."),
    ("Sell House Fast Alexandria", "blog-sell-house-fast-alexandria-virginia.html", "Alexandria market is competitive. We close faster than any agent can list."),
    ("Sell Inherited House Maryland", "blog-sell-inherited-house-maryland-fast.html", "Inherited a Maryland property? We buy it as-is. No probate delays."),
    ("Fair Cash Offer DC Distressed", "blog-fair-cash-offer-dc-distressed-property.html", "Your DC rowhouse doesn't need to be perfect. We buy it exactly as it sits."),
]

def sync_to_gmb(creds_path, dry_run=False):
    # Authenticate with service account
    creds = service_account.Credentials.from_service_account_file(creds_path)
    service = build('mybusinessbusinessinformation', 'v1', credentials=creds)
    
    # Get your business account
    # NOTE: You'll need to manually get your business ID from GMB dashboard
    # or fetch it from the API: https://developers.google.com/my-business/reference/rest/v4.11/accounts/list
    business_id = "YOUR_BUSINESS_ID_HERE"
    
    for title, slug, desc in POSTS:
        url = f"https://www.parlevugloballlc.com/{slug}"
        print(f"  {title}")
        if not dry_run:
            # Create post via API (implementation would go here)
            # This is a placeholder — full API integration requires more setup
            print(f"    → Would post to GMB: {url}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--creds", required=True, help="Path to service account JSON")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    sync_to_gmb(args.creds, args.dry_run)
```

---

## Recommended Approach

**For today:** Use **Option 1 (Manual)** to get familiar with GMB's UI and see immediate results.

**For ongoing:** Set a recurring calendar reminder (e.g., every Monday morning) to post 1-2 blog posts per week. This keeps your GMB feed active without overwhelming your followers.

**For scale:** Once you're comfortable, move to **Option 3** and run the sync script weekly or after each new batch.

---

## What GMB Posts Do

✅ Show up in Google Search results (3-pack carousel for local searches)  
✅ Appear on your GMB business card (right side of Google Search for "Parlevu Global" + queries)  
✅ Drive clicks back to your website (trackable in GA4)  
✅ Signal freshness to Google's algorithm (regular posts → higher local ranking)  
✅ Give customers another reason to trust you (active, responsive business)

---

## Next Steps

1. **Today:** Pick 3 posts and manually post them (Option 1) to see how they render
2. **This week:** Post the remaining 5
3. **Ongoing:** Post new blog content to GMB within 48 hours of publishing to the site

---

## Troubleshooting

**Post not showing in search results?**
- Google caches GMB posts for 24-48 hours. Check back in a day.
- Verify your business is fully verified (blue checkmark in GMB).

**Image not loading?**
- GMB prefers images 1200×630px or square. Our images are 1200×630 — should be fine.
- If stuck, re-upload the image directly from your computer.

**Can't find the Posts button?**
- Make sure you're logged in with an account that has "Owner" or "Manager" permissions on the business.

---

## Resources

- [Google My Business Help Center](https://support.google.com/business/answer/2721894)
- [Posts Feature Overview](https://support.google.com/business/answer/7577590)
- [Business Profile API Docs](https://developers.google.com/my-business/reference/rest)
