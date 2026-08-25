import json

from crawlers.jp_calibration.evaluate import JP_CAVEAT, stamp_jp_caveat
from crawlers.url_finder.evaluate import summarize


def test_stamp_jp_caveat_replaces_vn28_blurb():
    vn_shaped = summarize(
        [
            {
                "hit": False,
                "error_type": "abstain",
                "ticker": "1",
            }
        ]
    )
    assert "n=28" in vn_shaped["caveat"]
    metrics = {
        "caveat": vn_shaped["caveat"],
        "by_stratum": {"0-20": dict(vn_shaped)},
        "by_prefecture": {"大阪府": dict(vn_shaped)},
    }
    stamp_jp_caveat(metrics)
    assert "n=28" not in metrics["caveat"]
    assert metrics["by_stratum"]["0-20"]["caveat"] == JP_CAVEAT
    assert metrics["by_prefecture"]["大阪府"]["caveat"] == JP_CAVEAT
    assert "gBizINFO" in metrics["caveat"]


def test_live_identity_has_no_url_leak():
    from crawlers.jp_calibration.identity import load_jp_identity
    from crawlers.jp_calibration.paths import IDENTITY_FILE

    if not IDENTITY_FILE.exists():
        return
    rows = load_jp_identity()
    assert len(rows) == 300
    blob = json.dumps(rows).lower()
    assert "http" not in blob
    assert "www." not in blob

    vn_shaped = summarize(
        [
            {
                "hit": False,
                "error_type": "abstain",
                "ticker": "1",
            }
        ]
    )
    assert "n=28" in vn_shaped["caveat"]
    metrics = {
        "caveat": vn_shaped["caveat"],
        "by_stratum": {"0-20": dict(vn_shaped)},
        "by_prefecture": {"大阪府": dict(vn_shaped)},
    }
    stamp_jp_caveat(metrics)
    assert "n=28" not in metrics["caveat"]
    assert metrics["by_stratum"]["0-20"]["caveat"] == JP_CAVEAT
    assert metrics["by_prefecture"]["大阪府"]["caveat"] == JP_CAVEAT
    assert "gBizINFO" in metrics["caveat"]
