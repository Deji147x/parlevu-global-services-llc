#!/usr/bin/env python3
"""Enhance blog posts with hero images and internal linking."""
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BLOG_DIR = REPO
CAL = REPO / "content-calendar.json"

# Internal linking strategy map
LINKING_MAP = {
    "blog-seller-pain-points-real-estate-baltimore": [
        ("blog-fsbo-frequently-asked-questions-baltimore", "FSBO Frequently Asked Questions"),
        ("blog-we-buy-houses-baltimore-fast", "We Buy Houses Baltimore Fast"),
        ("blog-foreclosure-prevention", "Foreclosure Prevention Guide"),
    ],
    "blog-we-buy-houses-baltimore-fast": [
        ("blog-seller-pain-points-real-estate-baltimore", "7 Biggest Pain Points When Selling"),
        ("blog-fsbo-frequently-asked-questions-baltimore", "FSBO FAQ"),
        ("blog-foreclosure-md", "Facing Foreclosure in Maryland?"),
    ],
    "blog-fsbo-frequently-asked-questions-baltimore": [
        ("blog-seller-pain-points-real-estate-baltimore", "7 Biggest Seller Pain Points"),
        ("blog-why-your-fsbo-listing-isnt-selling-baltimore", "Why Your FSBO Listing Isn't Selling"),
        ("blog-we-buy-houses-baltimore-fast", "Alternative: Sell to a Cash Buyer"),
    ],
    "blog-foreclosure-prevention": [
        ("blog-foreclosure-md", "Foreclosure in Maryland"),
        ("blog-foreclosure-va", "Foreclosure in Virginia"),
        ("blog-foreclosure-dc", "Foreclosure in Washington DC"),
        ("blog-seller-pain-points-real-estate-baltimore", "Understanding Seller Pain Points"),
    ],
    "blog-foreclosure-md": [
        ("blog-foreclosure-prevention", "Foreclosure Prevention Guide"),
        ("blog-seller-pain-points-real-estate-baltimore", "7 Pain Points Foreclosure Sellers Face"),
        ("blog-we-buy-houses-baltimore-fast", "We Buy Homes in Foreclosure"),
    ],
}

def get_related_links(slug):
    """Get related links for a post."""
    if slug in LINKING_MAP:
        return LINKING_MAP[slug]

    # Default linking strategy based on post type
    links = []

    if "foreclosure" in slug:
        links.append(("blog-foreclosure-prevention", "Foreclosure Prevention Guide"))
        links.append(("blog-seller-pain-points-real-estate-baltimore", "7 Seller Pain Points"))

    if "fsbo" in slug or "selling" in slug:
        links.append(("blog-seller-pain-points-real-estate-baltimore", "7 Seller Pain Points"))
        links.append(("blog-we-buy-houses-baltimore-fast", "Sell Fast for Cash"))

    if "inherited" in slug:
        links.append(("blog-seller-pain-points-real-estate-baltimore", "7 Seller Pain Points"))
        links.append(("blog-we-buy-houses-baltimore-fast", "We Buy Inherited Homes"))

    if "divorced" in slug or "divorce" in slug:
        links.append(("blog-seller-pain-points-real-estate-baltimore", "7 Seller Pain Points"))
        links.append(("blog-we-buy-houses-baltimore-fast", "Quick Sale Solution"))

    if "sell-my-house-fast" in slug or "sell-house-fast" in slug:
        links.append(("blog-seller-pain-points-real-estate-baltimore", "Why Sellers Choose Cash Offers"))
        links.append(("blog-we-buy-houses-baltimore-fast", "Get Your Cash Offer"))

    # Limit to 3 links max
    return links[:3] if links else [("blog-we-buy-houses-baltimore-fast", "Get a Cash Offer")]

def add_hero_image(html, slug):
    """Add hero image section after article-intro."""
    if 'class="article-hero"' in html:
        return html  # Already has hero

    hero_html = f'''    <div class="article-hero">
      <img src="images/blog/{slug}.jpg" alt="Blog post hero image" style="width:100%;max-width:800px;height:auto;border-radius:8px;margin:32px 0;display:block;">
    </div>
'''

    # Find article-intro and insert after it
    pattern = r'(</div>\s*</div>\s*(?=<h2))'
    match = re.search(pattern, html)
    if match:
        insert_pos = match.start()
        return html[:insert_pos] + hero_html + html[insert_pos:]

    return html

def add_internal_links(html, slug):
    """Add internal links within article content."""
    if 'class="related-links"' in html:
        return html  # Already has links

    links = get_related_links(slug)
    if not links:
        return html

    links_html = '    <div class="related-links" style="margin:36px 0;padding:24px;background:rgba(201,168,76,.05);border-left:3px solid var(--gold);border-radius:4px;">\n'
    links_html += '      <p style="color:var(--navy);font-size:0.95rem;font-weight:600;margin-bottom:12px;">📖 Related Articles:</p>\n'
    links_html += '      <ul style="list-style:none;padding:0;margin:0;">\n'

    for link_slug, link_title in links:
        links_html += f'        <li style="margin-bottom:8px;"><a href="{link_slug}.html" style="color:var(--navy);font-weight:500;text-decoration:none;">→ {link_title}</a></li>\n'

    links_html += '      </ul>\n'
    links_html += '    </div>\n'

    # Insert before first CTA section
    cta_pattern = r'(<div style="text-align:center;padding:36px 24px;background:linear-gradient)'
    match = re.search(cta_pattern, html)
    if match:
        insert_pos = match.start()
        return html[:insert_pos] + links_html + html[insert_pos:]

    return html

def enhance_post(slug):
    """Enhance a single blog post."""
    post_file = BLOG_DIR / f"{slug}.html"

    if not post_file.exists():
        print(f"  ❌ {slug}.html not found")
        return False

    html = post_file.read_text(encoding='utf-8')

    # Add enhancements
    html = add_hero_image(html, slug)
    html = add_internal_links(html, slug)

    # Write back
    post_file.write_text(html, encoding='utf-8')
    print(f"  ✅ {slug}.html enhanced")
    return True

def main():
    posts_to_enhance = [
        "blog-seller-pain-points-real-estate-baltimore",
        "blog-we-buy-houses-baltimore-fast",
        "blog-fsbo-frequently-asked-questions-baltimore",
        "blog-foreclosure-prevention",
        "blog-foreclosure-md",
    ]

    print("🚀 Enhancing blog posts with hero images + internal links...\n")

    count = 0
    for slug in posts_to_enhance:
        if enhance_post(slug):
            count += 1

    print(f"\n✅ Enhanced {count}/{len(posts_to_enhance)} posts")
    print("\nNext: Commit to GitHub")

if __name__ == "__main__":
    main()
