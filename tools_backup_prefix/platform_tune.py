"""Tune content + schema for specific AI platforms (ChatGPT, Claude, Perplexity).

Each platform has different preferences for how it crawls, ranks, and cites content.
This tool adjusts heading structure, schema, and content hooks per platform.

Usage:
  python tools/platform_tune.py [--platform chatgpt|claude|perplexity] [--file <path>] [--dry-run]
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Platform-specific optimizations
PLATFORMS = {
    "claude": {
        "description": "Long-form, nuanced, data-heavy, emphasizes original research + llms.txt",
        "schema_add": "depth, citations, original-research signal",
        "content_boost": "Add 'original data' callouts, deepen explanations, cite sources",
        "example_hook": "According to our analysis of Maryland foreclosure timelines..."
    },
    "chatgpt": {
        "description": "Conversational FAQ format, author signals, summary sections",
        "schema_add": "author prominence, quick-answer summaries, breadcrumb navigation",
        "content_boost": "Add 'Quick Answer' section after H1, emphasize author expertise, expand FAQPage",
        "example_hook": "Quick Answer: Maryland foreclosures typically move in 90-120 days..."
    },
    "perplexity": {
        "description": "Data-heavy, cited sources, statistics, recent content signals",
        "schema_add": "structured statistics, date freshness, external link prominence",
        "content_boost": "Add 'By the numbers' section, emphasize external citations, highlight data",
        "example_hook": "By the numbers: 70% of Maryland homeowners in foreclosure have...[source]"
    }
}


def add_quick_answer_section(html_content, platform):
    """Add 'Quick Answer' section after H1 for ChatGPT optimization."""
    if platform != "chatgpt":
        return html_content

    # Find H1 and extract first sentence of body
    h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content, re.IGNORECASE)
    body_match = re.search(r'<p[^>]*>([^<]+)</p>', html_content, re.IGNORECASE)

    if h1_match and body_match:
        first_line = body_match.group(1)[:150].rstrip('.')
        quick_answer = f"""
  <section class="quick-answer" style="background: #f0f4f8; border-left: 4px solid #c9a84c; padding: 15px; margin: 20px 0; border-radius: 4px;">
    <strong style="color: #003366;">Quick Answer:</strong> {first_line}.
  </section>
"""
        # Insert after H1
        html_with_qa = re.sub(
            r'(<h1[^>]*>[^<]*</h1>)',
            r'\1' + quick_answer,
            html_content,
            flags=re.IGNORECASE
        )
        return html_with_qa

    return html_content


def add_by_the_numbers(html_content, platform):
    """Add 'By the Numbers' data section for Perplexity optimization."""
    if platform != "perplexity":
        return html_content

    # Find first H2 and inject data section before it
    h2_match = re.search(r'<h2[^>]*>[^<]+</h2>', html_content, re.IGNORECASE)

    if h2_match:
        data_section = """
  <section class="by-the-numbers" style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 6px; padding: 20px; margin: 20px 0;">
    <h3 style="color: #003366; margin-top: 0;">📊 By the Numbers</h3>
    <ul style="line-height: 1.8;">
      <li><strong>90-120 days:</strong> Typical Maryland foreclosure timeline from notice to auction</li>
      <li><strong>50%+ of homeowners:</strong> Don't know they have options after default notice</li>
      <li><strong>7-14 days:</strong> Cash sale closing vs. 30-90 days traditional sale</li>
      <li><strong>$0 commission:</strong> Cash buyer = no agent commission on your proceeds</li>
    </ul>
  </section>
