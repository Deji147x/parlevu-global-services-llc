"""Build the situation landing pages (inherited, tenants, divorce) from one template.

    python tools/build_situation_pages.py

Header and footer are copied from pillar-foreclosure-property-help.html so the pages match the site.
Content rules: claims must come from published Parlevu posts; no invented numbers, reviews or client
stories; general information only, never legal or tax advice. Each page carries the valuation form
tagged with its situation, so the lead arrives in Hermes already labeled.
"""
import html, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://parlevugloballlc.com/"
PHONE, TEL = "(667) 646-8306", "+16676468306"
BOOK = "https://calendar.app.google/hfm91n5jiLxXJHiu6"
SCRIPT_V = "20261116"
TODAY = "2026-11-15"

src = (ROOT / "pillar-foreclosure-property-help.html").read_text(encoding="utf-8-sig")
NAV = re.search(r'<nav class="navbar">.*?</nav>', src, re.S).group(0).replace(' class="active"', "")
FOOTER = re.search(r"<footer.*?</footer>", src, re.S).group(0)
HEAD_TAGS = re.search(r"<!-- Google Tags.*?</script>\s*<script>.*?</script>", src, re.S).group(0)

PROCESS = [
    ("Tell us about the property", "Share the address and a few details by phone or with the form on this page."),
    ("Get a written offer", "Usually within 24–48 hours, after a quick walkthrough. No obligation."),
    ("Pick your closing date", "Most sales close in 7–21 days, or later if you need more time. As-is: no repairs, no cleaning, no showings, no agent commission."),
]
COMMON_FAQ = [
    ("Are there any fees or commissions?",
     "No agent commissions and no hidden fees. In most of our purchases the seller's closing costs are covered, so the "
     "offer you accept is very close to the cash you walk away with. We put the numbers in writing before you sign."),
    ("Do I have to clean out the house or make repairs?",
     "No. We buy as-is. Leave behind anything you don't want. Sellers must still disclose known material defects on the "
     "state disclosure form, even in an as-is sale."),
    ("Is a cash sale always the best option?",
     "No. If the house is in great shape and you have months to spare, listing it may net more, and we'll tell you so. "
     "A cash sale trades some top-line price for speed, certainty and no out-of-pocket costs."),
]

