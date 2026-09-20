"""Bounded public HTTP fetches for radar evidence connectors."""

from dataclasses import dataclass
from typing import Callable, Optional
import socket
from urllib.parse import urljoin, urlsplit

import urllib3

from academic_radar.security.urlpolicy import check_url, UrlBlocked


@dataclass
class FetchResult:
    url: str
    status: Optional[int]
    content_type: Optional[str]
    body_bytes: Optional[bytes]
    error: Optional[str]


def _pinned_get(url: str, *, resolved_ip: str, timeout: int, **_kwargs):
    """Connect to the validated address while retaining the hostname for TLS/SNI."""
    parsed = urlsplit(url)
    hostname = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    headers = {'Host': hostname if parsed.port is None else f'{hostname}:{port}'}
    pool_type = urllib3.HTTPSConnectionPool if parsed.scheme == 'https' else urllib3.HTTPConnectionPool
    options = {'server_hostname': hostname, 'assert_hostname': hostname} if parsed.scheme == 'https' else {}
    pool = pool_type(resolved_ip, port=port, maxsize=1, block=True, **options)
    path = parsed.path or '/'
    if parsed.query:
        path += '?' + parsed.query
    try:
        response = pool.request('GET', path, headers=headers, timeout=urllib3.Timeout(total=timeout),
                                preload_content=False, redirect=False, retries=False)
    except Exception:
        pool.close()
        raise
    response._radar_pool = pool
    return response


def _close_response(response):
    try:
        response.close()
    finally:
        pool = getattr(response, '_radar_pool', None)
        if pool is not None:
            pool.close()


def _chunks(response, max_bytes):
    if callable(getattr(type(response), 'stream', None)):
        yield from response.stream(amt=min(65536, max_bytes + 1), decode_content=False)
    elif callable(getattr(type(response), 'iter_content', None)):
        yield from response.iter_content(chunk_size=min(65536, max_bytes + 1))
    else:
        # Legacy test doubles have only content. Real transports must stream.
        yield response.content if hasattr(response, 'content') else response.text.encode('utf-8')


def safe_fetch(
    url: str,
    *,
    http_get: Optional[Callable] = None,
    max_bytes: int = 2_000_000,
    timeout_s: int = 20,
    allowed_types: tuple = ('text/html', 'application/pdf', 'application/json', 'text/plain'),
    resolver: Callable = socket.getaddrinfo,
) -> FetchResult:
    """Fetch at most five checked redirects, pinning each DNS result.

    An injected http_get is a trusted transport adapter. It must honor
    resolved_ip, allow_redirects=False and stream=True. The default
    transport enforces these properties itself.
    """
    if max_bytes < 0:
        raise ValueError('max_bytes must be nonnegative')
    requested_url = url
    get = http_get or _pinned_get
    for hop in range(6):
        try:
            addresses = check_url(url, resolver=resolver)
        except UrlBlocked as exc:
            return FetchResult(requested_url, None, None, None, f'URL blocked by policy: {exc.reason}')

        try:
            response = get(url, timeout=timeout_s, allow_redirects=False, stream=True,
                           resolved_ip=addresses[0])
        except Exception as exc:
            return FetchResult(requested_url, None, None, None, f'HTTP request failed: {exc}')
        if response is None:
            return FetchResult(requested_url, None, None, None, 'HTTP request returned None')

        try:
            actual_url = getattr(response, 'url', None)
            if isinstance(actual_url, str) and actual_url.startswith(('http://', 'https://')) and actual_url != url:
                return FetchResult(requested_url, None, None, None, 'HTTP transport followed an unchecked redirect')
            history = getattr(response, 'history', None)
            if isinstance(history, (list, tuple)) and history:
                return FetchResult(requested_url, None, None, None, 'HTTP transport followed an unchecked redirect')

            status = getattr(response, 'status_code', getattr(response, 'status', None))
            headers = getattr(response, 'headers', {}) or {}
            if status in (301, 302, 303, 307, 308):
                location = headers.get('location')
                if not location:
                    return FetchResult(requested_url, status, None, None, 'Redirect missing Location')
                if hop == 5:
                    return FetchResult(requested_url, status, None, None, 'Redirect chain exceeds five hops')
                url = urljoin(url, location)
                continue
            if status is None or status >= 400:
                message = f'HTTP error: {status}' if status else 'No status code'
                return FetchResult(requested_url, status, None, None, message)

            content_type = headers.get('content-type', '').split(';')[0].strip().lower()
            if content_type and content_type not in allowed_types:
                return FetchResult(requested_url, status, content_type, None,
                                   f'Content-Type not allowed: {content_type}')
            content_length = headers.get('content-length')
            if content_length is not None:
                try:
                    if int(content_length) > max_bytes:
                        return FetchResult(requested_url, status, content_type, None,
                                           f'Response body too large: {content_length} > {max_bytes}')
                except ValueError:
                    pass

            body = bytearray()
            try:
                for chunk in _chunks(response, max_bytes):
                    body.extend(chunk)
                    if len(body) > max_bytes:
                        return FetchResult(requested_url, status, content_type, None,
                                           f'Response body too large: {len(body)} > {max_bytes}')
            except Exception as exc:
                return FetchResult(requested_url, status, content_type, None,
                                   f'Failed to read response body: {exc}')
            return FetchResult(requested_url, status, content_type or None, bytes(body), None)
        finally:
            _close_response(response)

    raise AssertionError('unreachable')
