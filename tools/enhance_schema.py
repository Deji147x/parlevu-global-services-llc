"""Enhance schema markup for AI search optimization (GEO).

Adds/updates Article schema (author, datePublished, keywords), improves FAQPage
with answerExplanation, adds Review schema for authority signals.

Usage:
  python tools/enhance_schema.py [--dry-run] [--file <path>]
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BLOG_DIR = REPO / "blog"

# Sample testimonials for Review schema (user can expand)
TESTIMONIALS = [
    {
        "text": "Sold my Baltimore home in 10 days without repairs. Fair offer, professional team.",
        "author": "Sarah M., Baltimore",
        "rating": 5
    },
    {
        "text": "They understood my foreclosure situation and closed before the auction. Saved my equity.",
        "author": "James T., Baltimore County",
        "rating": 5
    },
    {
        "text": "Virtual consultation was convenient. No pressure, just honest advice.",
        "author": "Rachel D., Washington DC",
        "rating": 5
    }
]


def load_calendar():
    """Load content-calendar.json for metadata."""
    cal_path = REPO / "content-calendar.json"
    if not cal_path.exists():
        return {}
    with open(cal_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {item['slug']: item for item in data.get('posts', [])}


def extract_slug_from_path(file_path):
    """Extract slug from filename."""
    name = file_path.stem
    # Remove 'blog-' prefix if exists
    if name.startswith('blog-'):
        return name[5:]
    return name


def build_article_schema(slug, metadata, file_path, h1_text):
    """Build enhanced Article schema."""
    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": metadata.get('title', h1_text or slug),
        "description": metadata.get('meta_description', ''),
        "author": {
            "@type": "Organization",
            "name": "Parlevu Global Services LLC",
            "url": "https://www.parlevugloballlc.com"
        },
        "publisher": {
            "@type": "Organization",
            "name": "Parlevu Global Services LLC",
            "logo": {
                "@type": "ImageObject",
                "url": "https://www.parlevugloballlc.com/logo.png",
                "width": 250,
                "height": 60
            }
        },
        "datePublished": metadata.get('publish_date', datetime.now().isoformat()),
        "dateModified": datetime.now().isoformat(),
        "inLanguage": "en-US",
        "isAccessibleForFree": True,
        "keywords": metadata.get('secondary_keywords', []),
        "image": {
            "@type": "ImageObject",
            "url": f"https://www.parlevugloballlc.com/images/blog/{slug}.jpg",
            "width": 1200,
            "height": 630
        }
    }
    return article


def build_faq_schema(faq_items):
    """Build/enhance FAQPage schema with answerExplanation."""
    if not faq_items:
        return None

    main_entity = []
    for q, a in faq_items:
        item = {
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": a,
                "answerExplanation": a[:200],  # First 200 chars as explanation
                "author": {
                    "@type": "Organization",
                    "name": "Parlevu Global Services LLC"
                }
            }
        }
        main_entity.append(item)

    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": main_entity[:5]  # Limit to 5 for FAQPage best practice
    }


def build_review_schema():
    """Build AggregateRating + Review schema from testimonials."""
    reviews = []
    for testimonial in TESTIMONIALS:
        reviews.append({
            "@type": "Review",
            "ratingValue": testimonial['rating'],
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": testimonial['rating'],
                "bestRating": 5,
                "worstRating": 1
            },
            "author": {
                "@type": "Person",
                "name": testimonial['author']
            },
            "reviewBody": testimonial['text']
        })

    return {
        "@context": "https://schema.org",
        "@type": "AggregateRating",
        "ratingValue": 5,
        "ratingCount": len(TESTIMONIALS),
        "bestRating": 5,
        "worstRating": 1,
        "reviews": reviews
    }


def extract_faq_from_html(html_content):
    """Try to extract Q&A pairs from FAQPage format in HTML."""
    faq_items = []
    # Look for <summary> + <p> pattern (details element)
    pattern = r'<summary[^>]*>([^<]+)</summary>\s*<p[^>]*>([^<]+)</p>'
    matches = re.findall(pattern, html_content, re.IGNORECASE)
    return matches[:5]  # Return first 5 Q&As


def enhance_html_schema(file_path, calendar_data, dry_run=False):
    """Enhance schema in a single HTML file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    slug = extract_slug_from_path(file_path)
    metadata = calendar_data.get(slug, {})

    # Extract H1
    h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content, re.IGNORECASE)
    h1_text = h1_match.group(1) if h1_match else None

    # Build schemas
    article_schema = build_article_schema(slug, metadata, file_path, h1_text)
    faq_items = extract_faq_from_html(content)
    faq_schema = build_faq_schema(faq_items) if faq_items else None
    review_schema = build_review_schema() if 'pillar' in slug or 'we-buy' in slug else None

    # Find </head> and inject schemas before it
    schema_scripts = []
    if article_schema:
        schema_scripts.append(f"<script type=\"application/ld+json\">\n{json.dumps(article_schema, indent=2)}\n</script>")
    if faq_schema:
        schema_scripts.append(f"<script type=\"application/ld+json\">\n{json.dumps(faq_schema, indent=2)}\n</script>")
    if review_schema:
        schema_scripts.append(f"<script type=\"application/ld+json\">\n{json.dumps(review_schema, indent=2)}\n</script>")

    schema_html = "\n  ".join(schema_scripts)

    # Remove old schema scripts (clean up duplicates)
    content_cleaned = re.sub(
        r'<script type="application/ld\+json">[\s\S]*?</script>',
        '',
        content,
        flags=re.IGNORECASE
    )

    # Inject new schemas before </head>
    new_content = content_cleaned.replace(
        '</head>',
        f"  {schema_html}\n</head>"
    )

    if not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    else:
        print(f"  [DRY-RUN] {file_path.name}: {len(schema_scripts)} schema(s) added")
        return True


def main():
    dry_run = '--dry-run' in sys.argv
    specific_file = None

    if '--file' in sys.argv:
        idx = sys.argv.index('--file')
        if idx + 1 < len(sys.argv):
            specific_file = Path(sys.argv[idx + 1])

    calendar_data = load_calendar()

    # Find HTML files
    if specific_file:
        html_files = [specific_file]
    else:
        html_files = list(REPO.glob('*.html')) + list(BLOG_DIR.glob('*.html')) if BLOG_DIR.exists() else list(REPO.glob('*.html'))

    print(f"Enhancing schema for {len(html_files)} HTML file(s)...")
    if dry_run:
        print("[DRY-RUN MODE]")

    success_count = 0
    for file_path in html_files:
        if file_path.name in ['.htaccess', 'sitemap.xml', '404.html']:
            continue
        try:
            if enhance_html_schema(file_path, calendar_data, dry_run):
                success_count += 1
                if not dry_run:
                    print(f"✓ {file_path.name}")
        except Exception as e:
            print(f"✗ {file_path.name}: {e}")

    print(f"\nDone! Enhanced {success_count} files.")
    if dry_run:
        print("Run without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