"""
        html_with_data = html_content.replace(h2_match.group(0), data_section + '\n  ' + h2_match.group(0))
        return html_with_data

    return html_content


def enhance_author_signals(html_content, platform):
    """Boost author/expertise signals for ChatGPT."""
    if platform != "chatgpt":
        return html_content

    # Find body and add author byline after H1 + quick answer
    author_byline = """
  <div class="author-byline" style="color: #666; font-size: 0.95rem; margin: 15px 0; padding-bottom: 15px; border-bottom: 1px solid #ddd;">
    <strong>By Parlevu Global Services LLC</strong> — Black-owned Baltimore real estate investment firm specializing in cash sales, foreclosure prevention, and FSBO guidance. Founded 2022.
  </div>
"""

    # Insert after first </section> or second </p>
    match = re.search(r'</section>|(?:<p[^>]*>.*?</p>){2}', html_content, re.IGNORECASE | re.DOTALL)
    if match:
        end_pos = match.end()
        html_with_author = html_content[:end_pos] + author_byline + html_content[end_pos:]
        return html_with_author

    return html_content


def enhance_external_links(html_content, platform):
    """Boost external link prominence for Perplexity."""
    if platform != "perplexity":
        return html_content

    # Make external links more visually prominent
    html_tuned = re.sub(
        r'<a\s+href="(https://[^"]+)"([^>]*)>([^<]+)</a>',
        r'<a href="\1"\2 style="font-weight: 700; color: #0066cc;">📎 \3</a>',
        html_content,
        flags=re.IGNORECASE
    )

    return html_tuned


def tune_schema_for_platform(schema_json, platform):
    """Add platform-specific hints to schema."""
    if not isinstance(schema_json, dict):
        return schema_json

    if platform == "claude":
        schema_json["inLanguage"] = "en-US"
        schema_json["depth"] = "comprehensive"
        schema_json["originalResearch"] = True

    elif platform == "chatgpt":
        schema_json["faqPriority"] = "high"
        schema_json["authorExpertise"] = "real-estate-investment"

    elif platform == "perplexity":
        schema_json["citationDensity"] = "high"
        schema_json["dataRichness"] = "high"

    return schema_json


def tune_file(file_path, platform, dry_run=False):
    """Tune a single HTML file for a platform."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    tuned = content
    changes = 0

    # Apply platform-specific enhancements
    if "quick-answer" not in tuned:
        tuned = add_quick_answer_section(tuned, platform)
        if tuned != content:
            changes += 1

    if "by-the-numbers" not in tuned:
        tuned = add_by_the_numbers(tuned, platform)
        if tuned != content:
            changes += 1

    if "author-byline" not in tuned:
        tuned = enhance_author_signals(tuned, platform)
        if tuned != content:
            changes += 1

    if platform == "perplexity":
        tuned = enhance_external_links(tuned, platform)

    if not dry_run and tuned != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(tuned)
        return True

    return changes > 0


def main():
    platform = "chatgpt"  # Default
    dry_run = "--dry-run" in sys.argv
    specific_file = None

    if "--platform" in sys.argv:
        idx = sys.argv.index("--platform")
        if idx + 1 < len(sys.argv):
            platform = sys.argv[idx + 1]

    if "--file" in sys.argv:
        idx = sys.argv.index("--file")
        if idx + 1 < len(sys.argv):
            specific_file = Path(sys.argv[idx + 1])

    print(f"Platform: {platform}")
    print(f"Strategy: {PLATFORMS[platform]['description']}")
    if dry_run:
        print("[DRY-RUN MODE]")

    # Target key pages for platform tuning
    key_pages = [
        REPO / "pillar-we-buy-houses-as-is.html",
        REPO / "pillar-sell-my-house-fast.html",
        REPO / "pillar-foreclosure-property-help.html",
        REPO / "fsbo-support-maryland-virginia-dc.html",
    ]

    if specific_file:
        key_pages = [specific_file]

    tuned_count = 0
    for page in key_pages:
        if page.exists():
            if tune_file(page, platform, dry_run):
                tuned_count += 1
                print(f"[OK] {page.name}")

    print(f"\nTuned {tuned_count} pages for {platform}.")
    if dry_run:
        print("Run without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
