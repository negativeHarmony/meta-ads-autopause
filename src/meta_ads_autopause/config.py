"""Loads settings from environment variables (or a .env file) and an optional rules file."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml
from dotenv import find_dotenv, load_dotenv

DEFAULT_LOG_DIR = Path.home() / ".meta-ads-autopause" / "logs"


@dataclass(frozen=True)
class Rule:
    spend_threshold: float = 0.0
    min_link_clicks: int = 1
    window_hours: int = 24
    min_ad_age_hours: int = 24


@dataclass(frozen=True)
class Config:
    access_token: str = field(repr=False)
    ad_account_id: str
    allowed_campaign_ids: Optional[List[str]]
    dry_run: bool
    max_pauses_per_run: int
    rule: Rule
    log_dir: Path
    
#Helper functions. get envs and parse campaign id lits

def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing {name} in .env")
    return value


def _parse_campaigns(raw: str) -> Optional[List[str]]:
    if raw.strip().upper() == "ALL":
        return None
    ids = [c.strip() for c in raw.split(",") if c.strip()]
    if not ids:
        raise ValueError("ALLOWED_CAMPAIGN_IDS must be campaign IDs or ALL")
    return ids

def _load_rules_file() -> dict:
    path = os.getenv("RULES_FILE", "").strip()
    if not path:
        return {}
    with open(Path(path).expanduser()) as f:
        return yaml.safe_load(f) or {}
    
def load_config() -> Config:
    load_dotenv(find_dotenv(usecwd=True))
    rules = _load_rules_file()

    account_id = _require("META_AD_ACCOUNT_ID")
    if not account_id.startswith("act_"):
        account_id = "act_" + account_id

    return Config(
        access_token=_require("META_ACCESS_TOKEN"),
        ad_account_id=account_id,
        allowed_campaign_ids=_parse_campaigns(_require("ALLOWED_CAMPAIGN_IDS")),
        dry_run=os.getenv("DRY_RUN", "true").strip().lower() != "false",
        max_pauses_per_run=int(rules.get("max_pauses_per_run", 2)),
        rule=Rule(**rules.get("rule", {})),
        log_dir=Path(os.getenv("LOG_DIR", str(DEFAULT_LOG_DIR))).expanduser(),
    )