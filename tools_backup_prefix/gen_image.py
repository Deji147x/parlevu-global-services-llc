"""Generate a unique hero image per post using the free Pollinations.ai API.

No API key required. Saves 1200x630 JPEGs to images/blog/{slug}.jpg.
Falls back to a curated Unsplash CDN URL (hotlinked, not downloaded) if
Pollinations is unreachable — publish_next.py uses the returned path/URL.

Usage:  python tools/gen_image.py <slug> "<prompt>"
"""
import hashlib
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
IMG_DIR = REPO / "images" / "blog"

# Real-estate Unsplash photos already used/consistent with the site's look.
FALLBACK_POOL = [
    "https://images.unsplash.com/photo-1570129477492-45c003edd2be?auto=format&fit=crop&w=1200&q=75",
    "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1200&q=75",
    "https://images.unsplash.com/photo-1449844908441-8829872d2607?auto=format&fit=crop&w=1200&q=75",
    "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=75",
    "https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=1200&q=75",
    "https://images.unsplash.com/photo-1568605114967-8130f3a36994?auto=format&fit=crop&w=1200&q=75",
    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=75",
    "https://images.unsplash.com/photo-1583608205776-bfd35f0d9f83?auto=format&fit=crop&w=1200&q=75",
]


def generate(slug: str, prompt: str, retries: int = 3) -> str:
    """Return a relative path (downloaded) or absolute URL (fallback)."""
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    out = IMG_DIR / f"{slug}.jpg"
    if out.exists() and out.stat().st_size > 10_000:
        return f"images/blog/{slug}.jpg"

    seed = int(hashlib.sha1(slug.encode()).hexdigest()[:8], 16)
    url = ("https://image.pollinations.ai/prompt/"
           + urllib.parse.quote(prompt)
           + f"?width=1200&height=630&seed={seed}&nologo=true&model=flux")

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if len(data) > 10_000:  # sanity: not an error page
                out.write_bytes(data)
                return f"images/blog/{slug}.jpg"
        except Exception as e:
            print(f"  pollinations attempt {attempt + 1} failed: {e}")
            time.sleep(5 * (attempt + 1))

    # Fallback: stable per-slug pick from the Unsplash pool (hotlink)
    return FALLBACK_POOL[seed % len(FALLBACK_POOL)]


if __name__ == "__main__":
    slug, prompt = sys.argv[1], sys.argv[2]
    print(generate(slug, prompt))