PAGES = [
  {
    "slug": "sell-inherited-house",
    "situation": "inherited",
    "title": "Sell an Inherited House As-Is in MD, DC & VA | Parlevu",
    "desc": "Inherited a house in Baltimore or the DMV? Sell it as-is, with no repairs or clean-out, on a closing date "
            "that works for every heir. Free offer.",
    "h1": "Sell an Inherited House As-Is, on a Timeline That Works for the Family",
    "lede": "Settling an estate is hard enough. We buy inherited houses in Maryland, DC and Virginia as-is, full of "
            "belongings or not, and close on a date that works for every heir.",
    "sections": [
      ("First: you probably have time",
       "<p>Unless the estate has urgent debts or the carrying costs are a burden, you don't have to decide this week. "
       "Most decisions about inherited property don't come with 30-day deadlines, and Maryland probate itself typically "
       "takes 6–12 months. Meanwhile, keep paying the mortgage, taxes, insurance and utilities from estate funds so the "
       "house stays protected.</p>"),
      ("How probate affects the sale",
       "<p>In Maryland, probate runs through the <b>Register of Wills</b> in the county where the owner lived. The "
       "personal representative (executor) files the will and an inventory; the house is appraised at its value on the "
       "date of death; estate debts are paid from estate assets (heirs aren't personally responsible for them); and "
       "title passes to the heirs by deed once the court allows it. Small estates (under $50,000) have a simpler "
       "process.</p>"
       "<p>Probate may not be needed at all if the house was in a <b>living trust</b>, held in <b>joint tenancy with "
       "right of survivorship</b>, or passed by a <b>transfer-on-death deed</b>.</p>"
       "<p><b>Can you sell before probate is finished?</b> Generally you need clear title first, but the personal "
       "representative may be given authority to sell during probate, and a cash sale can sometimes be signed now and "
       "closed after probate is final. A probate attorney can tell you what applies to your estate.</p>"),
      ("Taxes: the stepped-up basis",
       "<p>Heirs usually get a <b>stepped-up basis</b>: your tax basis is the home's fair market value on the date of "
       "death, not what the owner originally paid. If you sell soon after inheriting, there's often little taxable gain. "
       "Appreciation after the date of death can be taxable, so talk to a CPA about your situation.</p>"),
      ("When several heirs share the house",
       "<p>Every co-owner has to agree to a sale, and the family conversation is often harder than the paperwork. A few "
       "things help:</p><ul><li><b>Meet early</b> and find out who wants to sell, keep, rent or buy others out.</li>"
       "<li><b>Get an independent appraisal</b> if one heir wants to buy out the others, so everyone works from the same "
       "number.</li><li><b>Keep it simple.</b> A direct sale means one walkthrough, one written offer every heir can "
       "review, and proceeds paid out at a single closing.</li></ul>"
       "<p>If heirs truly can't agree, a co-owner can ask a court to order a sale (a partition action), but it's slow, "
       "costly and hard on families. It should be a last resort.</p>"),
      ("Common snags we can work through",
       "<ul><li><b>A mortgage on the house:</b> it doesn't go away when the owner dies; it's paid off from the sale at "
       "closing and the remaining equity goes to the heirs.</li><li><b>Unpaid property taxes:</b> they create liens, and "
       "Baltimore City's tax sale process is aggressive. They're settled at or before closing.</li><li><b>Clouded "
       "title:</b> missing deeds or old unreleased liens can usually be cleared by a title company or real estate "
       "attorney.</li><li><b>A house full of belongings:</b> take what matters to you and leave the rest.</li></ul>"),
      ("Your three options",
       "<table class='opt'><tr><th></th><th>What it involves</th><th>Best when</th></tr>"
       "<tr><td>Direct cash sale</td><td>As-is, no clean-out, close in about 2–3 weeks once title is clear</td>"
       "<td>The house needs work, heirs live far away, or the family wants it settled</td></tr>"
       "<tr><td>List with an agent</td><td>Often 45–90 days on market plus closing; every heir signs at each stage</td>"
       "<td>The house is in good shape and already cleared out</td></tr>"
       "<tr><td>Renovate, then list</td><td>3–6+ months, renovation paid up front, contractors to manage</td>"
       "<td>There's real equity and someone nearby to run the project</td></tr></table>"),
      ("State notes",
       "<ul><li><b>Maryland:</b> the Seller's Disclosure and Disclaimer Statement is required, even as-is. Transfer and "
       "recordation taxes typically total 1.5–3% depending on the county.</li><li><b>Washington DC:</b> probate can take "
       "several months; a Seller's Property Condition Disclosure is required for most sales; transfer and recordation "
       "taxes can reach 2.9% combined.</li><li><b>Virginia:</b> sellers use the Residential Property Disclosure "
       "Statement and can't actively conceal known defects.</li><li>Homes built before 1978 also need the federal "
       "lead-paint disclosure.</li></ul>"),
    ],
    "faq": [
      ("Do I have to go through probate to sell an inherited house in Maryland?",
       "In most cases, yes, to transfer clear title. The exceptions are a house held in a living trust, in joint tenancy "
       "with right of survivorship, or passed by a transfer-on-death deed. Maryland probate runs through the Register of "
       "Wills and typically takes 6–12 months; small estates under $50,000 have a simpler process."),
      ("Can we sign now and close after probate?",
       "Sometimes. The personal representative may have authority to sell during probate, and a cash sale can be "
       "structured to close once probate is final. Ask your probate attorney what applies to the estate."),
      ("Do heirs pay capital gains tax on an inherited house?",
       "Usually little, thanks to the stepped-up basis: your basis is the home's value on the date of death. Gains after "
       "that date can be taxable. A CPA can confirm for your situation."),
    ],
    "related": [("blog-inherited-property.html", "How to sell an inherited property in Baltimore (step by step)"),
                ("blog-inherited-probate-md.html", "Selling an inherited house in Maryland"),
                ("blog-inherited-probate-dc.html", "Selling an inherited house in Washington DC"),
                ("blog-inherited-probate-va.html", "Selling an inherited house in Virginia"),
                ("blog-fsbo-inherited-house-as-is.html", "Inherited a house full of stuff?")],
    "form_title": "Get a free, no-obligation offer on the inherited house",
  },
  {
    "slug": "sell-house-with-tenants",
    "situation": "tired landlord",
    "title": "Sell a Rental House With Tenants in Maryland | Parlevu",
    "desc": "Done being a landlord? Sell your Maryland, DC or Virginia rental as-is with the tenants in place. No "
            "repairs, no vacancy to wait out. Free offer.",
    "h1": "Sell Your Rental House With the Tenants Still in It",
    "lede": "Repairs, turnover, late rent or just a plan that changed. We buy rental houses in Maryland, DC and "
            "Virginia as-is, including houses with tenants living in them.",
    "sections": [
      ("You don't have to empty the house first",
       "<p>Selling to a regular buyer usually means waiting out the lease, making repairs, and holding showings around "
       "the people who live there. A buyer who purchases rentals as investments can take the house with the tenants in "
       "place and the condition as it is.</p>"
       "<p>The tenants' rights don't disappear because the house is sold. The lease and local rules still apply, and "
       "the walkthrough happens with proper notice to the tenants.</p>"),
      ("Your options as a landlord",
       "<table class='opt'><tr><th></th><th>What it involves</th><th>Best when</th></tr>"
       "<tr><td>Sell with tenants in place</td><td>One walkthrough with notice; as-is; close in about 1–3 weeks</td>"
       "<td>You want out now, the house needs work, or the lease runs a long time</td></tr>"
       "<tr><td>Wait for the lease to end, then list</td><td>Months of carrying costs, then repairs, cleaning and "
       "showings</td><td>The house is in good shape and the lease ends soon</td></tr>"
       "<tr><td>Offer it to your tenant</td><td>Only works if they can get financing</td>"
       "<td>Your tenant wants to buy and can qualify</td></tr></table>"),
      ("What to have ready",
       "<ul class='check'><li>Current lease(s) and any renewals or side agreements</li><li>Rent amount, payment history "
       "and security deposit held</li><li>Repair and maintenance records</li><li>Any open code or licensing notices "
       "from the city or county</li><li>The state disclosure form (Maryland: Seller's Disclosure and Disclaimer "
       "Statement; DC: Seller's Property Condition Disclosure; Virginia: Residential Property Disclosure Statement), "
       "plus the federal lead-paint disclosure for homes built before 1978</li></ul>"),
      ("Before you sign anything",
       "<p>Rules for tenant-occupied sales differ between Maryland, DC and Virginia. In DC in particular, tenants can "
       "have purchase rights in some sales. Have a local real estate attorney confirm what applies to your property "
       "and lease before you sign a contract with anyone.</p>"),
    ],
    "faq": [
      ("Will my tenants have to move out when you buy the house?",
       "No. We can buy the house with the tenants in place, subject to their lease and local law. What happens after "
       "the sale follows the lease and the rules where the house is."),
      ("Do I need to fix things the tenants damaged?",
       "No. We buy as-is and price the repairs into the offer. You still need to disclose known material defects on "
       "the state disclosure form."),
      ("Are there tax issues when selling a rental?",
       "There can be, especially with depreciation and capital gains on investment property. Talk to a tax "
       "professional before you sell."),
    ],
    "related": [("blog-bad-tenants-md.html", "Selling a rental property with tenants in Maryland"),
                ("blog-bad-tenants-dc.html", "Selling a rental property with tenants in Washington DC"),
                ("blog-bad-tenants-va.html", "Selling a rental property with tenants in Virginia"),
                ("blog-fsbo-tenant-occupied.html", "Selling a tenant-occupied property by owner")],
    "form_title": "Get a free, no-obligation offer on your rental",
  },
  {
    "slug": "sell-house-divorce",
    "situation": "divorce",
    "title": "Selling a House During Divorce in Maryland | Parlevu",
    "desc": "Selling the house in a divorce? Get one written as-is offer you can both review. No showings, and a "
            "closing date you agree on. MD, DC & VA.",
    "h1": "Selling the House in a Divorce, Without Months of Showings",
    "lede": "When the house has to be sold, the fewer moving parts the better. We make one written as-is offer that "
            "both owners, and both attorneys, can review, and close on a date you both choose.",
    "sections": [
      ("Your options for the house",
       "<table class='opt'><tr><th></th><th>What it involves</th><th>Best when</th></tr>"
       "<tr><td>Sell and split the proceeds</td><td>A listing (30–90 days) or a direct cash sale (about 1–3 weeks)</td>"
       "<td>Neither of you wants or can afford to keep it</td></tr>"
       "<tr><td>One spouse buys the other out</td><td>An independent appraisal and refinancing</td>"
       "<td>One of you wants to stay and can qualify for the loan</td></tr>"
       "<tr><td>Keep it jointly for now</td><td>Shared payments and decisions after the divorce</td>"
       "<td>You both agree on a later sale date</td></tr></table>"
       "<p>Your separation agreement or court order controls what happens to the house. Work out the plan with your "
       "attorneys or mediator.</p>"),
      ("Why a direct sale can make this easier",
       "<ul><li><b>One number in writing.</b> Both owners see the same offer and the same line-by-line net sheet, so "
       "there's less to argue about.</li><li><b>No showings to coordinate.</b> One walkthrough instead of weeks of "
       "keeping the house ready while you're also handling the divorce.</li><li><b>As-is.</b> No negotiating over who "
       "pays for which repair.</li><li><b>A closing date you agree on.</b> Proceeds are paid out at closing as your "
       "agreement directs.</li></ul>"),
      ("What we need from both of you",
       "<p>Everyone on the title signs the contract and the deed. We're glad to send the offer to both owners, or to "
       "both attorneys, at the same time, and we stay neutral. We don't take sides or give legal advice.</p>"
       "<p>The usual disclosure rules still apply: known material defects must be disclosed on the state form, even "
       "in an as-is sale.</p>"),
      ("If payments are falling behind",
       "<p>Divorce can strain the mortgage. If payments are slipping, look at your options early. In Maryland, "
       "foreclosure can move from a Notice of Intent to auction in a matter of months, and homeowners can sell at any "
       "point before the auction. The earlier you act, the more options you have.</p>"),
    ],
    "faq": [
      ("Can we sell the house before the divorce is final?",
       "Often, yes, if both owners agree and nothing in a court order or agreement prevents it. Check with your "
       "attorneys before signing."),
      ("Do both spouses have to agree to sell?",
       "Everyone on the title has to sign. If only one of you is on the title, ask your attorney how the house is "
       "treated in the divorce before you sell."),
      ("How are the proceeds split?",
       "However your separation agreement or court order directs. The title company pays out the proceeds at closing "
       "according to those instructions."),
    ],
    "related": [("blog-divorce-md.html", "Selling a house during divorce in Maryland"),
                ("blog-divorce-dc.html", "Selling a house during divorce in Washington DC"),
                ("blog-divorce-va.html", "Selling a house during divorce in Virginia")],
    "form_title": "Get one written offer you can both review",
  },
]

