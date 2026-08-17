"""Upload upload-queue/ to the live host over SFTP.

Reads connection settings from .env (never committed - see .gitignore):

    DEPLOY_HOST=82.197.82.42
    DEPLOY_PORT=65002
    DEPLOY_USER=u628828002
    DEPLOY_KEY=C:\\Users\\...\\.ssh\\id_ed25519    # preferred
    # DEPLOY_PASS=...                              # fallback if no key
    DEPLOY_REMOTE_DIR=public_html

Usage:
    python tools/deploy_sftp.py --dry-run     # show what would upload, connect nothing
    python tools/deploy_sftp.py --check       # test auth + list remote dir only
    python tools/deploy_sftp.py               # upload for real

Also importable:  from deploy_sftp import deploy;  deploy(dry_run=False)
"""
import argparse
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
UPLOAD_QUEUE = REPO / "upload-queue"

# Never ship these to a public web root - content-calendar.json is the entire
# editorial plan, including unpublished titles and target keywords.
EXCLUDE = {"content-calendar.json", ".DS_Store", "Thumbs.db"}


def load_env():
    """Minimal .env parser - avoids a python-dotenv dependency."""
    env = {}
    f = REPO / ".env"
    if not f.exists():
        return env
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
    return env


def settings():
    env = load_env()
    cfg = {
        "host": env.get("DEPLOY_HOST") or os.environ.get("DEPLOY_HOST"),
        "port": int(env.get("DEPLOY_PORT") or os.environ.get("DEPLOY_PORT") or 22),
        "user": env.get("DEPLOY_USER") or os.environ.get("DEPLOY_USER"),
        "key": env.get("DEPLOY_KEY") or os.environ.get("DEPLOY_KEY"),
        "password": env.get("DEPLOY_PASS") or os.environ.get("DEPLOY_PASS"),
        "remote": (env.get("DEPLOY_REMOTE_DIR")
                   or os.environ.get("DEPLOY_REMOTE_DIR") or "public_html"),
    }
    missing = [k for k in ("host", "user") if not cfg[k]]
    if missing:
        raise SystemExit(f"ERROR: .env missing {', '.join('DEPLOY_' + m.upper() for m in missing)}")
    if not cfg["key"] and not cfg["password"]:
        raise SystemExit("ERROR: set DEPLOY_KEY (preferred) or DEPLOY_PASS in .env")
    return cfg


def files_to_send():
    """Every file under upload-queue/, as (local_path, relative_posix_path)."""
    if not UPLOAD_QUEUE.exists():
        return []
    out = []
    for p in sorted(UPLOAD_QUEUE.rglob("*")):
        if p.is_file() and p.name not in EXCLUDE:
            out.append((p, p.relative_to(UPLOAD_QUEUE).as_posix()))
    return out


def _mkdirs(sftp, remote_dir):
    """mkdir -p over SFTP."""
    parts, cur = remote_dir.strip("/").split("/"), ""
    for part in parts:
        cur = f"{cur}/{part}" if cur else part
        try:
            sftp.stat(cur)
        except FileNotFoundError:
            sftp.mkdir(cur)


def deploy(dry_run=False, check_only=False, verbose=True):
    cfg = settings()
    items = files_to_send()

    if not items and not check_only:
        print("upload-queue/ is empty - nothing to deploy.")
        return 0

    if dry_run:
        print(f"DRY RUN - would connect {cfg['user']}@{cfg['host']}:{cfg['port']}")
        print(f"          remote root: {cfg['remote']}")
        print(f"          {len(items)} file(s):")
        for local, rel in items:
            print(f"            {rel:60s} {local.stat().st_size:>9,} bytes")
        skipped = [p.name for p in UPLOAD_QUEUE.rglob("*")
                   if p.is_file() and p.name in EXCLUDE]
        if skipped:
            print(f"          excluded (never published): {', '.join(sorted(set(skipped)))}")
        return 0

    import paramiko  # imported late so --dry-run works without it

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connect_kw = dict(hostname=cfg["host"], port=cfg["port"], username=cfg["user"],
                      timeout=30, auth_timeout=30, look_for_keys=False, allow_agent=False)
    if cfg["key"]:
        connect_kw["key_filename"] = cfg["key"]
    else:
        connect_kw["password"] = cfg["password"]

    try:
        client.connect(**connect_kw)
    except paramiko.AuthenticationException:
        print(f"ERROR: authentication failed for {cfg['user']}@{cfg['host']}:{cfg['port']}\n"
              "       Verify DEPLOY_USER/DEPLOY_HOST/DEPLOY_PORT against hPanel > Advanced >\n"
              "       SSH Access, and that the public key is registered there.")
        return 2
    except Exception as e:
        print(f"ERROR: could not connect - {type(e).__name__}: {e}")
        return 2

    sent = 0
    try:
        sftp = client.open_sftp()
        try:
            sftp.stat(cfg["remote"])
        except FileNotFoundError:
            print(f"ERROR: remote dir {cfg['remote']!r} not found. Home contains: "
                  f"{', '.join(sorted(sftp.listdir('.'))[:15])}")
            return 3

        if check_only:
            print(f"AUTH OK  {cfg['user']}@{cfg['host']}:{cfg['port']}")
            print(f"home    : {sftp.normalize('.')}")
            print(f"remote  : {cfg['remote']} ->")
            for n in sorted(sftp.listdir(cfg["remote"]))[:20]:
                print(f"          {n}")
            return 0

        for local, rel in items:
            target = f"{cfg['remote']}/{rel}"
            parent = target.rsplit("/", 1)[0]
            if parent != cfg["remote"]:
                _mkdirs(sftp, parent)
            sftp.put(str(local), target)
            sent += 1
            if verbose:
                print(f"  uploaded {rel}")
    finally:
        client.close()

    print(f"Deployed {sent} file(s) to {cfg['host']}:{cfg['remote']}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="list what would upload; makes no connection")
    ap.add_argument("--check", action="store_true",
                    help="test auth and list the remote dir; uploads nothing")
    args = ap.parse_args()
    sys.exit(deploy(dry_run=args.dry_run, check_only=args.check))


if __name__ == "__main__":
    main()
