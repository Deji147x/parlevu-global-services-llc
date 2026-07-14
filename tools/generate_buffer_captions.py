"""Generate Buffer captions for all published blog posts."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CAL = REPO / "content-calendar.json"
SITE_URL = "https://www.parlevugloballlc.com"

def generate_caption(post):
    """Create Buffer caption for a blog post."""
    slug = post["slug"]
    title = post["title"]
    state = post["state"]
    state_name = {"MD": "Maryland", "VA": "Virginia", "DC": "Washington DC"}.get(state, state)

    url = f"{SITE_URL}/blog-{slug}.html"

    # Template based on post category
    category = post.get("category", "")

    if "Foreclosure" in category:
        caption = f"""⚠️ {title}

Facing foreclosure in {state_name}? You have options.

Don't wait — the sooner you act, the more choices you have.

Read the full guide: {url}

#RealEstate #{state} #Foreclosure #CashBuyer"""

    elif "Inherited" in category:
        caption = f"""📋 {title}

Inherited a property? We can help.

Sell fast. No probate delays. No headaches.

Learn your options: {url}

#RealEstate #{state} #Inheritance #CashBuyer"""

    elif "Divorce" in category:
        caption = f"""💔 {title}

Going through a divorce? Your house doesn't have to be a headache.

Sell fast for cash. Move forward.

Get the facts: {url}

#RealEstate #{state} #Divorce #CashBuyer"""

    elif "Liens" in category or "Violations" in category:
        caption = f"""⚖️ {title}

Tax liens? Code violations? We still buy.

Don't let debt hold you back.

See your options: {url}

#RealEstate #{state} #CashBuyer #PropertySolution"""

    elif "Fire" in category or "Water" in category or "Mold" in category or "Damage" in category:
        caption = f"""🔨 {title}

Damage that needs repair? We buy as-is.

Your damaged {state_name} home has value.

No repairs needed. Cash offer in 24 hours.

Learn how: {url}

#RealEstate #{state} #CashBuyer #AsIs"""

    elif "Hoarder" in category:
        caption = f"""🏠 {title}

A full house? Junk? Clutter? We buy it all.

Sell as-is. No cleaning required.

Get cash for your {state_name} home today: {url}

#RealEstate #{state} #CashBuyer #PropertySolution"""

    elif "Tenants" in category or "Bad" in category:
        caption = f"""🔔 {title}

Tenants causing trouble? We can take over.

Sell fast. No more landlord headaches.

Cash offer for your {state_name} property: {url}

#RealEstate #{state} #Investment #CashBuyer"""

    elif "Underwater" in category:
        caption = f"""📉 {title}

Underwater on your {state_name} mortgage?

You still have options. Sell for cash.

Explore your path forward: {url}

#RealEstate #{state} #CashBuyer #PropertySolution"""

    elif "Vacant" in category:
        caption = f"""⏳ {title}

A vacant property? Bleeding money each month?

Stop the drain. Sell for cash.

Fast closing in {state_name}: {url}

#RealEstate #{state} #CashBuyer #Investment"""

    elif "Relocation" in category or "Downsizing" in category:
        caption = f"""📍 {title}

Ready for your next chapter?

Sell your {state_name} home fast. Zero stress.

Let's make your move smooth: {url}

#RealEstate #{state} #CashBuyer #Relocation"""

    elif "Guides" in category or "City" in category or "Local" in category or "Fast" in category:
        # City/neighborhood guide
        city = post.get("city", state_name)
        caption = f"""🏡 {title}

Sell your {city} home for cash in 7 days.

No agent. No repairs. No commission.

Fair offer. Fast closing. Zero hassle.

Sell now: {url}

#{city} #RealEstate #CashBuyer"""

    elif "FSBO" in category or "FAQ" in category:
        caption = f"""📚 {title}

Thinking about selling on your own?

We answer your biggest questions.

Read the FSBO guide: {url}

#RealEstate #FSBO #SellingTips #CashBuyer"""

    else:
        # Generic caption
        caption = f"""✨ {title}

Learn the truth about selling your {state_name} home.

Real guidance. No fluff. Direct from Parlevu.

Read more: {url}

#RealEstate #{state} #CashBuyer"""

    return caption.strip()

def main():
    cal = json.loads(CAL.read_text(encoding="utf-8"))

    output = []
    output.append("=" * 80)
    output.append("BUFFER CAPTIONS FOR ALL 91 PARLEVU BLOG POSTS")
    output.append("=" * 80)
    output.append("")
    output.append("INSTRUCTIONS:")
    output.append("1. Copy caption for the post you want to share")
    output.append("2. Log into Buffer.com → Compose")
    output.append("3. Paste caption into text area")
    output.append("4. Paste blog URL (shown below each caption)")
    output.append("5. Schedule for Mon/Wed/Fri at 9 AM")
    output.append("")
    output.append("=" * 80)
    output.append("")

    count = 0
    for post in cal["posts"]:
        if post["status"] in ["published", "generated"]:
            count += 1
            slug = post["slug"]
            title = post["title"]
            state = post["state"]
            url = f"{SITE_URL}/blog-{slug}.html"

            output.append(f"POST #{count}: {title}")
            output.append(f"Slug: {slug}")
            output.append(f"State: {state}")
            output.append("")

            caption = generate_caption(post)
            output.append(caption)
            output.append("")
            output.append(f"URL: {url}")
            output.append("")
            output.append("-" * 80)
            output.append("")

    result = "\n".join(output)
    (REPO / "BUFFER_CAPTIONS.txt").write_text(result, encoding="utf-8")
    print(f"OK Generated captions for {count} posts")
    print(f"OK Saved to BUFFER_CAPTIONS.txt")

if __name__ == "__main__":
    main()
