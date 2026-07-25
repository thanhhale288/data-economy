"""Epic 3 Task #33 — batch website detector + marketplace URL audit."""

from __future__ import annotations

from pathlib import Path

from backend.app.models import Company, DigitalPresence
from crawlers.companies.website_audit import (
    WebsiteQaRow,
    apply_db_fixes,
    audit_allowlist,
    audit_ticker,
    seed_flag_mismatches,
    write_audit_report,
)
from crawlers.companies.website_detector import DetectionResult


def _seed_ral() -> dict:
    return {
        "stock_code": "RAL",
        "name": "Công ty Cổ phần Bóng đèn Rạng Đông",
        "vsic_code": "2740",
        "exchange": "HOSE",
        "website_url": "https://rangdong.com.vn",
        "has_ecommerce_site": True,
        "digital_channels": {"website": True, "shopee": True, "tiktok": False},
        "digital_presence": [
            {
                "channel_type": "website",
                "url": "https://rangdong.com.vn",
                "has_checkout": True,
                "match_confidence": 1.0,
            },
            {
                "channel_type": "shopee",
                "url": "https://shopee.vn/rangdong_official",
                "has_checkout": True,
                "match_confidence": 0.95,
            },
        ],
    }


def _seed_flag_without_url() -> dict:
    seed = _seed_ral()
    seed["stock_code"] = "BAD"
    seed["digital_channels"] = {"website": True, "shopee": True, "tiktok": False}
    seed["digital_presence"] = [
        {
            "channel_type": "website",
            "url": "https://example.com",
            "has_checkout": False,
        }
    ]
    return seed


def test_seed_flag_mismatches_detects_marketplace_without_url():
    problems = seed_flag_mismatches(_seed_flag_without_url())
    assert "shopee_flag_without_url" in problems


def test_audit_ticker_detect_fail_leaves_checkout_unknown():
    """Mock detector fail → never invent has_checkout=True."""

    def boom(_url: str) -> DetectionResult:
        return DetectionResult(ok=False, detail="http_fail status=403")

    row = audit_ticker(None, _seed_ral(), detect=boom, detect_enabled=True)
    assert row.website_ok is False
    assert row.has_checkout is None
    assert row.shopee_url == "https://shopee.vn/rangdong_official"
    assert row.flag_vs_url_mismatch == ""


def test_audit_ticker_detect_ok_records_checkout():
    def ok(_url: str) -> DetectionResult:
        return DetectionResult(
            ok=True, has_ecommerce=True, has_checkout=True, detail="ok"
        )

    row = audit_ticker(None, _seed_ral(), detect=ok, detect_enabled=True)
    assert row.website_ok is True
    assert row.has_checkout is True
    assert row.has_ecommerce is True


def test_apply_db_fixes_adds_missing_marketplace_url(db_session):
    """DQC-style drift: seed has shopee URL, DB only has website."""
    seed = _seed_ral()
    company = Company(
        stock_code="RAL",
        name=seed["name"],
        vsic_code="2740",
        exchange="HOSE",
        website_url=seed["website_url"],
        has_ecommerce_site=True,
        digital_channels=seed["digital_channels"],
    )
    db_session.add(company)
    db_session.flush()
    db_session.add(
        DigitalPresence(
            company_id=company.id,
            channel_type="website",
            url="https://rangdong.com.vn",
            has_checkout=True,
            match_confidence=1.0,
        )
    )
    db_session.commit()

    row = WebsiteQaRow(
        stock_code="RAL",
        website_ok=False,
        has_checkout=None,
        shopee_url="https://shopee.vn/rangdong_official",
        tiktok_url=None,
        flag_vs_url_mismatch="",
        db_mismatch="db_missing_shopee_url",
        detect_detail="http_fail status=403",
    )
    summary = apply_db_fixes(db_session, seed, row)
    assert "added_shopee_url" in summary.actions
    assert "website_checkout_unknown_kept_previous" in summary.skipped

    shopee = (
        db_session.query(DigitalPresence)
        .filter_by(company_id=company.id, channel_type="shopee")
        .first()
    )
    assert shopee is not None
    assert shopee.url == "https://shopee.vn/rangdong_official"

    website = (
        db_session.query(DigitalPresence)
        .filter_by(company_id=company.id, channel_type="website")
        .first()
    )
    # Failed detect must not invent checkout=False overwrite — keep prior True.
    assert website.has_checkout is True


def test_apply_db_fixes_live_ok_updates_checkout(db_session):
    seed = _seed_ral()
    company = Company(
        stock_code="RAL",
        name=seed["name"],
        vsic_code="2740",
        exchange="HOSE",
        website_url=seed["website_url"],
        has_ecommerce_site=True,
        digital_channels=seed["digital_channels"],
    )
    db_session.add(company)
    db_session.flush()
    db_session.add(
        DigitalPresence(
            company_id=company.id,
            channel_type="website",
            url="https://rangdong.com.vn",
            has_checkout=False,
            match_confidence=1.0,
        )
    )
    db_session.add(
        DigitalPresence(
            company_id=company.id,
            channel_type="shopee",
            url="https://shopee.vn/rangdong_official",
            has_checkout=True,
            match_confidence=0.95,
        )
    )
    db_session.commit()

    row = WebsiteQaRow(
        stock_code="RAL",
        website_ok=True,
        has_checkout=True,
        shopee_url="https://shopee.vn/rangdong_official",
        tiktok_url=None,
        flag_vs_url_mismatch="",
        detect_detail="ok",
    )
    summary = apply_db_fixes(db_session, seed, row)
    assert "updated_website_has_checkout_from_live" in summary.actions
    website = (
        db_session.query(DigitalPresence)
        .filter_by(company_id=company.id, channel_type="website")
        .first()
    )
    assert website.has_checkout is True


def test_write_audit_report_columns(tmp_path):
    rows = [
        WebsiteQaRow(
            stock_code="RAL",
            website_ok=True,
            has_checkout=True,
            shopee_url="https://shopee.vn/rangdong_official",
            tiktok_url=None,
            flag_vs_url_mismatch="",
            detect_detail="ok",
        )
    ]
    md_path, csv_path = write_audit_report(rows, report_dir=tmp_path, stem="t33-test")
    csv_text = csv_path.read_text(encoding="utf-8")
    header = csv_text.splitlines()[0]
    for col in (
        "stock_code",
        "website_ok",
        "has_checkout",
        "shopee_url",
        "tiktok_url",
        "flag_vs_url_mismatch",
    ):
        assert col in header
    assert "RAL" in csv_text
    assert md_path.exists()


def test_audit_allowlist_no_detect_skips_http(tmp_path, monkeypatch):
    """Offline mode never calls detect_website."""

    def boom(_url: str) -> DetectionResult:
        raise AssertionError("detect should not be called with detect_enabled=False")

    monkeypatch.setattr(
        "crawlers.companies.website_audit.load_seed_companies",
        lambda tickers=None: [_seed_ral()],
    )
    rows = audit_allowlist(
        None,
        tickers=["RAL"],
        detect=boom,
        detect_enabled=False,
        sleep_s=0,
    )
    assert len(rows) == 1
    assert rows[0].website_ok is None
    assert rows[0].has_checkout is None
    assert rows[0].shopee_url
    write_audit_report(rows, report_dir=tmp_path, stem="t33-offline")
