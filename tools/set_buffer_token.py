#!/usr/bin/env python3
"""Safely set BUFFER_ACCESS_TOKEN in parlevu-global-services-llc/.env.

Run this instead of hand-editing .env or pasting a token into a chat. The
token is typed at a hidden prompt, validated against Buffer BEFORE anything
is saved, and never appears in shell history or on screen.

Four things this handles that hand-editing does not:

  secrecy     getpass() hides the input, and the value is never echoed or
              printed back -- not even truncated.
  encoding    PowerShell's `Set-Content -Encoding utf8` writes a BOM, and a
              BOM silently corrupts the FIRST variable in a .env: the reader
              sees a key name with an invisible prefix and the value goes
              missing. This writes UTF-8 with no BOM.
  validation  it calls Buffer's CURRENT API with the token before saving, so
              a typo or an already-expired paste fails now rather than in the
              middle of a campaign.
  discovery   on success it lists the connected channels and their IDs, which
              is what BUFFER_CHANNEL_IDS needs. The old BUFFER_PROFILE_ID in
              this repo is still the literal placeholder
              'your_buffer_profile_id_here'.

Why the API changed: tools/post_to_buffer.py targets Buffer's legacy v1 REST
API (api.bufferapp.com), which Buffer is retiring on 2026-02-01 and which
already answers 401 here. The live API is GraphQL at https://api.buffer.com.
This script validates against the live one, so a token that passes here will
still work after the retirement date.

    python tools/set_buffer_token.py
"""
import io
import json
import os
import shutil
import sys
import urllib.error
import urllib.request
from getpass import getpass

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(REPO, ".env")
KEY = "BUFFER_ACCESS_TOKEN"


def gql(token, query, variables=None):
    body = {"query": query}
    if variables:
        body["variables"] = variables
    req = urllib.request.Request(
        "https://api.buffer.com",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "User-Agent": "parlevu-token-check",
        },
    )
    raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    return json.loads(raw)


def check(token):
    """Ask Buffer who this token belongs to. Returns (ok, detail, channels)."""
    try:
        d = gql(token, "query { account { organizations { id name } } }")
    except urllib.error.HTTPError as e:
        return False, "Buffer rejected it: HTTP %s" % e.code, []
    except Exception as e:
        return False, "could not reach Buffer: %s" % type(e).__name__, []

    if d.get("errors"):
        return False, "; ".join(x.get("message", "?") for x in d["errors"]), []

    orgs = ((d.get("data") or {}).get("account") or {}).get("organizations") or []
    if not orgs:
        return False, "token works but the account has no organizations", []

    channels = []
    for org in orgs:
        try:
            c = gql(
                token,
                "query($id: OrganizationId!) { channels(input: { organizationId: $id }) "
                "{ id name service } }",
                {"id": org["id"]},
            )
            for ch in ((c.get("data") or {}).get("channels") or []):
                channels.append({"org": org.get("name"), **ch})
        except Exception:
            pass  # organisation listed but channels unreadable; not fatal

    return True, ", ".join(o.get("name", "?") for o in orgs), channels


def write_env(token):
    """Replace or append KEY, preserving every other line. UTF-8, no BOM."""
    with io.open(ENV, encoding="utf-8-sig") as fh:
        lines = fh.read().splitlines()

    out, replaced = [], False
    for line in lines:
        if line.strip().startswith(KEY + "=") or line.strip().startswith(KEY + " ="):
            out.append(KEY + "=" + token)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(KEY + "=" + token)

    shutil.copyfile(ENV, ENV + ".bak")
    with io.open(ENV, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    return replaced


def main():
    if not os.path.exists(ENV):
        sys.exit("no .env at %s" % ENV)

    print("Get a token at: Buffer -> Settings -> Apps & Extras -> Create Access Token")
    print("Nothing is saved until Buffer confirms the token is valid.\n")

    token = getpass("Paste the new Buffer access token (input hidden): ").strip()
    if not token:
        sys.exit("nothing entered, no change made")

    print("checking it against Buffer...")
    ok, detail, channels = check(token)
    if not ok:
        sys.exit("FAILED: %s\n.env was NOT modified." % detail)

    print("OK - token belongs to: %s" % detail)
    replaced = write_env(token)
    print("%s %s in .env (backup at .env.bak)"
          % ("Replaced" if replaced else "Appended", KEY))

    if channels:
        print("\nConnected channels (%d):" % len(channels))
        for ch in channels:
            print("   %-12s %-24s id=%s"
                  % (ch.get("service"), ch.get("name"), ch.get("id")))
        print("\nAdd the ones you want to post to:")
        print("   BUFFER_CHANNEL_IDS=%s"
              % ",".join(ch["id"] for ch in channels if ch.get("id")))
    else:
        print("\nNo channels returned. Connect at least one in Buffer, then re-run.")

    print("\nNote: tools/post_to_buffer.py still targets the legacy v1 API that")
    print("Buffer retires 2026-02-01. It needs porting to GraphQL before it will")
    print("work with this token.")


if __name__ == "__main__":
    main()
