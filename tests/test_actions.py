from datetime import datetime, timedelta, timezone



from meta_ads_autopause.config import Config, Rule
from meta_ads_autopause.meta_client import AdStats         # test_rules.py
from meta_ads_autopause.actions import apply_decisions    # test_actions.py
from meta_ads_autopause.rules import Decision             # test_actions.py

NOW = datetime(2026, 11, 5, 10, 30, tzinfo=timezone(timedelta(hours=-5)))
RULE = Rule(spend_threshold=10, min_link_clicks=1, window_hours=24, min_ad_age_hours=6)

class FakeClient:
    """Pretends to be MetaClient: records pauses instead of calling Meta."""
    def __init__(self):
        self.paused = []

    def pause_ad(self, ad_id):
        self.paused.append(ad_id)





def make_config(log_dir, dry_run, allowed=None):
    return Config(access_token="fake", ad_account_id="act_1",
                  allowed_campaign_ids=allowed, dry_run=dry_run,
                  max_pauses_per_run=2, rule=RULE, log_dir=log_dir)


def bad_ad(ad_id, campaign_id="999"):
    ad = AdStats(ad_id=ad_id, name=f"Ad {ad_id}", campaign_id=campaign_id,
                 created_time=NOW - timedelta(hours=48), spend=15.0, link_clicks=0)
    return Decision(ad, True, "spent R15.00 with 0 link clicks in 24h")


def test_dry_run_never_pauses(tmp_path):
    client = FakeClient()
    apply_decisions([bad_ad("1")], client, make_config(tmp_path, dry_run=True), NOW)
    assert client.paused == []


def test_live_mode_respects_max_pauses(tmp_path):
    client = FakeClient()
    ads = [bad_ad("1"), bad_ad("2"), bad_ad("3")]
    apply_decisions(ads, client, make_config(tmp_path, dry_run=False), NOW)
    assert client.paused == ["1", "2"]


def test_blocks_ads_outside_allowlist(tmp_path):
    client = FakeClient()
    ad = bad_ad("1", campaign_id="other")
    apply_decisions([ad], client, make_config(tmp_path, dry_run=False, allowed=["999"]), NOW)
    assert client.paused == []