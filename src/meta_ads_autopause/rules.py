"""Pure decision logic: AdStats in, decisions out. Never talks to Meta."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from .config import Rule
from .meta_client import AdStats


@dataclass(frozen=True)
class Decision:
    ad: AdStats
    should_pause: bool
    reason: str
    
def evaluate_ad(ad: AdStats, rule: Rule, now: datetime) -> Decision:
    age_hours = (now - ad.created_time).total_seconds() / 3600
    
    if age_hours < rule.min_ad_age_hours:
        return Decision(ad, False, f"too new ({age_hours:.1f}h old, minimum {rule.min_ad_age_hours}h)")
    
    if ad.link_clicks >= rule.min_link_clicks:
        return Decision(ad, False, f"has {ad.link_clicks} link clicks (minimum {rule.min_link_clicks})")   
    
    if ad.spend <= rule.spend_threshold:
        return Decision(ad, False, f"spend {ad.spend:.2f} is not above {rule.spend_threshold:.2f}")

    return Decision(
        ad, True,
        f"only {ad.link_clicks} link clicks in {rule.window_hours}h "
        f"(minimum {rule.min_link_clicks}), spent R{ad.spend:.2f}",
    )
    
def evaluate_all(ads: List[AdStats], rule: Rule, now: datetime) -> List[Decision]:
    return [evaluate_ad(ad, rule, now) for ad in ads]

        