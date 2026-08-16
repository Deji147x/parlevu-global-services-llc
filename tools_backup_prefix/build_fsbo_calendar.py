#!/usr/bin/env python3
"""Build the 90-day FSBO Support series into content-calendar.json.

- 10 pillar briefs (kind=pillar, hand-written long-form) on days 1,10,19,...
- 80 question briefs (kind=question, generate_post.py pipeline) on remaining days
- Existing status=queued posts are re-dated to resume after day 90.

Run:  python3 tools/build_fsbo_calendar.py
"""
import json
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CAL = REPO / "content-calendar.json"
HUB = "fsbo-support-maryland-virginia-dc.html"
START = date.today() + timedelta(days=1)

# 10 clusters: (pillar slug-stem, pillar title, primary kw, [8 question posts])
# Each question: (slug-stem, title, primary_kw, [secondary kws])
CLUSTERS = [
    ("fsbo-maryland-complete-guide", "For Sale By Owner in Maryland: The Complete 2026 Guide",
     "for sale by owner maryland",
     [
      ("how-does-fsbo-work-maryland", "How Does For Sale By Owner Work in Maryland?", "how does for sale by owner work in maryland", ["fsbo process maryland", "sell by owner steps"]),
      ("is-fsbo-worth-it-maryland", "Is Selling FSBO Worth It in Maryland? The Honest Math", "is fsbo worth it", ["fsbo savings maryland", "fsbo commission savings"]),
      ("fsbo-mistakes-maryland", "7 FSBO Mistakes Maryland Sellers Make (And How to Avoid Them)", "fsbo mistakes to avoid", ["fsbo tips maryland", "for sale by owner mistakes"]),
      ("fsbo-baltimore-guide", "Selling Your Baltimore Home By Owner: What's Different in the City", "for sale by owner baltimore", ["fsbo baltimore", "sell by owner baltimore"]),
      ("fsbo-disclosure-maryland", "What Must You Disclose When Selling By Owner in Maryland?", "maryland seller disclosure fsbo", ["fsbo disclosure requirements", "maryland disclosure statement"]),
      ("fsbo-attorney-maryland", "Do You Need a Real Estate Attorney to Sell FSBO in Maryland?", "real estate attorney fsbo maryland", ["fsbo lawyer cost", "fsbo settlement attorney"]),
      ("fsbo-inspection-maryland", "FSBO and the Home Inspection: What Maryland Sellers Should Expect", "fsbo home inspection", ["home inspection by owner sale", "fsbo inspection negotiation"]),
      ("fsbo-safety-showings", "Showing Your FSBO Home Safely: A Practical Checklist", "fsbo showing safety", ["fsbo open house tips", "showing house by owner"]),
     ]),
    ("sell-house-without-realtor-md-va-dc", "How to Sell a House Without a Realtor in Maryland, Virginia & DC",
     "sell house without realtor",
     [
      ("can-i-sell-without-realtor-maryland", "Can I Sell My House Without a Realtor in Maryland?", "sell house without realtor maryland", ["no realtor home sale md", "sell without agent maryland"]),
      ("can-i-sell-without-realtor-virginia", "Can I Sell My House Without a Realtor in Virginia?", "sell house without realtor virginia", ["no agent sale virginia", "fsbo virginia rules"]),
      ("can-i-sell-without-realtor-dc", "Can I Sell My House Without a Realtor in Washington DC?", "sell house without realtor dc", ["fsbo washington dc", "no agent sale dc"]),
      ("sell-without-realtor-save-money", "How Much Do You Really Save Selling Without a Realtor?", "how much save selling without realtor", ["realtor commission savings", "fsbo net proceeds"]),
      ("sell-without-realtor-paperwork", "The Paperwork You Handle Yourself When There's No Agent", "selling house without realtor paperwork", ["no realtor documents", "fsbo forms"]),
      ("sell-without-realtor-to-cash-buyer", "Selling Directly to a Cash Buyer: No Realtor, No Listing", "sell house directly to cash buyer", ["no realtor cash sale", "direct home sale"]),
      ("sell-without-realtor-negotiation", "Negotiating a Home Sale Yourself: Scripts That Work", "negotiate home sale without agent", ["fsbo negotiation tips", "counter offer by owner"]),
      ("sell-without-realtor-risks", "The Real Risks of Selling Without an Agent (and How to Manage Them)", "risks of selling house without realtor", ["fsbo risks", "sell by owner pitfalls"]),
     ]),
    ("fsbo-paperwork-contracts-guide", "FSBO Paperwork & Contracts: Every Form You Need in MD, VA & DC",
     "fsbo paperwork",
     [
      ("who-draws-up-contract-fsbo", "Who Draws Up the Contract in a For Sale By Owner Deal?", "who draws up contract for sale by owner", ["fsbo contract who writes", "fsbo purchase agreement"]),
      ("fsbo-contract-maryland", "The Maryland FSBO Contract: Clauses You Can't Skip", "fsbo contract maryland", ["maryland residential contract", "fsbo purchase agreement md"]),
      ("fsbo-deed-transfer", "How the Deed Gets Transferred in an FSBO Sale", "fsbo deed transfer", ["property deed transfer by owner", "title transfer fsbo"]),
      ("fsbo-escrow-explained", "Who Holds Escrow in an FSBO Sale?", "who holds escrow in fsbo", ["fsbo earnest money", "escrow without agent"]),
      ("fsbo-title-company", "Do FSBO Sellers Need a Title Company? (Yes — Here's Why)", "fsbo title company", ["title search by owner sale", "settlement company fsbo"]),
      ("fsbo-lead-paint-disclosure", "Lead Paint Disclosure Rules for Pre-1978 Homes in the DMV", "lead paint disclosure fsbo", ["pre-1978 home disclosure", "federal lead disclosure"]),
      ("fsbo-contingencies", "Understanding Contingencies in Your FSBO Contract", "fsbo contract contingencies", ["financing contingency fsbo", "inspection contingency by owner"]),
      ("fsbo-paperwork-mistakes", "5 Paperwork Mistakes That Kill FSBO Closings", "fsbo paperwork mistakes", ["fsbo closing problems", "fsbo document errors"]),
     ]),
    ("fsbo-closing-costs-guide", "FSBO Closing Costs in Maryland, Virginia & DC: Who Pays What",
     "fsbo closing costs",
     [
      ("who-pays-closing-costs-fsbo", "Who Pays Closing Costs When Selling a House By Owner?", "who pays closing costs for sale by owner", ["fsbo closing costs split", "seller closing costs by owner"]),
      ("maryland-transfer-tax-fsbo", "Maryland Transfer & Recordation Taxes in an FSBO Sale", "maryland transfer tax home sale", ["recordation tax maryland", "fsbo transfer tax md"]),
      ("dc-transfer-tax-fsbo", "DC's Transfer Taxes Are High — Here's How FSBO Sellers Plan for Them", "dc transfer tax home sale", ["dc recordation tax", "fsbo closing costs dc"]),
      ("fsbo-buyer-agent-commission", "Do You Have to Pay the Buyer's Agent in an FSBO Sale?", "do i pay buyers agent fsbo", ["fsbo buyer agent commission", "buyer agent fee by owner"]),
      ("fsbo-no-closing-costs-cash", "How Cash Sales Cut Closing Costs to Nearly Zero", "sell house no closing costs", ["cash sale closing costs", "we pay closing costs"]),
      ("fsbo-property-tax-proration", "Property Tax Prorations at an FSBO Closing, Explained Simply", "property tax proration home sale", ["fsbo tax proration", "closing adjustments"]),
      ("fsbo-capital-gains", "Will You Owe Capital Gains Tax After Your FSBO Sale?", "capital gains selling house by owner", ["home sale tax exclusion", "capital gains primary residence"]),
      ("fsbo-closing-day", "What Actually Happens on FSBO Closing Day", "fsbo closing process", ["closing day by owner", "settlement day fsbo"]),
     ]),
    ("flat-fee-mls-maryland-guide", "Flat Fee MLS in Maryland: How FSBO Sellers Get on the MLS",
     "flat fee mls maryland",
     [
      ("do-fsbo-homes-go-on-mls", "Do For Sale By Owner Homes Go on the MLS?", "do fsbo homes go on mls", ["fsbo mls listing", "mls without realtor"]),
      ("how-to-list-on-mls-by-owner", "How to List on the MLS Without an Agent", "how to list on mls by owner", ["flat fee mls listing", "mls access fsbo"]),
      ("flat-fee-mls-worth-it", "Is Flat Fee MLS Worth It? Costs vs. Exposure", "is flat fee mls worth it", ["flat fee mls cost", "flat fee vs full service"]),
      ("where-list-fsbo-free", "Where to List Your Home For Sale By Owner for Free", "list home for sale by owner free", ["free fsbo listing sites", "zillow fsbo listing"]),
      ("fsbo-zillow-listing", "Listing Your FSBO Home on Zillow: Step-by-Step", "fsbo zillow how to", ["zillow for sale by owner", "post home on zillow"]),
      ("fsbo-photos-that-sell", "FSBO Listing Photos: What Buyers Click On", "fsbo listing photos", ["real estate photo tips", "listing photos by owner"]),
      ("fsbo-listing-description", "Writing a Listing Description That Actually Rings Your Phone", "fsbo listing description", ["home listing description examples", "write listing by owner"]),
      ("fsbo-mls-vs-cash-offer", "MLS Exposure vs. a Direct Cash Offer: Which Fits Your Timeline?", "mls listing vs cash offer", ["list or sell cash", "fsbo or cash buyer"]),
     ]),
    ("sell-house-as-is-by-owner-guide", "Selling a House As-Is By Owner: Any Condition, Any Situation",
     "sell house as-is by owner",
     [
      ("sell-as-is-no-repairs", "Can You Sell a House As-Is Without Making Repairs?", "sell house as is no repairs", ["as is home sale", "sell without fixing"]),
      ("sell-as-is-maryland-rules", "As-Is Sales in Maryland: What 'As-Is' Legally Means", "sell house as is maryland", ["as is disclosure maryland", "as is contract md"]),
      ("fsbo-fixer-upper", "Selling a Fixer-Upper By Owner: Pricing Honest Condition", "sell fixer upper by owner", ["fsbo fixer upper", "sell house needs work"]),
      ("fsbo-inherited-house-as-is", "Inherited a House Full of Stuff? Selling As-Is By Owner", "sell inherited house as is", ["inherited house by owner", "estate property as is"]),
      ("fsbo-fire-water-damage", "Selling a Damaged Home By Owner: Fire, Water & Mold", "sell damaged house by owner", ["fire damage home sale", "water damage house sale"]),
      ("fsbo-code-violations", "Selling a House With Code Violations By Owner", "sell house with code violations", ["code violation home sale", "open permits sale"]),
      ("fsbo-tenant-occupied", "Selling a Tenant-Occupied Property By Owner in the DMV", "sell tenant occupied house", ["sell rental property tenants", "tenant rights home sale dc"]),
      ("fsbo-as-is-cash-buyers", "Why As-Is Sellers Often Skip the Listing and Take Cash", "as is cash home buyers", ["cash buyers any condition", "sell as is fast"]),
     ]),
    ("fsbo-pricing-guide", "How to Price Your FSBO Home: CMA, Appraisals & Strategy",
     "how to price house for sale by owner",
     [
      ("fsbo-cma-yourself", "How to Run Your Own Comparative Market Analysis (CMA)", "how to do a cma yourself", ["fsbo comps", "comparable sales analysis"]),
      ("fsbo-appraisal-before-listing", "Should You Get an Appraisal Before Selling By Owner?", "pre listing appraisal fsbo", ["appraisal before selling", "fsbo appraisal cost"]),
      ("fsbo-overpricing-trap", "The Overpricing Trap: Why FSBO Homes Sit 55 Days", "fsbo overpricing", ["overpriced house not selling", "fsbo days on market"]),
      ("fsbo-price-reduce-when", "When (and How Much) to Reduce Your FSBO Price", "when to reduce house price", ["price reduction strategy", "fsbo price drop"]),
      ("fsbo-zestimate-accuracy", "Is the Zestimate Accurate? What Maryland Data Shows", "is zestimate accurate", ["zestimate vs appraisal", "zillow estimate accuracy"]),
      ("fsbo-pricing-baltimore", "Pricing a Baltimore Rowhome: Block-by-Block Reality", "price house baltimore", ["baltimore home values", "baltimore rowhome pricing"]),
      ("fsbo-seller-concessions", "Seller Concessions: When Giving a Little Wins the Deal", "seller concessions fsbo", ["closing cost help buyer", "concessions negotiation"]),
      ("fsbo-cash-offer-math", "Cash Offer Math: Comparing Net Proceeds, Not Sticker Price", "cash offer vs listing net proceeds", ["cash offer calculator", "net sheet home sale"]),
     ]),
    ("fsbo-marketing-guide", "FSBO Marketing That Works: Free & Low-Cost Ways to Find Your Buyer",
     "fsbo marketing ideas",
     [
      ("fsbo-facebook-marketplace", "Selling Your House on Facebook Marketplace: A Real Playbook", "sell house facebook marketplace", ["facebook home listing", "social media home sale"]),
      ("fsbo-yard-sign-tips", "Yard Signs Still Work: Placement, Wording, Phone Volume", "fsbo yard sign", ["for sale by owner sign", "yard sign tips"]),
      ("fsbo-open-house", "Running an FSBO Open House That Produces Offers", "fsbo open house", ["open house by owner", "open house checklist"]),
      ("fsbo-craigslist-nextdoor", "Craigslist, Nextdoor & Neighborhood Groups: Hidden Buyer Pools", "list house craigslist nextdoor", ["nextdoor home sale", "local buyer marketing"]),
      ("fsbo-video-walkthrough", "Phone-Shot Video Walkthroughs That Double Inquiries", "home video walkthrough diy", ["video tour by owner", "listing video tips"]),
      ("fsbo-curb-appeal-budget", "Curb Appeal on a $200 Budget", "cheap curb appeal ideas", ["curb appeal before selling", "budget home staging"]),
      ("fsbo-buyer-screening", "Screening Buyers: Pre-Approval Letters & Proof of Funds", "screen home buyers fsbo", ["proof of funds letter", "pre approval verification"]),
      ("fsbo-marketing-not-working", "Marketing Not Working? Diagnosing a Silent FSBO Listing", "fsbo not getting showings", ["no offers on house", "listing no interest"]),
     ]),
    ("fsbo-vs-cash-offer-guide", "FSBO Stalled? Your Options: Relist, Reduce, or Take a Cash Offer",
     "fsbo not selling what to do",
     [
      ("fsbo-not-selling-reasons", "Why Isn't My FSBO Home Selling? The 6 Usual Suspects", "why is my house not selling", ["fsbo no offers", "house sitting on market"]),
      ("fsbo-expired-what-next", "FSBO Didn't Work — What Are Your Next Moves?", "fsbo failed what next", ["after fsbo fails", "relist or sell cash"]),
      ("fsbo-vs-cash-timeline", "FSBO Timeline vs. Cash Sale Timeline: 55 Days vs. 7", "how long does fsbo take", ["fsbo median days on market", "cash sale timeline"]),
      ("fsbo-lowball-offers", "Handling Lowball Offers Without Losing the Buyer", "lowball offer on house", ["respond to low offer", "counter lowball"]),
      ("fsbo-deal-fell-through", "Your Buyer Backed Out: Recovering When the Deal Falls Through", "home sale fell through", ["buyer backed out", "failed settlement"]),
      ("fsbo-carrying-costs", "The Hidden Cost of Waiting: Carrying Costs Month by Month", "carrying costs unsold house", ["cost of house sitting", "mortgage while selling"]),
      ("fsbo-cash-offer-legit", "How to Tell a Legit Cash Buyer From a Wholesaler", "legit cash home buyers", ["cash buyer scams", "vet cash buyer"]),
      ("fsbo-hybrid-exit", "The Hybrid Exit: Keep Your Listing Live While Getting a Cash Backup Offer", "backup cash offer", ["cash offer while listed", "fsbo backup plan"]),
     ]),
    ("fsbo-timeline-guide", "The Real FSBO Timeline: From Decision to Closing Day",
     "how long does it take to sell a house by owner",
     [
      ("fsbo-timeline-week-by-week", "Your FSBO Sale, Week by Week", "fsbo timeline", ["sell by owner schedule", "fsbo steps timeline"]),
      ("fsbo-prep-before-listing", "The 2 Weeks Before You List: Prep That Pays", "prepare house for sale checklist", ["pre listing checklist", "get house ready to sell"]),
      ("fsbo-best-time-sell-dmv", "The Best Month to Sell in Maryland, Virginia & DC (Data)", "best time to sell house maryland", ["best month sell home dmv", "seasonal home sales"]),
      ("fsbo-under-contract-to-close", "Under Contract to Closing: The 30-45 Days Nobody Explains", "under contract to closing timeline", ["escrow period steps", "closing timeline"]),
      ("fsbo-sell-in-7-days", "Need to Sell in 7 Days? What's Actually Possible", "sell house in 7 days", ["one week home sale", "emergency home sale"]),
      ("fsbo-sell-in-30-days", "The 30-Day Sale: A Realistic Sprint Plan", "sell house in 30 days", ["fast home sale plan", "30 day sale checklist"]),
      ("fsbo-moving-coordination", "Coordinating Your Move With an Uncertain Closing Date", "moving before closing", ["rent back agreement", "possession after closing"]),
      ("fsbo-relocation-deadline", "Selling By Owner on a Relocation Deadline", "sell house fast relocation", ["job relocation home sale", "moving deadline sale"]),
     ]),
]