CSS = """
  body{margin:0}
  .sit-hero{background:var(--navy,#0A1628);color:#fff;padding:56px 20px 48px}
  .sit-hero .in,.sit-main{max-width:900px;margin:0 auto}
  .sit-hero .crumbs{font-size:.85rem;color:#9fb0c5;margin-bottom:14px}.sit-hero .crumbs a{color:#c9d3e0}
  .sit-hero h1{font-family:'Montserrat',sans-serif;color:#fff;font-size:clamp(1.7rem,4vw,2.5rem);line-height:1.2;margin:0 0 14px}
  .sit-hero p{color:#c9d3e0;font-size:1.1rem;max-width:720px;margin:0 0 22px}
  .sit-cta{display:flex;flex-wrap:wrap;gap:12px}
  .sit-cta a{padding:13px 20px;border-radius:8px;font-weight:700;text-decoration:none;font-family:'Montserrat',sans-serif}
  .sit-cta .p{background:var(--gold,#C9A84C);color:#0A1628}.sit-cta .s{border:1px solid #33465f;color:#fff}
  .sit-main{padding:12px 20px 40px;font-family:'Open Sans',sans-serif;line-height:1.75;color:#2D3748}
  .sit-main h2{font-family:'Montserrat',sans-serif;color:#0A1628;font-size:1.4rem;margin:36px 0 12px}
  .sit-steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:26px 0 8px}
  .sit-steps div{background:#F7F8FC;border:1px solid #E2E8F0;border-radius:10px;padding:16px}
  .sit-steps b{display:block;font-family:'Montserrat',sans-serif;color:#0A1628;margin-bottom:4px}
  .sit-steps span{font-family:'Montserrat',sans-serif;color:#A8863A;font-weight:800}
  table.opt{width:100%;border-collapse:collapse;font-size:.95rem;margin:8px 0}
  table.opt th{background:#0A1628;color:#fff;text-align:left;padding:9px 10px;font-family:'Montserrat',sans-serif;font-size:.85rem}
  table.opt td{border-bottom:1px solid #E2E8F0;padding:9px 10px;vertical-align:top}
  table.opt td:first-child{font-weight:700;color:#0A1628}
  @media(max-width:640px){table.opt,table.opt tbody,table.opt tr,table.opt td{display:block;width:auto}
    table.opt tr:first-child{display:none}table.opt tr{border-bottom:2px solid #E2E8F0;padding:6px 0}
    table.opt td{border:0;padding:3px 0}}
  ul.check{list-style:none;padding-left:0}ul.check li{padding-left:26px;position:relative;margin:6px 0}
  ul.check li:before{content:"\\2713";position:absolute;left:4px;color:#A8863A;font-weight:800}
  #offer{scroll-margin-top:90px;margin:36px 0}
  .sit-faq details{background:#F7F8FC;border-radius:8px;padding:12px 16px;margin:10px 0}
  .sit-faq summary{font-weight:700;color:#0A1628;cursor:pointer}
  .sit-related{background:#F7F8FC;border-radius:10px;padding:18px 20px;margin:30px 0}
  .sit-related a{display:block;color:#A8863A;font-weight:700;text-decoration:none;margin:6px 0}
  .sit-fine{font-size:.85rem;color:#4A5568;border-top:1px solid #E2E8F0;padding-top:14px;margin-top:30px}
"""


