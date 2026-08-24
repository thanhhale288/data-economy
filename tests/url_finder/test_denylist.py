from crawlers.url_finder.denylist import is_aggregator_host


def test_cafef_and_wikipedia_are_aggregators():
    assert is_aggregator_host("https://s.cafef.vn/hose/RAL.chn")
    assert is_aggregator_host("https://vi.wikipedia.org/wiki/Vinamilk")
    assert is_aggregator_host("https://masothue.com/0101526991-x")


def test_tax_directory_hosts_are_aggregators():
    assert is_aggregator_host("https://hosocongty.vn/cong-ty-x.htm")
    assert is_aggregator_host("https://note8.vn/ma-so-thue/x")
    assert is_aggregator_host("https://congty.com/")
    assert not is_aggregator_host("https://vinamilk.com.vn")
