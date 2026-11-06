"""Entry point: one full check of the ad account. Run hourly by launchd."""
from __future__ import annotations

import argparse
import sys
from dataclasses import replace

from .config import load_config
from .pipeline import run_check

#parse_args() says exactly as before

def parse_args():
    parser = argparse.ArgumentParser(description="Pause Meta ads that spend without clicks.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Force dry-run, even if .env says DRY_RUN=false")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config()
    if args.dry_run:
        config = replace(config, dry_run=True)

    try:
        result = run_check(config)
    except Exception as e:
        message = str(e).replace(config.access_token, "[REDACTED]")
        print(f"ERROR: {type(e).__name__}: {message}", file=sys.stderr)
        return 1

    mode = "DRY RUN" if result.dry_run else "LIVE"
    print(f"[{result.time}] {mode} - checking {result.scope}")
    if not result.summary:
        print("  No active ads found.")
    for line in result.summary:
        print("  " + line)
    return 0

if __name__ == "__main__":
    sys.exit(main())