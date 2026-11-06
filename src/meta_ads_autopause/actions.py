"""The gatekeeper: the only code that may pause an ad. Enforces every safety rail."""
from __future__ import annotations

from datetime import datetime
from typing import List

from .config import Config
from .decision_log import log_decision
from .meta_client import MetaClient
from .rules import Decision

def apply_decisions(decisions: List[Decision], client: MetaClient, config: Config, now: datetime) -> List[str]:
    pauses_done = 0
    summary = []
    
    for decision in decisions:
        error = None
        allowed  = config.allowed_campaign_ids
        
        if not decision.should_pause:
            action = "kept"
        elif allowed is not None and decision.ad.campaign_id not in allowed:
            action = "blocked_not_allowed"
        elif pauses_done >= config.max_pauses_per_run:
            action = "skipped_limit"
        elif config.dry_run:
            action = "would_pause"
            pauses_done += 1
        else:
            try:
                client.pause_ad(decision.ad.ad_id)
                action = "paused"
                pauses_done += 1
            except Exception as e:
                action = "failed"
                error = str(e)

        log_decision(config.log_dir, decision, action, config.dry_run, now, error)        
        summary.append(f"{action}: {decision.ad.name} ({decision.ad.ad_id}) - {decision.reason}")

    return summary