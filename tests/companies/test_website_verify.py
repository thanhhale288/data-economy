"""Task #80 — website verify honesty from seed / Task #40 audit (no live HTTP)."""

from __future__ import annotations

from datetime import datetime

from backend.app.models import Company, DigitalPresence
from backend.app.services import company_service
from backend.app.services.website_verify import (
    FAIL_NOTE,
    WEBSITE_VERIFY_FAIL,
    extract_stored_website_verify,
    merge_website_verify_into_channels,
    resolve_website_verify,
)


def test_gee_seed_provenance_is_ssl_fail_not_http_code():
    rec = extract_stored_website_verify(
        {
            "website": True,
            "website_verify": {
                "status": "fail",
                "reason": "ssl_unverified",
                "source": "epic3_task40_audit",
            },
        }
    )
    assert rec.status == WEBSITE_VERIFY_FAIL
    assert rec.reason == "ssl_unverified"
    assert rec.reason != "500"
    assert "ssl" in rec.reason


def test_resolve_prefers_stored_provenance_over_ticker_fallback():
    rec = resolve_website_verify(
        stock_code="GEE",
        website_url="https://gelex-electric.com",
        digital_channels={
            "website_verify": {"status": "unknown", "reason": "not_measured"}
        },
    )
    assert rec.status == "unknown"
    assert rec.reason == "not_measured"


def test_gee_documented_audit_fallback_when_channels_lack_verify():
    rec = resolve_website_verify(
        stock_code="GEE",
        website_url="https://gelex-electric.com",
        digital_channels={"website": True, "shopee": False},
    )
    assert rec.status == "fail"
    assert rec.reason == "ssl_unverified"


def test_ok_ticker_is_not_fail_without_provenance():
    rec = resolve_website_verify(
        stock_code="RAL",
        website_url="https://rangdong.com.vn",
        digital_channels={"website": True, "shopee": True},
    )
    assert rec.status is None
    assert rec.shows_chip is False


def test_fail_does_not_imply_no_ecommerce_copy():
    assert "không có TMĐT" not in FAIL_NOTE.lower()
    assert "checkout" in FAIL_NOTE.lower()  # warns not to infer it


def test_merge_top_level_seed_fields_into_channels():
    channels = merge_website_verify_into_channels(
        {
            "website_verify_status": "fail",
            "website_verify_reason": "ssl_unverified",
            "digital_channels": {"website": True, "shopee": False},
        }
    )
    assert channels["website"] is True
    assert channels["website_verify"]["status"] == "fail"
    assert channels["website_verify"]["reason"] == "ssl_unverified"


def test_list_and_detail_flag_gee_not_ral(db_session):
    gee = Company(
        stock_code="GEE",
        name="Gelex Electric",
        vsic_code="2710",
        exchange="HOSE",
        website_url="https://gelex-electric.com",
        has_ecommerce_site=False,
        digital_channels={
            "website": True,
            "website_verify": {
                "status": "fail",
                "reason": "ssl_unverified",
                "source": "epic3_task40_audit",
            },
        },
    )
    ral = Company(
        stock_code="RAL",
        name="Rạng Đông",
        vsic_code="2740",
        exchange="HOSE",
        website_url="https://rangdong.com.vn",
        has_ecommerce_site=True,
        digital_channels={"website": True, "shopee": True},
    )
    db_session.add_all([gee, ral])
    db_session.flush()
    db_session.add(
        DigitalPresence(
            company_id=gee.id,
            channel_type="website",
            url="https://gelex-electric.com",
            is_active=True,
            has_checkout=False,
            match_confidence=1.0,
            crawled_at=datetime(2024, 6, 1),
        )
    )
    db_session.add(
        DigitalPresence(
            company_id=ral.id,
            channel_type="website",
            url="https://rangdong.com.vn",
            is_active=True,
            has_checkout=True,
            match_confidence=1.0,
            crawled_at=datetime(2024, 6, 1),
        )
    )
    db_session.commit()

    listed = {row.stock_code: row for row in company_service.list_companies(db_session)}
    assert listed["GEE"].website_verify_status == "fail"
    assert listed["GEE"].website_verify_reason == "ssl_unverified"
    assert listed["RAL"].website_verify_status is None

    gee_detail = company_service.get_company(db_session, "GEE")
    assert gee_detail.website_verify_status == "fail"
    assert any("ssl_unverified" in n for n in gee_detail.data_quality.notes)
    assert all("không có TMĐT" not in n for n in gee_detail.data_quality.notes)

    ral_detail = company_service.get_company(db_session, "RAL")
    assert ral_detail.website_verify_status is None
    assert all("ssl_unverified" not in n for n in ral_detail.data_quality.notes)


def test_gee_seed_file_records_task40_ssl_fail():
    import json
    from pathlib import Path

    seed = json.loads(
        (Path(__file__).resolve().parents[2] / "data" / "seeds" / "companies.json").read_text(
            encoding="utf-8"
        )
    )
    rows = seed["companies"] if isinstance(seed, dict) else seed
    gee = next(c for c in rows if c["stock_code"] == "GEE")
    assert gee["website_url"] == "https://gelex-electric.com"
    assert gee["website_verify_status"] == "fail"
    assert gee["website_verify_reason"] == "ssl_unverified"
    assert gee["digital_channels"]["website_verify"]["status"] == "fail"
    # Storage default is not a measured "no ecommerce" conclusion.
    assert gee["has_ecommerce_site"] is False
