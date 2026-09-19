import pytest
import socket
from academic_radar.security.urlpolicy import check_url, check_redirect_chain, UrlBlocked


def mock_resolver_public(host, family=0):
    """Mock resolver that returns a public IP."""
    if host == "example.org":
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
    raise socket.gaierror("Unknown host")


def mock_resolver_localhost(host, family=0):
    """Mock resolver that returns 127.0.0.1 for localhost."""
    if host == "localhost":
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))]
    raise socket.gaierror("Unknown host")


def mock_resolver_private(host, family=0):
    """Mock resolver that returns a private IP."""
    if host == "internal.local":
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 0))]
    raise socket.gaierror("Unknown host")


def mock_resolver_metadata(host, family=0):
    """Mock resolver for metadata endpoint."""
    if host == "169.254.169.254":
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 0))]
    raise socket.gaierror("Unknown host")


class TestCheckUrl:
    def test_allowed_https_public_ip(self):
        """HTTPS with public IP should be allowed."""
        check_url("https://example.org/path", resolver=mock_resolver_public)

    def test_blocked_file_scheme(self):
        """file:// scheme should be blocked."""
        with pytest.raises(UrlBlocked) as exc_info:
            check_url("file:///etc/passwd")
        assert "scheme" in str(exc_info.value).lower()

    def test_blocked_ftp_scheme(self):
        """ftp:// scheme should be blocked."""
        with pytest.raises(UrlBlocked) as exc_info:
            check_url("ftp://example.org/file.txt")
        assert "scheme" in str(exc_info.value).lower()

    def test_blocked_loopback_127_0_0_1(self):
        """http://127.0.0.1 should be blocked."""
        with pytest.raises(UrlBlocked) as exc_info:
            check_url("http://127.0.0.1", resolver=socket.getaddrinfo)
        assert "loopback" in str(exc_info.value).lower()

    def test_blocked_localhost(self):
        """http://localhost should be blocked (resolves to 127.0.0.1)."""
        with pytest.raises(UrlBlocked) as exc_info:
            check_url("http://localhost", resolver=mock_resolver_localhost)
        assert "loopback" in str(exc_info.value).lower()

    def test_blocked_private_ip(self):
        """http://10.0.0.5 should be blocked (private range)."""
        with pytest.raises(UrlBlocked) as exc_info:
            check_url("http://internal.local", resolver=mock_resolver_private)
        assert "private" in str(exc_info.value).lower()

    def test_blocked_metadata_endpoint(self):
        """http://169.254.169.254/latest/meta-data should be blocked."""
        with pytest.raises(UrlBlocked) as exc_info:
            check_url("http://169.254.169.254/latest/meta-data", resolver=mock_resolver_metadata)
        assert "metadata" in str(exc_info.value).lower()

    def test_blocked_ipv6_loopback(self):
        """http://[::1]/ should be blocked (IPv6 loopback)."""
        with pytest.raises(UrlBlocked) as exc_info:
            check_url("http://[::1]/")
        assert "loopback" in str(exc_info.value).lower()

    def test_blocked_ipv6_mapped_loopback(self):
        """http://[::ffff:127.0.0.1]/ should be blocked (IPv4-mapped loopback)."""
        with pytest.raises(UrlBlocked) as exc_info:
            check_url("http://[::ffff:127.0.0.1]/")
        assert "loopback" in str(exc_info.value).lower()

    def test_blocked_userinfo(self):
        """http://user:pw@example.org/ should be blocked (userinfo in URL)."""
        with pytest.raises(UrlBlocked) as exc_info:
            check_url("http://user:pw@example.org/", resolver=mock_resolver_public)
        assert "userinfo" in str(exc_info.value).lower()

    def test_blocked_missing_host(self):
        """URL without host should be blocked."""
        with pytest.raises(UrlBlocked) as exc_info:
            check_url("http:///path")
        assert "host" in str(exc_info.value).lower()


class TestCheckRedirectChain:
    def test_chain_of_allowed_urls(self):
        """Chain of 3 allowed URLs should pass."""
        urls = [
            "https://example.org/page1",
            "https://example.org/page2",
            "https://example.org/page3",
        ]
        check_redirect_chain(urls, resolver=mock_resolver_public)

    def test_chain_exceeding_5_hops(self):
        """Chain of 6 URLs should be blocked (max 5)."""
        urls = [
            "https://example.org/1",
            "https://example.org/2",
            "https://example.org/3",
            "https://example.org/4",
            "https://example.org/5",
            "https://example.org/6",
        ]
        with pytest.raises(UrlBlocked) as exc_info:
            check_redirect_chain(urls, resolver=mock_resolver_public)
        assert "redirect" in str(exc_info.value).lower() or "hop" in str(exc_info.value).lower()

    def test_chain_with_private_ip_at_third_hop(self):
        """Chain where 3rd hop is private should be blocked."""
        def mock_resolver_mixed(host, family=0):
            if host == "example.org":
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
            elif host == "internal.local":
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 0))]
            raise socket.gaierror("Unknown host")

        urls = [
            "https://example.org/page1",
            "https://example.org/page2",
            "http://internal.local/page3",  # 3rd hop is private
        ]
        with pytest.raises(UrlBlocked) as exc_info:
            check_redirect_chain(urls, resolver=mock_resolver_mixed)
        assert "private" in str(exc_info.value).lower()
