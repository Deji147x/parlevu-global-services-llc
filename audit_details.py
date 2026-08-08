#!/usr/bin/env python3
import re
from pathlib import Path
from collections import defaultdict

REPO = Path('.')
issues_by_type = defaultdict(list)

for html_file in sorted(REPO.glob('blog-*.html')):
    html = html_file.read_text(encoding='utf-8', errors='replace')

    # Meta desc length
    m = re.search(r'<meta name="description" content="(.*?)"', html)
    if m:
        desc = m.group(1)
        if len(desc) > 165:
            issues_by_type['meta_too_long'].append((html_file.name, len(desc)))
        elif len(desc) < 70:
            issues_by_type['meta_too_short'].append((html_file.name, len(desc)))

    # Title length
    m = re.search(r'<title>(.*?)</title>', html)
    if m:
        title = m.group(1)
        if len(title) > 65:
            issues_by_type['title_too_long'].append((html_file.name, len(title)))

print("Issue Summary (first 5 of each type):")
for issue_type in sorted(issues_by_type.keys()):
    items = issues_by_type[issue_type]
    print(f"\n{issue_type}: {len(items)} pages")
    for item in items[:5]:
        if isinstance(item, tuple):
            print(f"  {item[0]}: {item[1]} chars")
        else:
            print(f"  {item}")
