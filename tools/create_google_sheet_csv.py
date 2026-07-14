"""Create CSV for Google Sheets import - copy/paste ready Buffer captions."""
import csv
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
    category = post.get("category", "")

    if "Foreclosure" in category:
        caption = f"""Facing Foreclosure in {state_name}? You have options.

Don't wait — the sooner you act, the more choices you have.

#RealEstate #{state} #Foreclosure #CashBuyer"""

    elif "Inherited" in category:
        caption = f"""Inherited a property? We can help. Sell fast. No probate delays.

#RealEstate #{state} #Inheritance #CashBuyer"""

    elif "Divorce" in category:
        caption = f"""Going through a divorce? Your house doesn't have to be a headache. Sell fast for cash.

#RealEstate #{state} #Divorce #CashBuyer"""

    elif "Liens" in category or "Violations" in category:
        caption = f"""Tax liens? Code violations? We still buy. Don't let debt hold you back.

#RealEstate #{state} #CashBuyer #PropertySolution"""

    elif "Fire" in category or "Water" in category or "Mold" in category or "Damage" in category:
        caption = f"""Damage that needs repair? We buy as-is. No repairs needed. Cash offer in 24 hours.

#RealEstate #{state} #CashBuyer #AsIs"""

    elif "Hoarder" in category:
        caption = f"""A full house? Junk? Clutter? We buy it all. Sell as-is. No cleaning required.

#RealEstate #{state} #CashBuyer #PropertySolution"""

    elif "Tenants" in category or "Bad" in category:
        caption = f"""Tenants causing trouble? We can take over. Sell fast. No more landlord headaches.

#RealEstate #{state} #Investment #CashBuyer"""

    elif "Underwater" in category:
        caption = f"""Underwater on your {state_name} mortgage? You still have options. Sell for cash.

#RealEstate #{state} #CashBuyer #PropertySolution"""

    elif "Vacant" in category:
        caption = f"""A vacant property? Bleeding money each month? Stop the drain. Sell for cash.

#RealEstate #{state} #CashBuyer #Investment"""

    elif "Relocation" in category or "Downsizing" in category:
        caption = f"""Ready for your next chapter? Sell your {state_name} home fast. Zero stress.

#RealEstate #{state} #CashBuyer #Relocation"""

    elif "Guides" in category or "City" in category or "Local" in category or "Fast" in category:
        city = post.get("city", state_name)
        caption = f"""Sell your {city} home for cash in 7 days. No agent. No repairs. No commission.

Fair offer. Fast closing. Zero hassle.

#{city} #RealEstate #CashBuyer"""

    elif "FSBO" in category or "FAQ" in category:
        caption = f"""Thinking about selling on your own? We answer your biggest questions.

#RealEstate #FSBO #SellingTips #CashBuyer"""

    else:
        caption = f"""Learn the truth about selling your {state_name} home. Real guidance. No fluff.

#RealEstate #{state} #CashBuyer"""

    return caption.strip()

def main():
    cal = json.loads(CAL.read_text(encoding="utf-8"))

    rows = [["Post #", "Title", "State", "Caption", "Blog URL", "Status"]]

    count = 0
    for post in cal["posts"]:
        if post["status"] in ["published", "generated"]:
            count += 1
            slug = post["slug"]
            title = post["title"]
            state = post["state"]
            url = f"{SITE_URL}/blog-{slug}.html"
            status = post["status"]
            caption = generate_caption(post)

            rows.append([
                count,
                title,
                state,
                caption,
                url,
                status
            ])

    # Write CSV
    csv_path = REPO / "BUFFER_POSTS.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"OK Generated CSV for {count} posts")
    print(f"OK Saved to BUFFER_POSTS.csv")
    print(f"OK Ready to import into Google Sheets")

if __name__ == "__main__":
    main()
