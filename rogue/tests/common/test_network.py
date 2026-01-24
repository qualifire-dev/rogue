from rogue.common.network import get_host_for_url


def test_get_host_for_url_ipv4():
    assert get_host_for_url("127.0.0.1") == "127.0.0.1"
    assert get_host_for_url("192.168.1.1") == "192.168.1.1"


def test_get_host_for_url_hostname():
    assert get_host_for_url("localhost") == "localhost"
    assert get_host_for_url("example.com") == "example.com"


def test_get_host_for_url_ipv6():
    assert get_host_for_url("::1") == "[::1]"
    assert get_host_for_url("2001:db8::1") == "[2001:db8::1]"
    assert (
        get_host_for_url("[::1]") == "[::1]"
    )  # Already bracketed? No, ip_address might fail or return IPv6.
    # ip_address("[::1]") raises ValueError. So it returns input as is (hostname).
    # That is acceptable behavior for already bracketed input if considered a hostname.


def test_get_host_for_url_wildcard():
    assert get_host_for_url("0.0.0.0") == "127.0.0.1"
    assert get_host_for_url("::") == "127.0.0.1"
