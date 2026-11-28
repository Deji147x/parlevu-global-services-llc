"""Regenerate each blog post's hero image so it matches the topic, and put a short caption on it.

Why: the first batch of heroes used generic prompts ("a house in Maryland"), so most posts show a
pretty suburban house whatever the topic, rowhouse neighborhoods show detached homes, "underwater
mortgage" shows a house in water, and several images carry garbled AI text on signs. No hero had
a caption.

What it does per post:
  1. builds a prompt from the post's topic + place (rules below; first match wins), always asking
     for no text, letters, signs or watermarks so the model cannot invent garbled words;
  2. renders it with Pollinations (same free service as tools/gen_image.py);
  3. draws a plain caption, taken from the post's H1, on a dark band at the bottom.

Sources (--source):
  pexels (default)   real stock photos from the Pexels API (free for commercial use, no credit
                     required). Needs PEXELS_API_KEY in the environment or in .env. Each photo is used
                     by one post only; picks are logged in drafts/hero_review/pexels_used.tsv
                     (photo id, photographer, page). --redo picks a different photo.
  ai                 the Pollinations generator (step 2 above; kept as a fallback)

Modes:
  default            write images to drafts/hero_review/<slug>.jpg only (nothing on the site changes)
  --apply            copy reviewed images to images/blog/<slug>-v2.jpg and point every page at them
                     (new file name, so Hostinger's 7-day CDN cache can't serve the old picture)

Usage:
  python tools/regen_hero_images.py --slugs underwater-mortgage-md,hoarder-house-md
  python tools/regen_hero_images.py --all            # every blog-*.html, skips ones already in review
  python tools/regen_hero_images.py --apply --all    # after the owner approves the review folder
"""
import argparse
import glob
import hashlib
import html
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
REVIEW = REPO / "drafts" / "hero_review"
IMG_DIR = REPO / "images" / "blog"
FONT = r"C:\Windows\Fonts\segoeuib.ttf"
W, H = 1200, 630

NO_TEXT = ("photorealistic documentary photograph, natural light, realistic everyday details, "
           "full-bleed image with no border and no frame, "
           "no text, no words, no letters, no numbers, no handwriting, no signs with writing, no logos, no watermark")

# Place -> what the housing there actually looks like.
PLACES = [
    (r"baltimore|dundalk|towson|glen-burnie|essex|parkville",
     "Baltimore Maryland brick rowhouses with white marble front steps"),
    (r"shaw|petworth|capitol-hill|columbia-height|brookland|trinidad|ivy-city|deanwood|anacostia|"
     r"congress-height|fort-totten|woodridge|-dc$|-dc-|washington",
     "Washington DC brick rowhouse street with small front porches and street trees"),
    (r"alexandria|arlington|fairfax|manassas|woodbridge|fredericksburg|richmond|norfolk|"
     r"virginia-beach|chesapeake|hampton|newport-news|-va$|-va-|virginia",
     "Virginia suburban neighborhood with modest brick colonial homes"),
    (r"annapolis|bowie|columbia|frederick|rockville|silver-spring|upper-marlboro|waldorf|-md$|-md-|maryland",
     "Maryland suburban street with modest older single-family homes"),
]
DEFAULT_PLACE = "mid-Atlantic neighborhood of modest older homes"

