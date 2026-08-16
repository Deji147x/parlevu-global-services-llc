#!/usr/bin/env python3
"""Fix audit findings: duplicate H1s, missing canonical, noindex thank-you, sitemap refresh."""
import re
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TODAY = date.today().isoformat()

def fix_duplicate_h1(path):
    """Demote <h1 class="article-title"> to <h2> — page-header H1 stays the single H1.
    CSS targets .article-title by class, so visuals are unchanged."""
    html = path.read_text(encoding='utf-8')
    new = html.replace('<h1 class="article-title">', '<h2 class="article-title">')
    new = re.sub(r'(<h2 class="article-title">[^<]*)</h1>', r'\1</h2>', new)
    if new != html:
        path.write_text(new, encoding='utf-8')
        return True
    return False

def fix_canonical(path, filename):
    html = path.read_text(encoding='utf-8')
    if '<link rel="canonical"' in html:
        return False
    tag = f'  <link rel="canonical" href="https://parlevugloballlc.com/{filename}"/>\n'
    new = html.replace('<meta name="twitter:card"', tag + '  <meta name="twitter:card"', 1)
    if new == html:  # fallback: insert before </head>
        new = html.replace('</head>', tag + '</head>', 1)
    path.write_text(new, encoding='utf-8')
    return True

def noindex_thankyou():
    p = REPO / 'thank-you.html'
    if not p.exists():
        return False
    html = p.read_text(encoding='utf-8')
    if 'noindex' in html:
        return False
    html = html.replace('</title>', '</title>\n  <meta name="robots" content="noindex,follow"/>', 1)
    p.write_text(html, encoding='utf-8')
    return True

def rebuild_sitemap():
    """Regenerate sitemap from pages on disk (exclude thank-you + utility pages)."""
    exclude = {'thank-you.html'}
    pages = sorted(p.name for p in REPO.glob('*.html') if p.name not in exclude)
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for name in pages:
        pri = '1.0' if name == 'index.html' else ('0.9' if name.startswith('sell-house-fast') else ('0.7' if name.startswith('blog-') else '0.8'))
        freq = 'weekly' if name in ('index.html', 'blog.html') else 'monthly'
        lines.append(f'  <url><loc>https://parlevugloballlc.com/{name}</loc><lastmod>{TODAY}</lastmod><changefreq>{freq}</changefreq><priority>{pri}</priority></url>')
    lines.append('</urlset>')
    (REPO / 'sitemap.xml').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return len(pages)

def main():
    h1_fixed = 0
    for p in sorted(REPO.glob('*.html')):
        if fix_duplicate_h1(p):
            h1_fixed += 1
    print(f"H1 demoted on {h1_fixed} pages")

    if fix_canonical(REPO / 'blog-fsbo-frequently-asked-questions-baltimore.html',
                     'blog-fsbo-frequently-asked-questions-baltimore.html'):
        print("Canonical added: blog-fsbo-frequently-asked-questions-baltimore.html")

    if noindex_thankyou():
        print("noindex added: thank-you.html")

    n = rebuild_sitemap()
    print(f"Sitemap rebuilt with {n} URLs (lastmod {TODAY})")

if __name__ == "__main__":
    main()
