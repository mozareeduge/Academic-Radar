from dataclasses import dataclass
from typing import Callable, Optional
import socket

from academic_radar.security.urlpolicy import check_url, UrlBlocked


@dataclass
class FetchResult:
    url: str
    status: Optional[int]
    content_type: Optional[str]
    body_bytes: Optional[bytes]
    error: Optional[str]


def safe_fetch(
    url: str,
    *,
    http_get: Callable,
    max_bytes: int = 2_000_000,
    timeout_s: int = 20,
    allowed_types: tuple = ('text/html', 'application/pdf', 'application/json', 'text/plain'),
    resolver: Callable = socket.getaddrinfo,
) -> FetchResult:
    try:
        check_url(url, resolver=resolver)
    except UrlBlocked as e:
        return FetchResult(url=url, status=None, content_type=None, body_bytes=None, error=f"URL blocked by policy: {e.reason}")

    try:
        resp = http_get(url, timeout=timeout_s)
    except Exception as e:
        return FetchResult(url=url, status=None, content_type=None, body_bytes=None, error=f"HTTP request failed: {str(e)}")

    if resp is None:
        return FetchResult(url=url, status=None, content_type=None, body_bytes=None, error="HTTP request returned None")

    status = getattr(resp, 'status_code', None)
    if status is None or status >= 400:
        error_msg = f"HTTP error: {status}" if status else "No status code"
        return FetchResult(url=url, status=status, content_type=None, body_bytes=None, error=error_msg)

    content_type = resp.headers.get('content-type', '').split(';')[0].strip() if hasattr(resp, 'headers') else None

    if content_type and content_type not in allowed_types:
        return FetchResult(url=url, status=status, content_type=content_type, body_bytes=None, error=f"Content-Type not allowed: {content_type}")

    try:
        body_bytes = resp.content if hasattr(resp, 'content') else resp.text.encode('utf-8')
    except Exception as e:
        return FetchResult(url=url, status=status, content_type=content_type, body_bytes=None, error=f"Failed to read response body: {str(e)}")

    if len(body_bytes) > max_bytes:
        return FetchResult(url=url, status=status, content_type=content_type, body_bytes=None, error=f"Response body too large: {len(body_bytes)} > {max_bytes}")

    return FetchResult(url=url, status=status, content_type=content_type, body_bytes=body_bytes, error=None)