# Topic -> scene. Order matters: specific situations before general ones.
TOPICS = [
    (r"underwater-mortgage", "worried homeowner at a kitchen table with a mortgage statement and a calculator, "
                             "dry ordinary kitchen, house in the window, {place}"),
    (r"fire", "house exterior after a fire, black soot streaks above the windows, burned roof section, "
              "plywood over two windows, fire is completely out, clear daytime, {place}"),
    (r"water-mold|fire-water", "interior wall with water stains and mold patches, wet drywall cut away, dehumidifier on floor"),
    (r"foundation", "cracked concrete foundation wall in a basement with a measuring tape, close-up"),
    (r"hoarder", "hoarding situation, living room filled almost to the ceiling with piles of clothes, bags, "
                 "furniture and stacked belongings, only a narrow path through the clutter, daylight"),
    (r"vacant", "vacant house with overgrown lawn, closed curtains and mail piled at the door, {place}"),
    (r"storm", "house with storm damage, missing roof shingles and fallen tree branches in the yard, {place}"),
    (r"damaged-homes|damaged-house|fixer-upper|as-is|no-repairs|any-condition|distressed",
     "older house needing repairs, peeling paint, worn porch steps, {place}"),
    (r"code-violation|liens-violations", "older house with peeling paint and a broken porch railing, "
                                         "official envelope on the front step, {place}"),
    (r"foreclosure", "homeowner sitting at a table reading a stack of bank letters, serious mood, home interior"),
    (r"divorce|marital", "two people at opposite ends of a dining table with paperwork between them, "
                         "calm and serious, home interior"),
    (r"inherited|probate|estate", "two adult siblings in their forties sitting in their late parent's dated living room, "
                                  "an old set of house keys and a framed photo on the coffee table, quiet mood"),
    (r"bad-tenants|tenant", "landlord standing outside a worn rental rowhouse holding a folder, {place}"),
    (r"relocation|relocat|moving|deadline", "packed moving boxes by the front door and a moving truck outside, {place}"),
    (r"downsizing", "older couple packing keepsakes into boxes in a family home"),
    (r"scam", "homeowner looking at a phone and a printed offer with a skeptical expression, kitchen table"),
    (r"ibuyer", "person comparing two printed offers side by side on a laptop desk at home"),
    (r"closing-cost|who-pays|commission|transfer-tax|proration|capital-gains|carrying-cost|cost",
     "calculator, a set of house keys and a closed folder on a wooden table, close-up"),
    (r"closing-day|under-contract|title|escrow|deed", "close-up of one hand handing a set of house keys to another hand, blurred living room behind"),
    (r"contract|paperwork|disclosure|attorney|contingenc|checklist|draws-up",
     "closed document folder and a pen on a desk next to a coffee cup, shallow depth of field"),
    (r"inspection|appraisal", "home inspector with a clipboard and flashlight checking a basement water heater"),
    (r"open-house|showing|safety", "seller opening the front door of a tidy home to a visitor, {place}"),
    (r"photos|video", "person photographing a bright tidy living room with a phone on a small tripod"),
    (r"curb-appeal|prep|yard-sign", "homeowner planting flowers and painting the front door of a modest house, {place}"),
    (r"pricing|price|cma|zestimate|overpricing|lowball|offer-math|calculat|offers-calculated|cash-offer-math",
     ["homeowner reviewing printed comparable home sales with a highlighter and laptop at a kitchen table",
      "calculator, a pen and a printed spreadsheet on a table with a small model house",
      "couple discussing numbers on a notepad at a kitchen island"]),
    (r"zillow|mls|listing|website|facebook|craigslist|marketing|where-list|flat-fee",
     ["person at a laptop browsing home listings, home office, screen not readable",
      "phone in a hand showing a blurred photo of a house, living room background",
      "couple on a sofa scrolling home listings on a tablet, screen not readable"]),
    (r"negotiat|concession", "two people shaking hands across a kitchen table with papers, friendly"),
    (r"buyer-screening|questions", "seller talking with a prospective buyer at the front door of a home"),
    (r"sell-my-house-fast-|sell-house-fast-|sell-house-arlington|sell-fast-baltimore",
     ["street view of {place}, everyday daylight",
      "homeowner locking the front door of a house on {place}, late afternoon",
      "close view of the front steps and door of one house on {place}"]),
    (r"winter", "modest house in light snow with a shoveled front walk, {place}"),
    (r"market-update|home-values|best-time", "aerial view of a residential neighborhood, {place}, soft daylight"),
    (r"timeline|7-day|in-7|in-30|quick|sell-before|fast",
     ["wall calendar and house keys on a kitchen counter, morning light",
      "hourglass next to a set of house keys on a wooden table",
      "homeowner checking a phone calendar while standing in a half-packed living room"]),
    (r"fsbo|by-owner|without-realtor|vs-agent|avoid-realtor|private-home",
     ["homeowner standing at the front door of their own house, {place}",
      "homeowner at a kitchen table with a notebook planning the sale of their home",
      "homeowner showing a bright living room to a visitor"]),
    (r"cash-buyers|cash-home|buy-houses|we-buy|cash-vs|how-cash|baltimore-cash|cash-offer|sell-quickly|sell-fast",
     ["seller and a buyer shaking hands on the front steps, {place}",
      "house keys handed from one person to another on a front porch, {place}"]),
    (r"sell-house|sell-without", "street view of {place}, everyday daylight"),
]
DEFAULT_TOPIC = "street view of {place}, everyday daylight"

