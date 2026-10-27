#!/usr/bin/env python3
"""Build faq.html and fsbo-consultation.html, the two pages the FAQ review asks for.

Both are assembled from what-we-buy.html's own head, nav and footer, so they
inherit the live site's GA4 tags, styles, navigation and contact block rather
than a hand-rolled copy that drifts. Only the title, description, canonical,
schema and body content are new.

  faq.html                All 30 FAQs grouped into the review's five categories,
                          with FAQPage schema.
  fsbo-consultation.html  The review's highest-priority page. Carries FAQs 7-12,
                          the seller-responsibility material the review asks for,
                          and a consultation CTA.

Content comes from faq-calendar.json, so the answers on these pages and the
answers in the social captions cannot drift apart.

A note on FAQPage schema: Google has limited FAQ rich results largely to
authoritative government and health sites, so this will probably not produce
rich snippets. It is still worth emitting -- it states the Q&A relationship
unambiguously for AI assistants and other consumers.

  python tools/build_faq_pages.py            # dry run
  python tools/build_faq_pages.py --apply
"""
import html
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CAL = REPO / "faq-calendar.json"
TEMPLATE = REPO / "what-we-buy.html"
SITE = "https://parlevugloballlc.com"
PHONE = "(667) 646-8306"
BOOKING = "https://calendar.app.google/hfm91n5jiLxXJHiu6"

CATEGORY_ORDER = ["A", "B", "C", "D", "E"]
CATEGORY_TITLE = {
    "A": "Selling a House for Cash in Baltimore",
    "B": "FSBO: For Sale By Owner",
    "C": "Difficult Property and Personal Situations",
    "D": "Cash Offers, Fees, Paperwork and Closing",
    "E": "Real Estate Investment",
}


def esc(s):
    return html.escape(s, quote=True)


def parts():
    """head boilerplate, nav, footer -- lifted from the live template."""
    s = io.open(TEMPLATE, encoding="utf-8").read()
    head_open = s[:s.index("<title>")]
    after_canonical = s.index('<link rel="canonical"')
    head_tail = s[s.index("/>", after_canonical) + 2:s.index("</head>")]
    # The template carries its own JSON-LD, including a FAQPage describing
    # what-we-buy.html. Inheriting it would put that page's four questions on
    # ours, so every new page would claim FAQs it does not show.
    head_tail = re.sub(
        r'\s*<script type="application/ld\+json">.*?</script>', "",
        head_tail, flags=re.S)
    nav = s[s.index("<nav"):s.index("</nav>") + len("</nav>")]
    footer = s[s.index("<footer"):s.index("</footer>") + len("</footer>")]
    tail = s[s.index("</footer>") + len("</footer>"):]
    return head_open, head_tail, nav, footer, tail


def faq_schema(items):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in items
        ],
    }


def page(slug, title, description, header_h1, header_lead, body_html, schema):
    head_open, head_tail, nav, footer, tail = parts()
    return (
        head_open
        + "<title>" + esc(title) + "</title>\n"
        + '  <meta name="description" content="' + esc(description) + '"/>\n'
        + '  <link rel="canonical" href="' + SITE + "/" + slug + '"/>'
        + head_tail
        + '  <script type="application/ld+json">\n'
        + json.dumps(schema, indent=2, ensure_ascii=False)
        + "\n  </script>\n"
        + "</head>\n<body>\n\n<!-- ===== NAVBAR ===== -->\n"
        + nav + "\n\n"
        + '<section class="page-header">\n  <div class="container">\n'
        + '    <div class="page-header-inner">\n'
        + '      <div class="breadcrumb"><a href="index.html">Home</a> <span>/</span> '
        + esc(header_h1) + "</div>\n"
        + "      <h1>" + esc(header_h1) + "</h1>\n"
        + "      <p>" + esc(header_lead) + "</p>\n"
        + "    </div>\n  </div>\n</section>\n\n"
        + body_html
        + "\n" + footer + tail
    )


CTA_BLOCK = (
    '<section class="section bg-off-white">\n  <div class="container" '
    'style="text-align:center;max-width:720px">\n'
    '    <h2>Not sure which route fits?</h2>\n'
    '    <p style="color:var(--text-body);line-height:1.8">Tell us the address, the '
    'condition and your timeline. We will say plainly whether a direct sale, an FSBO '
    'consultation, or simply listing is the better fit for your situation. There is no '
    'charge and no obligation.</p>\n'
    '    <p style="margin-top:22px">\n'
    '      <a href="tel:+16676468306" class="btn btn-primary">Call ' + PHONE + '</a>\n'
    '      <a href="' + BOOKING + '" target="_blank" rel="noopener" '
    'class="btn btn-secondary">Book a free consultation</a>\n'
    "    </p>\n  </div>\n</section>\n"
)


