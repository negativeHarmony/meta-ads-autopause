"""MCP server: exposes the autopause agent as tools any MCP client can call."""
from __future__ import annotations

from dataclasses import asdict

from mcp.server.mcpserver import MCPServer


from .config import load_config
from .decision_log import read_recent
from .meta_client import AdStats
from .pipeline import describe_scope, preview
from .pipeline import run_check as run_pipeline

mcp = MCPServer("meta-ads-autopause")

def _call(fn):
    """Load settings, run fn, and make sure errors never leak the access token."""
    config = load_config()
    try:
        return fn(config)
    except Exception as e:
        raise RuntimeError(str(e).replace(config.access_token, "[REDACTED]")) from None
    
def _ad_dict(ad: AdStats) -> dict:
    return {
        "ad_id": ad.ad_id,
        "name": ad.name,
        "campaign_id": ad.campaign_id,
        "created_time": ad.created_time.isoformat(),
        "spend": round(ad.spend, 2),
        "link_clicks": ad.link_clicks,
    }
    
@mcp.tool()
def run_check() -> dict:
    """Run one full autopause check: fetch active ads in scope, apply the pause rule,
    and pause ads that fail it. When DRY_RUN is on (the default) nothing is paused;
    decisions are only logged as 'would_pause'. The server enforces the campaign
    allowlist and a maximum number of pauses per run. Returns a summary of every decision."""
    return _call(lambda config: asdict(run_pipeline(config)))


@mcp.tool()
def preview_decisions() -> list[dict]:
    """Show what the pause rule WOULD do to each active ad right now, with the reason.
    Read-only: never pauses anything and does not write to the decision log."""
    def go(config):
        return [
            {**_ad_dict(d.ad), "would_pause": d.should_pause, "reason": d.reason}
            for d in preview(config)
        ]
    return _call(go)

@mcp.tool()
def get_ad_performance() -> list[dict]:
    """List active ads in scope with their spend (in the ad account's currency) and
    link clicks over the rule's time window. Read-only."""
    def go(config):
        from .meta_client import MetaClient
        return [_ad_dict(ad) for ad in MetaClient(config).get_ad_performance()]
    return _call(go)
    

@mcp.tool()
def get_decision_log(limit: int = 20) -> list[dict]:
    """Return the most recent decisions (newest last): what was paused, kept,
    skipped or would have been paused, and why. Read-only."""
    return _call(lambda config: read_recent(config.log_dir, limit))

@mcp.tool()
def get_settings() -> dict:
    """Show the current settings: dry-run on/off, which campaigns are in scope,
    the pause rule and the max pauses per run. Never includes the access token. Read-only."""
    def go(config):
        return {
            "ad_account_id": config.ad_account_id,
            "dry_run": config.dry_run,
            "scope": describe_scope(config),
            "max_pauses_per_run": config.max_pauses_per_run,
            "rule": asdict(config.rule),
        }
    return _call(go)

def main() -> None:
    mcp.run()
    
if __name__ == "__main__":
    main()