# Pexels (real stock photos): search terms per topic, same first-match order as TOPICS.
# "{place}" becomes a short place search term. Several terms per topic so posts on the same
# topic get different photos; a photo is never used twice (pexels_used.tsv).
PEXELS_PLACES = [
    (r"baltimore|dundalk|towson|glen-burnie|essex|parkville", "baltimore row houses"),
    # Pexels has few DC neighborhood photos; "washington dc" searches return downtown offices.
    (PLACES[1][0], "brick row houses"),
    (PLACES[2][0], "brick colonial house"),
    (PLACES[3][0], "suburban house front"),
]
QUERIES = [
    (r"underwater-mortgage", ["worried man bills kitchen table", "stressed woman paying bills", "couple reviewing bills"]),
    (r"fire", ["burned house", "fire damaged house", "house fire aftermath"]),
    (r"water-mold|fire-water", ["water damage ceiling", "mold wall", "water damaged room"]),
    (r"foundation", ["cracked concrete wall", "basement wall crack", "old basement"]),
    (r"hoarder", ["hoarding", "cluttered garage", "piles of stuff room"]),
    (r"vacant", ["abandoned house overgrown yard", "boarded up house", "empty old house exterior"]),
    (r"storm", ["storm damage house", "fallen tree house", "damaged roof"]),
    (r"damaged-homes|damaged-house|fixer-upper|as-is|no-repairs|any-condition|distressed",
     ["old house peeling paint", "run down house", "house needs repair"]),
    (r"code-violation|liens-violations", ["old house peeling paint", "broken porch", "run down house"]),
    (r"foreclosure", ["man reading letter worried", "stressed homeowner documents", "foreclosure"]),
    (r"divorce|marital", ["couple arguing table", "divorce", "couple sitting apart"]),
    (r"inherited|probate|(?<!real-)estate", ["old family photographs", "vintage living room empty", "old house keys"]),
    (r"bad-tenants|tenant", ["rental house", "landlord", "apartment building exterior"]),
    (r"relocation|relocat|moving|deadline", ["moving boxes", "moving truck house", "packing boxes home"]),
    (r"downsizing", ["senior couple packing", "older couple moving boxes", "elderly couple home"]),
    (r"scam", ["suspicious phone call", "man looking at phone worried", "scam"]),
    (r"ibuyer", ["comparing documents laptop", "person laptop home office", "online home buying"]),
    (r"closing-cost|who-pays|commission|transfer-tax|proration|capital-gains|carrying-cost|cost",
     ["calculator house keys", "calculator money house", "house model coins"]),
    (r"closing-day|under-contract|title|escrow|deed", ["handing over house keys", "new house keys", "signing contract house"]),
    (r"contract|paperwork|disclosure|attorney|contingenc|checklist|draws-up",
     ["signing documents", "contract signing pen", "paperwork desk"]),
    (r"inspection|appraisal", ["home inspector", "inspecting house", "contractor checking house"]),
    (r"open-house|showing|safety", ["open house real estate", "front door welcome", "house tour"]),
    (r"photos|video", ["photographing living room", "real estate photography", "bright living room"]),
    (r"yard-sign", ["for sale sign front yard", "house for sale sign"]),
    (r"curb-appeal|prep", ["front porch flowers", "painting front door", "house front yard"]),
    (r"pricing|price|cma|zestimate|overpricing|lowball|offer-math|calculat|offers-calculated|cash-offer-math",
     ["house price calculator", "real estate calculator", "couple budget planning", "house model money"]),
    (r"zillow|mls|listing|website|facebook|craigslist|marketing|where-list|flat-fee",
     ["browsing homes laptop", "house search phone", "couple looking at tablet"]),
    (r"negotiat|concession", ["handshake deal table", "business handshake home", "negotiation"]),
    (r"buyer-screening|questions", ["couple talking realtor", "people talking front door", "home buyers"]),
    (r"sell-my-house-fast-|sell-house-fast-|sell-house-arlington|sell-fast-baltimore",
     ["{place}", "house front door", "residential street houses"]),
    (r"winter", ["house snow", "winter house", "snowy street houses"]),
    (r"market-update|home-values|best-time", ["aerial neighborhood houses", "suburban neighborhood aerial", "residential neighborhood"]),
    (r"timeline|7-day|in-7|in-30|quick|sell-before|fast", ["calendar house keys", "hourglass", "calendar planning"]),
    (r"fsbo|by-owner|without-realtor|vs-agent|avoid-realtor|private-home",
     ["for sale house", "homeowner front door", "house front porch"]),
    (r"cash-buyers|cash-home|buy-houses|we-buy|cash-vs|how-cash|baltimore-cash|cash-offer|sell-quickly|sell-fast",
     ["handshake house keys", "house keys hand", "sold house"]),
    (r"sell-house|sell-without", ["{place}", "house exterior", "residential houses"]),
]
DEFAULT_QUERIES = ["{place}", "house exterior"]


