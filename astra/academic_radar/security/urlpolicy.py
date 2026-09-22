import socket
import ipaddress
from urllib.parse import urlparse


class UrlBlocked(Exception):
    """Raised when a URL is blocked by SSRF policy."""
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def check_url(url, resolver=socket.getaddrinfo):
    """
    Check if a URL is allowed according to SSRF policy.

    Raises UrlBlocked if:
    - scheme is not http or https
    - host is missing
    - URL contains userinfo (user:password)
    - resolved IP is loopback, private, link-local, multicast, reserved, unspecified
    - resolved IP is cloud metadata (169.254.169.254)

    Args:
        url: URL string to check
        resolver: function for DNS resolution (default: socket.getaddrinfo)

    Raises:
        UrlBlocked: if URL violates SSRF policy
    """
    try:
        parsed = urlparse(url)
        # Reject malformed ports before a transport can interpret the URL differently.
        _ = parsed.port
        hostname = parsed.hostname
    except ValueError as exc:
        raise UrlBlocked(f"Malformed URL: {exc}") from exc

    # Check scheme
    if parsed.scheme not in ("http", "https"):
        raise UrlBlocked(f"Scheme '{parsed.scheme}' is not allowed; only http/https permitted")

    # Check for userinfo
    if parsed.username is not None or parsed.password is not None:
        raise UrlBlocked("URL contains userinfo (username/password); userinfo not allowed")

    # Check host exists
    if not hostname:
        raise UrlBlocked("URL missing hostname")

    # Try to parse as IP address directly first
    try:
        ip = ipaddress.ip_address(hostname)
        _check_ip_blocked(ip)
        return (str(ip),)
    except ValueError:
        # Not an IP address, resolve via DNS
        pass

    # Resolve hostname
    try:
        results = resolver(hostname, socket.AF_UNSPEC)
    except (socket.gaierror, OSError):
        raise UrlBlocked(f"Could not resolve hostname: {hostname}")

    if not results:
        raise UrlBlocked(f"No address records found for hostname: {hostname}")

    # Check all resolved IPs
    addresses = []
    for result in results:
        family, socktype, proto, canonname, sockaddr = result
        ip_str = sockaddr[0]

        try:
            ip = ipaddress.ip_address(ip_str)
            _check_ip_blocked(ip)
            addresses.append(str(ip))
        except ValueError:
            raise UrlBlocked(f"Invalid IP address: {ip_str}")
    return tuple(dict.fromkeys(addresses))


def _check_ip_blocked(ip):
    """
    Check if an IP address is blocked.

    Args:
        ip: ipaddress.IPv4Address or ipaddress.IPv6Address

    Raises:
        UrlBlocked: if IP is in a blocked category
    """
    # Check for metadata endpoint first (169.254.169.254 and IPv6 equivalent)
    if isinstance(ip, ipaddress.IPv4Address):
        if str(ip) == "169.254.169.254":
            raise UrlBlocked(f"IP {ip} is cloud metadata endpoint and blocked")
    elif isinstance(ip, ipaddress.IPv6Address):
        # IPv6 metadata is ::ffff:169.254.169.254 (IPv4-mapped form of 169.254.169.254)
        if str(ip) == "::ffff:169.254.169.254":
            raise UrlBlocked(f"IP {ip} is cloud metadata endpoint and blocked")

    # Check for loopback
    if ip.is_loopback:
        raise UrlBlocked(f"IP {ip} is loopback and blocked")

    # Check for private
    if ip.is_private:
        raise UrlBlocked(f"IP {ip} is in private range and blocked")

    # Check for link-local
    if ip.is_link_local:
        raise UrlBlocked(f"IP {ip} is link-local and blocked")

    # Check for multicast
    if ip.is_multicast:
        raise UrlBlocked(f"IP {ip} is multicast and blocked")

    # Check for reserved
    if ip.is_reserved:
        raise UrlBlocked(f"IP {ip} is reserved and blocked")

    # Check for unspecified
    if ip.is_unspecified:
        raise UrlBlocked(f"IP {ip} is unspecified and blocked")


def check_redirect_chain(urls, resolver=socket.getaddrinfo):
    """
    Check a chain of redirect URLs.

    Raises UrlBlocked if:
    - any URL in the chain violates SSRF policy
    - chain has more than 5 hops

    Args:
        urls: list of URL strings
        resolver: function for DNS resolution (default: socket.getaddrinfo)

    Raises:
        UrlBlocked: if any URL violates policy or chain exceeds 5 hops
    """
    if len(urls) > 5:
        raise UrlBlocked(f"Redirect chain has {len(urls)} hops, maximum 5 allowed")

    for url in urls:
        check_url(url, resolver=resolver)
