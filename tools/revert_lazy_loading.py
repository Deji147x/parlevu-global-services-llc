#!/usr/bin/env python3
"""Remove lazy-loading, keep only HubSpot defer."""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BLOG_DIR = REPO

def fix_post(file_path):
    """Remove lazy-loading from images (was causing TBT spike on mobile)."""
    html = file_path.read_text(encoding='utf-8')
    original = html

    # Remove loading="lazy" from all images
    html = re.sub(r' loading="lazy"', '', html)

    if html != original:
        file_path.write_text(html, encoding='utf-8')
        return True
    return False

def main():
    print("🔧 Reverting lazy-loading (causes mobile TBT spike)...\n")

    blog_files = sorted(REPO.glob('blog-*.html'))
    count = 0
    for blog_file in blog_files:
        if fix_post(blog_file):
            count += 1
            print(f"  ✅ {blog_file.name}")

    print(f"\n✅ Reverted {count} posts")
    print("\nKeeking only:")
    print("  • HubSpot deferred (no performance regression)")
    print("  • Eager image loading (no TBT spike)")

if __name__ == "__main__":
    main()