def pexels_queries(slug):
    place = next((q for pat, q in PEXELS_PLACES if re.search(pat, slug)), "house street")
    qs = next((q for pat, q in QUERIES if re.search(pat, slug)), DEFAULT_QUERIES)
    # Start at a different term per post so same-topic posts don't all draw from one search.
    # Place-led topics (city pages) always search the local housing style first.
    k = 0 if qs[0] == "{place}" else int(hashlib.md5(slug.encode()).hexdigest(), 16) % len(qs)
    return [q.format(place=place) for q in qs[k:] + qs[:k]]


def pexels_key():
    if os.environ.get("PEXELS_API_KEY"):
        return os.environ["PEXELS_API_KEY"].strip()
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8-sig").splitlines():
            k, _, v = line.partition("=")
            if k.strip() == "PEXELS_API_KEY" and v.strip():
                return v.strip().strip('"').strip("'")
    sys.exit("PEXELS_API_KEY not found in the environment or .env")


USED = REVIEW / "pexels_used.tsv"
META = REVIEW / "manifest.json"


def load_meta():
    import json
    return json.loads(META.read_text(encoding="utf-8")) if META.exists() else {}


def save_meta(slug, fields):
    import json
    m = load_meta()
    m.setdefault(slug, {}).update(fields)
    META.write_text(json.dumps(m, indent=1, ensure_ascii=False), encoding="utf-8")


def used_ids():
    if not USED.exists():
        return {}
    out = {}
    for line in USED.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            out[parts[1]] = parts[0]
    return out


# Photo descriptions that make a hero wrong for a US home-selling post (found in the first full
# review): app/brand screens, foreign money, landmarks instead of homes, buyer-side "first home"
# shots, black-and-white, night scenes, collages, palm-tree settings.
BANNED_ALT = re.compile(
    r"pexels|google|logo|euro|banknote|currency|rupee|\blei\b|pound sterling|"
    r"monument|museum|smithsonian|capitol|skyline|mosque|minaret|church|cathedral|temple|"
    r"first home|our first|black and white|monochrome|\bnight\b|collage|illustration|"
    r"palm|stock market|trading|credit card|shopping|hacker|hoodie|candle|"
    r"office|downtown|hotel|intersection|avenue|child|girl|\bboy\b|\bkid|food|recipe|"
    r"online store|e-commerce|home sweet home|tenge|ruble|yuan|yen\b|peso|hryvnia|junk|"
    r"sepia|netherlands|dutch|amsterdam|rotterdam|utrecht|holland|belgium", re.I)


