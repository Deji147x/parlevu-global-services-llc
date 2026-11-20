#!/usr/bin/env python3
"""Soften the absolute "all closing costs" claim across the site.

RUN THIS ONLY IF the written purchase agreement does NOT cover every seller
closing cost without exception. If it genuinely does, the claim is accurate
and should stay -- softening a true claim weakens real differentiation.

WHY IT MATTERS
The phrase appears ~100 times across 55+ pages, including inside FAQPage
structured data, and Google is already lifting it into the search snippet for
"Parlevu Global Services LLC". Schema is machine-readable, which is exactly
why it gets quoted, and "you don't have to spend a dime" is the most absolute
form of it.

APPROACH
An earlier version of this tool matched exact strings and covered only 5 of
103 distinct phrasings. The wording varies far too much for that, so this uses
a regex on the claim itself and handles the absolute dollar statements
separately.

KNOWN CAVEAT
At least one occurrence describes a THIRD PARTY's flat-fee MLS service, not
Parlevu ("charging a flat fee for its services, which includes the MLS listing
and all closing costs"). The blanket replacement alters that sentence too.
Review the diff before committing; --report lists every match with context.

  python tools/soften_closing_costs.py --report    # list every occurrence
  python tools/soften_closing_costs.py             # dry run counts
  python tools/soften_closing_costs.py --apply
"""
import glob
import io
import os
import re
import sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CLAIM = re.compile(r"\ball closing costs\b", re.I)
REPLACEMENT = "the standard closing costs"

# The absolutes: these promise a specific outcome, not just coverage.
ABSOLUTES = [
    (re.compile(r"so you don't have to spend a dime on repairs", re.I),
     "so you don't pay for repairs"),
    (re.compile(r"so you'll spend \$0 on repairs", re.I),
     "so you don't pay for repairs"),
]

# Added once per page that carries the claim, inside the first FAQ answer
# mentioning it, so the qualification travels with the structured data.
QUALIFIER = (" Liens, payoffs and arrears are settled from the sale proceeds; "
             "your written offer and settlement statement set out the exact figures.")


def targets():
    return sorted(glob.glob("*.html")) + sorted(glob.glob("upload-queue/*.html"))


def main():
    report = "--report" in sys.argv
    apply = "--apply" in sys.argv

    if report:
        n = 0
        for f in targets():
            if f.startswith("upload-queue"):
                continue
            s = io.open(f, encoding="utf-8", errors="replace").read()
            for m in CLAIM.finditer(s):
                pre = s[:m.start()]
                where = ("SCHEMA" if pre.rfind("application/ld+json") > pre.rfind("</script>")
                         else "body")
                ctx = " ".join(s[max(0, m.start() - 75):m.end() + 45].split())
                ctx = "".join(c for c in ctx if ord(c) < 128)
                n += 1
                print("  %-6s %-46s %s" % (where, f[:46], ctx[:110]))
        print("\n  total occurrences on live pages: %d" % n)
        return

    files = body = schema = absolutes = 0
    for f in targets():
        s = io.open(f, encoding="utf-8", errors="replace").read()
        if not CLAIM.search(s):
            continue
        for m in CLAIM.finditer(s):
            pre = s[:m.start()]
            if pre.rfind("application/ld+json") > pre.rfind("</script>"):
                schema += 1
            else:
                body += 1
        new = CLAIM.sub(REPLACEMENT, s)
        for rx, rep in ABSOLUTES:
            new, k = rx.subn(rep, new)
            absolutes += k
        if new != s:
            files += 1
            if apply:
                io.open(f, "w", encoding="utf-8", newline="\n").write(new)

    left = sum(1 for f in glob.glob("*.html")
               if CLAIM.search(io.open(f, encoding="utf-8", errors="replace").read()))
    print("  files affected     : %d" % files)
    print("  body occurrences   : %d" % body)
    print("  schema occurrences : %d" % schema)
    print("  absolute phrases   : %d" % absolutes)
    print("  live pages carrying the claim %s: %d"
          % ("after" if apply else "right now", left))
    print()
    print("  %s" % ("APPLIED" if apply else "DRY RUN - nothing written. Re-run with --apply."))


if __name__ == "__main__":
    main()
