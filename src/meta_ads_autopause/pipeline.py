"""One full check (fetch → evaluate → gatekeeper). Shared by the CLI and the MCP server."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from .actions import apply_decisions
from .config import Config
from .meta_client import MetaClient
from .rules import Decision, evaluate_all

@dataclass
class CheckResult:
    time: str
    dry_run: bool
    scope: str
    summary: List[str]
    
    
def describe_scope(config: Config) -> str:
    if config.allowed_campaign_ids is None:
        return "all campaigns"
    return "campaigns " + ", ".join(config.allowed_campaign_ids)


def preview(config: Config) -> List[Decision]:
    """Judge every ad but change nothing and log nothing."""
    client = MetaClient(config)
    now = datetime.now(client.tz)
    return evaluate_all(client.get_ad_performance(), config.rule, now)

def run_check(config: Config) -> CheckResult:
    """The full agent: judge every ad, then let the gatekeeper act and log."""
    client = MetaClient(config)
    now = datetime.now(client.tz)
    decisions = evaluate_all(client.get_ad_performance(), config.rule, now)
    summary = apply_decisions(decisions, client, config, now)
    return CheckResult(
        time=now.isoformat(),
        dry_run=config.dry_run,
        scope=describe_scope(config),
        summary=summary,
    )
    
    