def build_faq_page(entries):
    by_cat = {}
    for e in entries:
        by_cat.setdefault(e["category"], []).append(e)

    out = []
    for i, cat in enumerate(CATEGORY_ORDER):
        items = by_cat.get(cat, [])
        if not items:
            continue
        shade = ' bg-off-white' if i % 2 else ''
        out.append('<section class="section%s">\n  <div class="container" '
                   'style="max-width:860px">\n' % shade)
        out.append("    <h2>" + esc(CATEGORY_TITLE[cat]) + "</h2>\n")
        for e in items:
            out.append(
                '    <div style="margin:28px 0">\n'
                '      <h3 style="color:var(--navy);font-size:1.12rem;margin-bottom:10px">'
                + esc(e["question"]) + "</h3>\n"
                '      <p style="color:var(--text-body);line-height:1.8">'
                + esc(e["answer"]) + "</p>\n"
                '      <p style="margin-top:8px"><a href="' + e["publish_on_page"]
                + '" style="color:var(--gold);font-weight:700">More on this</a></p>\n'
                "    </div>\n")
        out.append("  </div>\n</section>\n\n")
    out.append(CTA_BLOCK)

    schema = faq_schema([(e["question"], e["answer"]) for e in entries])
    return page(
        "faq.html",
        "Frequently Asked Questions | Parlevu Global Services LLC",
        "Straight answers on selling a house for cash in Baltimore: as-is sales, "
        "inherited and distressed property, FSBO, offers, closing and Maryland "
        "disclosure rules.",
        "Frequently Asked Questions",
        "Thirty questions Baltimore homeowners actually ask before they call, "
        "answered plainly. Where an answer depends on your particular property, "
        "it says so rather than pretending otherwise.",
        "".join(out), schema)


FSBO_INTRO = (
    '<section class="section">\n  <div class="container" style="max-width:860px">\n'
    "    <h2>What you take on when you sell it yourself</h2>\n"
    '    <p style="color:var(--text-body);line-height:1.8">Selling without a listing '
    "agent is legal in Maryland and plenty of owners do it well. What changes is not "
    "the paperwork so much as who carries it. Pricing, marketing, fielding buyers, "
    "negotiating, keeping the contract moving and coordinating settlement all become "
    "yours.</p>\n"
    '    <p style="color:var(--text-body);line-height:1.8">The two places FSBO sales '
    "most often come apart are pricing and the contract. An online estimate cannot see "
    "a roof, a tenant or a lien, so a price set from one tends to be wrong in whichever "
    "direction costs you most. And a buyer's agent will be working from a contract "
    "written to protect their client, not you.</p>\n"
    "    <h2 style=\"margin-top:40px\">Where a consultation helps</h2>\n"
    '    <p style="color:var(--text-body);line-height:1.8">An FSBO consultation is not '
    "a listing pitch and it does not commit you to selling to us. We walk through what "
    "comparable properties actually sold for, what condition issues a buyer's lender is "
    "likely to flag, which disclosures apply to your sale, and what the realistic net "
    "looks like once costs are counted. If listing is the better route for your "
    "property, that is what we will tell you.</p>\n"
    '    <p style="color:var(--text-body);line-height:1.8">If you later decide the '
    "effort is not worth it, you can ask for a cash offer at any point. One does not "
    "oblige the other.</p>\n"
    "  </div>\n</section>\n\n"
)


def build_fsbo_page(entries):
    items = [e for e in entries if e["category"] == "B"]
    out = [FSBO_INTRO]
    out.append('<section class="section bg-off-white">\n  <div class="container" '
               'style="max-width:860px">\n    <h2>FSBO questions, answered</h2>\n')
    for e in items:
        out.append(
            '    <div style="margin:28px 0">\n'
            '      <h3 style="color:var(--navy);font-size:1.12rem;margin-bottom:10px">'
            + esc(e["question"]) + "</h3>\n"
            '      <p style="color:var(--text-body);line-height:1.8">'
            + esc(e["answer"]) + "</p>\n    </div>\n")
    out.append('    <p style="margin-top:18px"><a href="faq.html" '
               'style="color:var(--gold);font-weight:700">See all 30 questions</a></p>\n')
    out.append("  </div>\n</section>\n\n")
    out.append(CTA_BLOCK)

    schema = faq_schema([(e["question"], e["answer"]) for e in items])
    return page(
        "fsbo-consultation.html",
        "FSBO Consultation in Maryland | Parlevu Global Services LLC",
        "Selling your Baltimore home yourself? An FSBO consultation covers pricing, "
        "disclosures, contracts and realistic net proceeds. Free, no obligation.",
        "FSBO Consultation",
        "Selling without an agent keeps the commission but hands you the pricing, "
        "the paperwork and the negotiation. A consultation makes those parts "
        "manageable, and commits you to nothing.",
        "".join(out), schema)


def main():
    apply = "--apply" in sys.argv
    cal = json.loads(CAL.read_text(encoding="utf-8"))
    entries = cal["entries"]

    pages = {
        "faq.html": build_faq_page(entries),
        "fsbo-consultation.html": build_fsbo_page(entries),
    }
    for name, content in pages.items():
        n_q = content.count('"@type": "Question"')
        balanced = content.count("<div") == content.count("</div>")
        print("  %-26s %6d bytes  questions=%2d  div_balanced=%s%s"
              % (name, len(content), n_q, balanced,
                 "  (exists, will overwrite)" if (REPO / name).exists() else ""))
        if apply:
            (REPO / name).write_text(content, encoding="utf-8", newline="\n")
            (REPO / "upload-queue" / name).write_text(content, encoding="utf-8",
                                                      newline="\n")

    print("\n%s" % ("APPLIED (live + upload-queue)" if apply
                    else "DRY RUN - nothing written. Re-run with --apply."))


if __name__ == "__main__":
    main()
