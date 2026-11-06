from datetime import datetime, timedelta, timezone

from meta_ads_autopause.config import Config, Rule
from meta_ads_autopause.meta_client import AdStats
from meta_ads_autopause.rules import evaluate_ad          # test_rules.py


EASTERN = timezone(timedelta(hours=-5))
NOW = datetime(2026, 11, 5, 10, 30, tzinfo=EASTERN)
RULE = Rule(spend_threshold=40, min_link_clicks=1, window_hours=24, min_ad_age_hours=6)


def make_ad(spend, clicks, age_hours=48):
    return AdStats(
        ad_id="111", name="Cap ad A", campaign_id="999",
        created_time=NOW - timedelta(hours=age_hours),
        spend=spend, link_clicks=clicks,
    )
    
def test_pauses_ad_that_spent_too_much_with_no_clicks():
    assert evaluate_ad(make_ad(spend=45, clicks=0), RULE, NOW).should_pause


def test_keeps_ad_with_a_click(tmp_path):
    assert not evaluate_ad(make_ad(spend=45, clicks=1), RULE, NOW).should_pause


def test_keeps_ad_under_threshold(tmp_path):
    # Ad 111 from the Lesson 2 walkthrough
    assert not evaluate_ad(make_ad(spend=25.8, clicks=0), RULE, NOW).should_pause


def test_exactly_at_threshold_is_kept(tmp_path):
    assert not evaluate_ad(make_ad(spend=40, clicks=0), RULE, NOW).should_pause


def test_keeps_ad_that_is_too_new(tmp_path):
    assert not evaluate_ad(make_ad(spend=45, clicks=0, age_hours=3), RULE, NOW).should_pause