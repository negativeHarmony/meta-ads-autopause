"""Appends every decision to decisions.jsonl in the log folder, one JSON object per line."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .rules import Decision

LOG_FILENAME = "decisions.jsonl"


def log_decision(log_dir: Path, decision: Decision, action: str, dry_run: bool,
                 now: datetime, error: Optional[str] = None) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "time": now.isoformat(),
        "ad_id": decision.ad.ad_id,
        "ad_name": decision.ad.name,
        "campaign_id": decision.ad.campaign_id,
        "spend": round(decision.ad.spend, 2),
        "link_clicks": decision.ad.link_clicks,
        "reason": decision.reason,
        "action": action,
        "dry_run": dry_run,
        "error": error,
    }
    with open(log_dir / LOG_FILENAME, "a") as f:
        f.write(json.dumps(entry) + "\n")
        
def read_recent(log_dir: Path, limit: int = 20) -> List[dict]:
    path = log_dir / LOG_FILENAME
    if not path.exists():
        return []
    with open(path) as f:
        lines = f.readlines()
    return [json.loads(line) for line in lines[-limit:]]