SCENES = ["sunlit front porch of a brick rowhome", "kitchen table with paperwork and coffee",
          "handshake at a front door", "family packing moving boxes", "yard sign on a green lawn",
          "aerial view of a suburban neighborhood", "cozy living room with staging touches",
          "keys and contract on a wooden table", "row of charming townhouses at golden hour",
          "home office desk with laptop showing a listing"]
STYLES = ["photorealistic, warm natural light", "editorial photography, shallow depth of field",
          "bright airy real-estate photography", "documentary style, authentic feel"]
CTAS = ["offer", "consult", "call"]
STATES = ["MD", "MD", "VA", "DC"]  # Maryland-weighted per user focus

def brief(slug, title, kw, secondaries, kind, cluster_i, day_i, pub_date):
    st = "MD" if kind == "pillar" else STATES[day_i % len(STATES)]
    return {
        "slug": f"fsbo-{slug}" if not slug.startswith("fsbo") else slug,
        "title": title,
        "primary_keyword": kw,
        "secondary_keywords": secondaries,
        "state": st,
        "city": "Baltimore" if (st == "MD" and day_i % 3 == 0) else "",
        "category": "FSBO Support",
        "kind": kind,
        "hub": HUB,
        "image_prompt": f"{SCENES[(cluster_i*3 + day_i) % len(SCENES)]}, {STYLES[day_i % len(STYLES)]}, no text, no watermark",
        "cta_variant": CTAS[day_i % len(CTAS)],
        "status": "queued",
        "publish_date": pub_date.isoformat(),
        "published_on": None,
    }

