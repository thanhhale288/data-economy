from crawlers.url_finder.domain import registrable_domain
from crawlers.url_finder.hypothesis import (
    brand_combos,
    hypothesize_hosts,
    hypothesize_slugs,
    hypothesize_urls,
)
from crawlers.url_finder.identity import assert_no_url_fields

RAL = {
    "ticker": "RAL",
    "legal_name": "Công ty Cổ phần Bóng đèn Rạng Đông",
    "tax_id": "0101526991",
    "address": "87-89 phố Hạ Đình, Hà Nội",
    "aliases": ["RALACO", "RANG DONG LIGHT SOURCE AND VACUUM FLASK JOINT STOCK COMPANY"],
}

VNM = {
    "ticker": "VNM",
    "legal_name": "Công ty Cổ phần Sữa Việt Nam",
    "tax_id": "0300588569",
    "aliases": ["VINAMILK", "VIETNAM DAIRY PRODUCTS JOINT STOCK COMPANY"],
}

FPT = {
    "ticker": "FPT",
    "legal_name": "Tập đoàn FPT",
    "tax_id": "0101248141",
    "aliases": ["FPT CORP", "FPT CORPORATION"],
}

GEE = {
    "ticker": "GEE",
    "legal_name": "Công ty Cổ phần Điện Gia Dụng Gelex",
    "tax_id": "0107547109",
    "aliases": ["GELEX ELECTRIC., JSC", "GELEX ELECTRICITY JOINT STOCK COMPANY"],
}


def test_slugs_from_alias_and_name_not_gold_url():
    assert_no_url_fields(RAL, context="hypothesis")
    slugs = hypothesize_slugs(RAL)
    assert "rangdong" in slugs
    assert "ralaco" in slugs
    assert "website_url" not in RAL


def test_vinamilk_and_fpt_brand_slugs():
    assert "vinamilk" in hypothesize_slugs(VNM)
    slugs = hypothesize_slugs(FPT)
    assert "fpt" in slugs
    assert "fptshop" not in slugs


def test_gelex_hyphen_slug():
    slugs = hypothesize_slugs(GEE)
    assert "gelex-electric" in slugs or "gelexelectric" in slugs


TLH = {
    "ticker": "TLH",
    "legal_name": "Công ty Cổ phần Tập đoàn Thép Tiến Lên",
    "tax_id": "3700361744",
    "aliases": ["T.L.C", "TIEN LEN STEEL CORPORATION JOINT - STOCK COMPANY"],
}

GVR = {
    "ticker": "GVR",
    "legal_name": "Tập đoàn Công nghiệp Cao su Việt Nam",
    "tax_id": "0301266564",
    "aliases": ["VRG", "VIETNAM RUBBER GROUP"],
}


def test_hypothesis_urls_are_https_and_tagged():
    hits = hypothesize_urls(VNM, resolve=False)
    assert hits
    assert all(h.url.startswith("https://") for h in hits)
    assert all(h.source == "domain_hypothesis" for h in hits)
    assert any("vinamilk" in h.url for h in hits)


def test_slug_major_order_reaches_every_tld_of_the_first_slug():
    hosts = hypothesize_hosts(GVR)
    assert hosts[:3] == ["vrg.com.vn", "vrg.vn", "vrg.com"]


def test_dotvn_candidate_survives_the_cap():
    # Suffix-major ordering used to spend the whole budget on .com.vn.
    domains = {registrable_domain(h.url) for h in hypothesize_urls(GVR, resolve=False)}
    assert "vrg.vn" in domains


def test_brand_combos_use_generic_tails_only():
    combos = brand_combos(["tienlen", "tien"], ["group", "corp"])
    assert "tienlengroup" in combos
    assert "tienlencorp" in combos
    # -CO acronym stem: NAVICO -> navi(+corp)
    assert "navicorp" in brand_combos(["navico"], ["corp"])
    # A tail already present must not be duplicated.
    assert "tienlengroupgroup" not in brand_combos(["tienlengroup"], ["group"])


def test_combo_hosts_are_generated_and_reachable():
    assert "tienlengroup.vn" in hypothesize_hosts(TLH)
    # Without the DNS prefilter the base slugs fill the default cap, so the combo
    # slice only pays off once dead hosts are dropped (or with a wider limit).
    domains = {
        registrable_domain(h.url) for h in hypothesize_urls(TLH, resolve=False, limit=64)
    }
    assert "tienlengroup.vn" in domains