def schema(p):
    url = BASE + p["slug"] + ".html"
    org = {"@type": "Organization", "name": "Parlevu Global Services LLC", "url": BASE, "telephone": "+1-667-646-8306"}
    return [
        {"@context": "https://schema.org", "@type": "Service", "name": p["h1"], "description": p["desc"], "url": url,
         "serviceType": "Direct home purchase (as-is cash sale)", "provider": org,
         "areaServed": [{"@type": "State", "name": n} for n in ("Maryland", "Virginia")] +
                       [{"@type": "City", "name": "Washington, DC"}]},
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                        for q, a in p["faq"] + COMMON_FAQ]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE},
            {"@type": "ListItem", "position": 2, "name": "Services", "item": BASE + "services.html"},
            {"@type": "ListItem", "position": 3, "name": p["h1"], "item": url}]},
    ]


def render(p):
    url = BASE + p["slug"] + ".html"
    e = html.escape
    ld = "\n".join(f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>' for s in schema(p))
    steps = "".join(f"<div><span>{i}</span><b>{e(t)}</b>{e(d)}</div>" for i, (t, d) in enumerate(PROCESS, 1))
    body = "".join(f"<h2>{e(h)}</h2>{c}" for h, c in p["sections"])
    faq = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in p["faq"] + COMMON_FAQ)
    rel = "".join(f'<a href="{h}">{e(t)} →</a>' for h, t in p["related"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  {HEAD_TAGS}
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{e(p["title"])}</title>
  <meta name="description" content="{e(p["desc"])}"/>
  <link rel="canonical" href="{url}"/>
  <meta property="og:type" content="website"/><meta property="og:url" content="{url}"/>
  <meta property="og:title" content="{e(p["title"])}"/><meta property="og:description" content="{e(p["desc"])}"/>
  <meta property="og:image" content="{BASE}logo.png"/>
  <link rel="preconnect" href="https://fonts.googleapis.com"/><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&family=Open+Sans:wght@400;500;600&display=swap"/>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"/>
  <link rel="stylesheet" href="styles.css"/>
  <style>{CSS}</style>
  {ld}
</head>
<body>
{NAV}
<header class="sit-hero"><div class="in">
  <div class="crumbs"><a href="index.html">Home</a> / <a href="services.html">Services</a> / {e(p["h1"].split(",")[0])}</div>
  <h1>{e(p["h1"])}</h1>
  <p>{e(p["lede"])}</p>
  <div class="sit-cta"><a class="p" href="#offer">Get my free offer</a><a class="s" href="tel:{TEL}">Call {PHONE}</a></div>
</div></header>
<main class="sit-main">
  <div class="sit-steps">{steps}</div>
  {body}
  <section id="offer"><div data-parlevu-magnet="valuation" data-situation="{e(p["situation"])}" data-title="{e(p["form_title"])}"></div></section>
  <h2>Questions people ask</h2>
  <div class="sit-faq">{faq}</div>
  <div class="sit-related"><b>Read more</b>{rel}
    <a href="guides/parlevu-maryland-as-is-seller-guide.pdf" target="_blank" rel="noopener">Free guide: Selling your Maryland house as-is (PDF) →</a></div>
  <p class="sit-fine">General information, not legal, tax or financial advice. Parlevu Global Services LLC is a real
  estate investment company that buys homes; we are not a law firm or a brokerage. We treat every homeowner the same
  and follow fair housing laws. Prefer to talk it through? <a href="{BOOK}" target="_blank" rel="noopener">Book a free call</a>.</p>
</main>
{FOOTER}
<script src="main.js?v=20261114" defer></script>
<script src="/parlevu-estimator.js?v={SCRIPT_V}" defer data-api="https://api.parlevugloballlc.com"></script>
</body>
</html>
"""


if __name__ == "__main__":
    for p in PAGES:
        out = ROOT / (p["slug"] + ".html")
        out.write_text(render(p), encoding="utf-8", newline="\n")
        print("wrote", out.name, len(out.read_text(encoding="utf-8")))