def fetch(url, timeout=60, tries=4):
    """GET bytes from the Pexels CDN, retrying dropped connections (WinError 10054 is common)."""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "parlevu-hero-images"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            if isinstance(e, urllib.error.HTTPError) and e.code < 500 or i == tries - 1:
                raise
            print(f"  download dropped ({e}); retrying in 20s", flush=True)
            time.sleep(20)


def looks(p):
    """(brightness, saturation, edge detail) of the photo's small preview, 0-255 scales."""
    import io
    from PIL import ImageFilter, ImageStat
    im = Image.open(io.BytesIO(fetch(p["src"]["small"], 30))).convert("RGB").resize((160, 90))
    return (ImageStat.Stat(im.convert("L")).mean[0], ImageStat.Stat(im.convert("HSV")).mean[1],
            ImageStat.Stat(im.convert("L").filter(ImageFilter.FIND_EDGES)).mean[0])


_SEARCH = {}


def pexels_search(q, key):
    """One search per term per run (posts share terms). Free tier = 200 searches/hour: on 429,
    wait for the reset the API reports, then retry."""
    import json
    if q in _SEARCH:
        return _SEARCH[q]
    url = ("https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
        {"query": q, "orientation": "landscape", "per_page": 80}))
    for _ in range(3):
        req = urllib.request.Request(url, headers={"Authorization": key, "User-Agent": "parlevu-hero-images"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                _SEARCH[q] = json.loads(r.read().decode()).get("photos", [])
                return _SEARCH[q]
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            reset = int(e.headers.get("X-Ratelimit-Reset") or 0)
            wait = max(60, min(3700, reset - int(time.time()) + 5)) if reset else 900
            print(f"  Pexels hourly limit reached; waiting {wait // 60} min", flush=True)
            time.sleep(wait)
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            print(f"  network error ({e}); retrying in 30s", flush=True)
            time.sleep(30)
    raise RuntimeError("Pexels rate limit did not reset")


def pexels_pick(slug, key, used, fresh=False):
    """The most relevant unused photo (Pexels' own ranking) that is neat enough for a hero: not
    too dark, not black-and-white, not a busy jumble, and no banned subject in its description.
    No photo is used by two posts. fresh=True (--redo) also skips photos this post had before."""
    for q in pexels_queries(slug):
        for p in pexels_search(q, key):
            pid = str(p["id"])
            free = pid not in used if fresh else used.get(pid, slug) == slug
            if not free or p["width"] < 1200 or BANNED_ALT.search(p.get("alt") or ""):
                continue
            bright, sat, edges = looks(p)
            if bright >= 60 and sat >= 12 and edges <= 46:
                return q, p
    return None, None


def pexels_render(slug, out, key, used, fresh=False):
    q, p = pexels_pick(slug, key, used, fresh)
    if not p:
        return None
    out.write_bytes(fetch(p["src"]["large2x"]))
    pid = str(p["id"])
    save_meta(slug, {"photo_id": pid, "photo_alt": (p.get("alt") or "").strip(),
                     "photographer": p.get("photographer", ""), "photo_page": p.get("url", ""), "query": q})
    if used.get(pid) != slug:
        used[pid] = slug
        with open(USED, "a", encoding="utf-8") as fh:
            fh.write(f"{slug}\t{pid}\t{p.get('photographer', '')}\t{p.get('url', '')}\t{q}\n")
    return f"pexels {pid} ({q}) by {p.get('photographer', '')}"


CITY_RE = re.compile(r"(?:sell-my-house-fast|sell-house-fast|sell-house)-([a-z-]+?)(?:-maryland|-virginia|-washington)?$")


def place_for(slug):
    region = next((d for pat, d in PLACES if re.search(pat, slug)), DEFAULT_PLACE)
    m = CITY_RE.search(slug)
    if m and m.group(1) not in ("fast", "without-realtor-md-va-dc"):
        city = m.group(1).replace("-", " ").title()
        return f"a typical residential street in {city}, {region}"
    return region


def prompt_for(slug):
    place = place_for(slug)
    scene = next((s for pat, s in TOPICS if re.search(pat, slug)), DEFAULT_TOPIC)
    if isinstance(scene, list):  # several scenes for common topics, picked per post
        scene = scene[int(hashlib.md5(slug.encode()).hexdigest(), 16) % len(scene)]
    return scene.format(place=place) + ", " + NO_TEXT


CAPTION_OVERRIDES = {
    "zillow-bans-non-mls-fsbo-listings": "Zillow's new rule for FSBO listings, explained",
    "17-questions": "17 questions buyers forget to ask",
}


def caption_for(title, slug=""):
    """Plain, short caption from the H1: drop guide boilerplate and trailing clauses."""
    if slug in CAPTION_OVERRIDES:
        return CAPTION_OVERRIDES[slug]
    t = html.unescape(re.sub(r"<[^>]+>", "", title)).strip()
    t = re.sub(r"^(complete guide|the complete guide)\s*:\s*", "", t, flags=re.I)
    t = re.sub(r"\s*\((?:data|real numbers|.*?)\)\s*$", "", t)
    for sep in (": ", " — ", " - ", " | "):
        if sep in t and len(t) > 50:
            t = t.split(sep)[0]
    if len(t) > 64 and "?" in t:
        t = t.split("?")[0] + "?"
    t = re.sub(r"\s*\.\.\.$", "", t).strip()
    if len(t) > 70:  # still long: cut at a word boundary
        t = t[:68].rsplit(" ", 1)[0] + "…"
    return t


def render(prompt, slug, out, retries=4):
    seed = int(hashlib.sha1(("v2" + slug).encode()).hexdigest()[:8], 16) & 0x7FFFFFFF
    url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
           + f"?width={W}&height={H + 40}&seed={seed}&nologo=true&model=flux")
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=150) as r:
                data = r.read()
            if len(data) > 10_000:
                out.write_bytes(data)
                return True
        except Exception as e:  # noqa: BLE001
            wait = (30, 90, 180, 300)[i] * (2 if isinstance(e, urllib.error.HTTPError) and e.code == 429 else 1)
            print(f"  {slug}: attempt {i + 1} failed ({e}); retry in {wait}s")
            time.sleep(wait)
    return False


