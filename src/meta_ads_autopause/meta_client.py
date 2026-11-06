"""The only module that talks to Meta: reads ads and their recent numbers."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.api import FacebookAdsApi

from .config import Config

HOUR_BREAKDOWN = "hourly_stats_aggregated_by_advertiser_time_zone"

#convert meta response Adstats object


@dataclass(frozen=True)
class AdStats:
    ad_id: str
    name: str
    campaign_id: str
    created_time: datetime
    spend: float
    link_clicks: int
    
    
class MetaClient:
    def __init__(self, config: Config):
        self.config = config
        FacebookAdsApi.init(access_token=config.access_token)
        self.account = AdAccount(config.ad_account_id)
        self.tz = self._account_timezone()

    def _account_timezone(self) -> timezone:
        info = self.account.api_get(fields=["timezone_offset_hours_utc"])
        return timezone(timedelta(hours=float(info["timezone_offset_hours_utc"])))
    
    def active_ads(self) -> List[dict]:
        ads = self.account.get_ads(
            fields = ["id", "name", "campaign_id", "created_time"],
            params = {"effective_status": ["ACTIVE"], "limit": 100}
        )
        allowed = self.config.allowed_campaign_ids
        return [ad for ad in ads if allowed is None or ad["campaign_id"] in allowed]
    
    def _recent_numbers(self, now: datetime) -> Dict[str, dict]:
        window_start = now - timedelta(hours=self.config.rule.window_hours)
        rows = self.account.get_insights(
            fields=["ad_id", "spend", "inline_link_clicks"],
            params = {
                "level": "ad",
                "time_range": {
                    "since": window_start.strftime("%Y-%m-%d"),
                    "until": now.strftime("%Y-%m-%d")
                },
                "time_increment": 1,
                "breakdowns": [HOUR_BREAKDOWN],
                "limit": 500,
            },
        )
        
        totals = defaultdict(lambda: {"spend": 0.0, "link_clicks": 0})
        for row in rows:
            hour = int(row[HOUR_BREAKDOWN][:2])
            bucket_start = datetime.strptime(row["date_start"], "%Y-%m-%d").replace(
                hour=hour ,tzinfo=self._account_timezone
            )
            if bucket_start + timedelta(hours=1) <= window_start: #only add to totals dict is ad is within the 24 hour window
                continue
            totals[row["ad_id"]]["spend"] += float(row.get("spend", 0))               #{"111": {"spend": 25.8, "link_clicks": 0},
#                                                                                            "222": {"spend": 3.0,  "link_clicks": 2}}
            totals[row["ad_id"]]["link_clicks"] += int(row.get("inline_link_clicks", 0))
        return totals
    
    def get_ad_performance(self) -> List[AdStats]:
        now = datetime.now(self.tz)
        numbers = self._recent_numbers(now)
        results = []
        for ad in self.active_ads():
            n = numbers.get(ad["id"], {"spend": 0.0, "link_clicks": 0})
            results.append(
                AdStats(
                    ad_id=ad["id"],
                    name=ad["name"],
                    campaign_id=ad["campaign_id"],
                    created_time=datetime.strptime(ad["created_time"], "%Y-%m-%dT%H:%M:%S%z"),
                    spend=n["spend"],
                    link_clicks=n["link_clicks"],
                )
            )
        return results
    
    def pause_ad(self, ad_id: str) -> None:
        Ad(ad_id).api_update(params={"status": "PAUSED"})