def main():
    cal = json.loads(CAL.read_text(encoding="utf-8"))
    posts = cal if isinstance(cal, list) else cal["posts"]
    existing_slugs = {p["slug"] for p in posts}

    # Build day order: pillar for cluster i on day i*9; its questions on the 8 days after
    new_briefs = []
    day = 0
    for ci, (pslug, ptitle, pkw, questions) in enumerate(CLUSTERS):
        pdate = START + timedelta(days=day)
        new_briefs.append(brief(pslug, ptitle, pkw,
                                [q[2] for q in questions[:4]], "pillar", ci, day, pdate))
        day += 1
        for qi, (qslug, qtitle, qkw, qsec) in enumerate(questions):
            qdate = START + timedelta(days=day)
            new_briefs.append(brief(qslug, qtitle, qkw, qsec, "question", ci, day, qdate))
            day += 1

    new_briefs = [b for b in new_briefs if b["slug"] not in existing_slugs]

    # Re-date existing queued posts to resume after the FSBO series
    resume = START + timedelta(days=day)
    queued_old = [p for p in posts if p.get("status") == "queued"]
    for i, p in enumerate(sorted(queued_old, key=lambda p: p.get("publish_date") or "")):
        p["publish_date"] = (resume + timedelta(days=i)).isoformat()

    posts.extend(new_briefs)
    if isinstance(cal, list):
        CAL.write_text(json.dumps(posts, indent=2), encoding="utf-8")
    else:
        cal["posts"] = posts
        CAL.write_text(json.dumps(cal, indent=2), encoding="utf-8")

    pillars = [b for b in new_briefs if b["kind"] == "pillar"]
    print(f"Added {len(new_briefs)} FSBO briefs ({len(pillars)} pillars, {len(new_briefs)-len(pillars)} questions)")
    print(f"FSBO series: {START} -> {START + timedelta(days=day-1)}")
    print(f"Existing {len(queued_old)} queued posts re-dated to start {resume}")
    for p in pillars:
        print(f"  PILLAR {p['publish_date']}: {p['slug']}")

if __name__ == "__main__":
    main()