def finish(raw, caption, out, badge=40):
    """Crop off the bottom strip (Pollinations badge; badge=0 for photos), cover-fit to 1200x630,
    draw the caption band."""
    im = Image.open(raw).convert("RGB")
    w, h = im.size
    im = im.crop((0, 0, w, h - badge))
    w, h = im.size
    scale = max(W / w, H / h)
    im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    left, top = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((left, top, left + W, top + H))
    d = ImageDraw.Draw(im, "RGBA")
    size = 46
    font = ImageFont.truetype(FONT, size)
    words, lines = caption.split(), []
    while True:
        lines, cur = [], ""
        for wd in words:
            test = (cur + " " + wd).strip()
            if d.textlength(test, font=font) <= W - 120:
                cur = test
            else:
                lines.append(cur); cur = wd
        lines.append(cur)
        if len(lines) <= 2 or size <= 34:
            break
        size -= 4; font = ImageFont.truetype(FONT, size)
    lh = int(size * 1.25)
    band = lh * len(lines) + 44
    d.rectangle((0, H - band, W, H), fill=(11, 26, 46, 200))          # site navy, mostly opaque
    d.rectangle((0, H - band, 10, H), fill=(212, 168, 67, 255))       # gold accent bar
    y = H - band + 22
    for ln in lines:
        d.text((60, y), ln, font=font, fill="white")
        y += lh
    im.save(out, "JPEG", quality=86, optimize=True, progressive=True)


