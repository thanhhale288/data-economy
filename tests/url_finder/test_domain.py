from crawlers.url_finder.domain import domains_match, host_from_url, registrable_domain


def test_strips_www_and_scheme():
    assert registrable_domain("https://www.hoaphat.com.vn/path") == "hoaphat.com.vn"
    assert host_from_url("https://www.hoaphat.com.vn/path") == "www.hoaphat.com.vn"


def test_com_vn_is_one_public_suffix():
    assert registrable_domain("https://rangdong.com.vn") == "rangdong.com.vn"
    assert domains_match("http://rangdong.com.vn/", "https://www.rangdong.com.vn/about")


def test_fpt_corporate_is_not_fptshop():
    assert not domains_match("https://fpt.com.vn", "https://fptshop.com.vn")
    assert registrable_domain("https://fptshop.com.vn") == "fptshop.com.vn"


def test_empty_url():
    assert registrable_domain("") == ""
    assert not domains_match("", "https://example.com")


def test_co_jp_is_one_public_suffix():
    assert registrable_domain("https://www.aisin.com/jp/") == "aisin.com"
    assert registrable_domain("https://www.toyota.co.jp/") == "toyota.co.jp"
    assert domains_match("https://toyota.co.jp/", "https://www.toyota.co.jp/company")
    assert not domains_match("https://toyota.co.jp/", "https://denso.co.jp/")