def posts(slugs, all_):
    files = sorted(glob.glob(str(REPO / "blog-*.html")))
    for f in files:
        slug = os.path.basename(f)[5:-5]
        if all_ or slug in slugs:
            yield slug, Path(f)


def h1(path):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", path.read_text(encoding="utf-8", errors="replace"), re.S | re.I)
    return m.group(1) if m else path.stem


SITE = "https://parlevugloballlc.com"


def seo_name(caption, slug, taken):
    """Descriptive file name from the caption (what image search reads), unique across posts.
    A new name also means Hostinger's 7-day CDN cache can't serve the old picture."""
    base = re.sub(r"[^a-z0-9]+", "-", html.unescape(caption).lower().replace("'", "")).strip("-")[:70].strip("-")
    name = base if base and base not in taken else f"{base}-{slug}"[:90]
    taken.add(name)
    return name


def alt_text(caption, photo_alt):
    """Alt = the caption (it is text burned into the image, so it must be in the alt) plus what the
    photo shows, when Pexels describes it. Plain words, no keyword lists."""
    cap = html.unescape(caption).rstrip("…").strip()
    desc = re.sub(r"\s+", " ", photo_alt or "").strip().rstrip(".")
    # Pexels often names where the photo was taken ("in Adams Morgan, Washington DC"). That can
    # contradict the post's own place, and the caption already says where: drop place names.
    desc = re.sub(r"\s+(?:in|at|of|near|from)\s+(?:the\s+)?[A-Z][\w'.-]*(?:\s+[A-Z][\w'.-]*)*(?:,\s*[A-Z][\w'. -]*)*", "", desc)
    desc = re.sub(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*(?:[A-Z]{2}|Washington DC|USA)\b", "", desc).strip(" ,")
    if desc and len(cap) + len(desc) < 150:
        return f"{cap}: {desc[0].lower() + desc[1:]}"
    return cap


def apply(slug, page, taken):
    """Put the reviewed image on the post: SEO file name + WebP, alt text, a link to the offer box
    (tracked as hero_click), og/twitter image, schema ImageObject. Other pages using the old hero
    (blog index cards) get the new JPG path."""
    src = REVIEW / f"{slug}.jpg"
    meta = load_meta().get(slug, {})
    if not src.exists() or "caption" not in meta:
        print(f"  {slug}: no reviewed image, skipped"); return 0
    cap = meta["caption"]
    name = meta.get("file") or seo_name(cap, slug, taken)
    save_meta(slug, {"file": name})
    jpg, webp = f"images/blog/{name}.jpg", f"images/blog/{name}.webp"
    shutil.copyfile(src, REPO / jpg)
    Image.open(src).save(REPO / webp, "WEBP", quality=80, method=6)
    alt = html.escape(alt_text(cap, meta.get("photo_alt")), quote=True)

    t = rd(page)
    # Hero = first content image: a local blog image or an old hot-linked Unsplash one.
    old_m = re.search(r'<img\b[^>]*\bsrc="(images/blog/[^"]+|https://images\.unsplash\.com/[^"]+)"[^>]*>', t)
    if not old_m:
        print(f"  {slug}: hero <img> not found, skipped"); return 0
    old = old_m.group(1)
    hero = (f'<a href="#offer" data-hero-cta aria-label="Get a free cash offer">'
            f'<picture><source srcset="{webp}" type="image/webp">'
            f'<img decoding="async" src="{jpg}" alt="{alt}" width="1200" height="630" '
            f'style="width:100%;height:auto;display:block" fetchpriority="high"/></picture></a>')
    # A post applied before is already wrapped: replace the whole <a>…</a>, not just the <img>.
    wrapped = re.search(r'<a href="#offer" data-hero-cta[^>]*><picture>.*?</picture></a>', t, re.S)
    t = t.replace(wrapped.group(0), hero, 1) if wrapped else t.replace(old_m.group(0), hero, 1)
    t = t.replace(f"{SITE}/{old}", f"{SITE}/{jpg}").replace(old, jpg)
    abs_jpg = f"{SITE}/{jpg}"
    t = t.replace(f'property="og:image" content="{jpg}"', f'property="og:image" content="{abs_jpg}"')
    t = re.sub(r'("image":\s*")images/', rf'\1{SITE}/images/', t)  # schema image must be a full URL
    # og:image:alt and twitter:image (alt for both), added once, refreshed on re-apply.
    t = re.sub(r'\s*<meta property="og:image:alt"[^>]*>', "", t)
    t = re.sub(r'\s*<meta name="twitter:image(?::alt)?"[^>]*>', "", t)
    extra = (f'\n  <meta property="og:image:alt" content="{alt}"/>'
             f'\n  <meta name="twitter:image" content="{abs_jpg}"/>'
             f'\n  <meta name="twitter:image:alt" content="{alt}"/>')
    t = re.sub(r'(<meta property="og:image" content="[^"]+"\s*/?>)', lambda m: m.group(1) + extra, t, count=1)
    # Schema: the ImageObject gets a caption (search engines use it as the image's description).
    t = re.sub(r'("@type":\s*"ImageObject",\s*"url":\s*"' + re.escape(abs_jpg) + r'",)(\s*"caption":\s*"[^"]*",)?',
               lambda m: m.group(1) + f' "caption": {json_str(html.unescape(alt))},', t)
    wr(page, t)
    changed = 1
    for f in glob.glob(str(REPO / "*.html")):
        if Path(f) == page:
            continue
        s = rd(f)
        if old in s:
            wr(f, s.replace(old, jpg)); changed += 1
    return changed


def rd(path):
    """Read keeping the file's own line endings (no CRLF/LF conversion)."""
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def wr(path, text):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def json_str(s):
    import json
    return json.dumps(s, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slugs", default="")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--redo", action="store_true", help="re-render even if a review image exists")
    ap.add_argument("--source", choices=["pexels", "ai"], default="pexels",
                    help="pexels = real stock photos (needs PEXELS_API_KEY); ai = Pollinations generator")
    a = ap.parse_args()
    want = {s.strip() for s in a.slugs.split(",") if s.strip()}
    REVIEW.mkdir(parents=True, exist_ok=True)
    key = pexels_key() if a.source == "pexels" and not a.apply else None
    used = used_ids()
    taken = {m["file"] for m in load_meta().values() if m.get("file")}
    if a.apply:
        for slug, page in posts(want, a.all):
            print(f"{slug}: {apply(slug, page, taken)} page(s) updated")
        # main.js gained hero_click tracking: bump its cache-buster on every page so visitors get it.
        ver = time.strftime("%Y%m%d")
        for f in glob.glob(str(REPO / "*.html")):
            s = rd(f)
            n = re.sub(r"main\.js\?v=\d+", f"main.js?v={ver}", s)
            if n != s:
                wr(f, n)
        sys.path.insert(0, str(REPO / "tools"))
        from publish_next import regen_sitemap  # rebuilds sitemap.xml with image entries
        regen_sitemap()
        return
    for slug, page in posts(want, a.all):
        out = REVIEW / f"{slug}.jpg"
        if out.exists() and not a.redo:
            continue
        cap = caption_for(h1(page), slug)
        raw = REVIEW / f"{slug}.raw.jpg"
        if a.source == "pexels":
            pr = pexels_render(slug, raw, key, used, fresh=a.redo)
            ok, badge = bool(pr), 0
            time.sleep(1)  # stay well under Pexels' rate limit
        else:
            pr = prompt_for(slug)
            ok, badge = render(pr, slug, raw), 40
        if ok:
            finish(raw, cap, out, badge); raw.unlink()
            save_meta(slug, {"caption": cap})
            print(f"{slug}: ok | {cap} | {pr if a.source == 'pexels' else ''}")
        else:
            print(f"{slug}: FAILED ({'no unused photo found' if a.source == 'pexels' else 'render'})")
        with open(REVIEW / "captions.tsv", "a", encoding="utf-8") as fh:
            fh.write(f"{slug}\t{cap}\t{pr}\n")


if __name__ == "__main__":
    sys.exit(main())
