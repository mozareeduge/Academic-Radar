"""Adversarial tests of the actual safe_fetch boundary."""

import socket

import urllib3

from academic_radar.security.fetch import safe_fetch


PUBLIC = "93.184.216.34"


def public_resolver(host, _family):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (PUBLIC, 80))]


class Response:
    def __init__(self, status, headers=None, chunks=()):
        self.status_code = status
        self.headers = headers or {}
        self.chunks = chunks
        self.closed = False

    def iter_content(self, chunk_size):
        for chunk in self.chunks:
            yield chunk

    def close(self):
        self.closed = True


def test_redirect_to_private_is_rejected_before_second_request():
    calls = []
    first = Response(302, {"location": "http://127.0.0.1/admin"})

    def get(url, **kwargs):
        calls.append((url, kwargs))
        return first

    result = safe_fetch("https://example.org/start", http_get=get, resolver=public_resolver)
    assert "blocked by policy" in result.error
    assert len(calls) == 1
    assert calls[0][1]["allow_redirects"] is False
    assert first.closed


def test_redirect_chain_checks_dns_of_each_hop():
    calls = []

    def resolver(host, _family):
        address = PUBLIC if host == "example.org" else "10.0.0.2"
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 80))]

    def get(url, **kwargs):
        calls.append(url)
        return Response(302, {"location": "https://internal.example/secret"})

    result = safe_fetch("https://example.org/start", http_get=get, resolver=resolver)
    assert "blocked by policy" in result.error
    assert calls == ["https://example.org/start"]


def test_valid_public_redirect_and_dns_pin_are_used():
    calls = []
    responses = [Response(302, {"location": "/next"}), Response(200, {"content-type": "text/plain"}, [b"safe"])]

    def get(url, **kwargs):
        calls.append((url, kwargs))
        return responses.pop(0)

    result = safe_fetch("https://example.org/start", http_get=get, resolver=public_resolver)
    assert result.error is None and result.body_bytes == b"safe"
    assert [url for url, _ in calls] == ["https://example.org/start", "https://example.org/next"]
    assert all(kwargs["resolved_ip"] == PUBLIC for _, kwargs in calls)
    assert all(kwargs["stream"] and kwargs["allow_redirects"] is False for _, kwargs in calls)


def test_transport_that_auto_follows_redirect_fails_closed():
    response = Response(200, {"content-type": "text/plain"}, [b"private data"])
    response.url = "http://127.0.0.1/admin"
    result = safe_fetch("https://example.org/start", http_get=lambda *_args, **_kwargs: response,
                        resolver=public_resolver)
    assert "unchecked redirect" in result.error
    assert result.body_bytes is None
    assert response.closed


def test_stream_stops_after_limit_without_consuming_rest():
    seen = []

    def chunks():
        for piece in (b"aa", b"bb", b"cc", b"never"):
            seen.append(piece)
            yield piece

    response = Response(200, {"content-type": "text/plain"}, chunks())
    result = safe_fetch("https://example.org/file", http_get=lambda *_args, **_kwargs: response,
                        max_bytes=5, resolver=public_resolver)
    assert "too large" in result.error
    assert seen == [b"aa", b"bb", b"cc"]
    assert response.closed


def test_oversized_content_length_prevents_body_read():
    response = Response(200, {"content-type": "text/plain", "content-length": "100"}, [b"secret"])
    result = safe_fetch("https://example.org/file", http_get=lambda *_args, **_kwargs: response,
                        max_bytes=5, resolver=public_resolver)
    assert "too large" in result.error
    assert response.closed


def test_mixed_public_private_dns_answers_fail_before_request():
    def resolver(_host, _family):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", (PUBLIC, 80)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80)),
        ]

    calls = []
    result = safe_fetch("https://example.org/file", http_get=lambda *_args, **_kwargs: calls.append(1),
                        resolver=resolver)
    assert "blocked by policy" in result.error
    assert calls == []


def test_default_https_transport_connects_to_validated_ip_with_original_tls_name(monkeypatch):
    pools = []
    response = Response(200, {"content-type": "text/plain"}, [b"ok"])

    class Pool:
        def __init__(self, host, **kwargs):
            pools.append((host, kwargs, self))

        def request(self, method, path, **kwargs):
            assert method == "GET"
            assert path == "/paper?q=1"
            assert kwargs["headers"]["Host"] == "example.org"
            assert kwargs["redirect"] is False
            assert kwargs["preload_content"] is False
            return response

        def close(self):
            self.closed = True

    monkeypatch.setattr(urllib3, "HTTPSConnectionPool", Pool)
    result = safe_fetch("https://example.org/paper?q=1", resolver=public_resolver)
    assert result.body_bytes == b"ok"
    assert pools[0][0] == PUBLIC
    assert pools[0][1]["server_hostname"] == "example.org"
    assert pools[0][1]["assert_hostname"] == "example.org"
    assert pools[0][2].closed


def test_malformed_port_is_rejected_before_request():
    calls = []
    result = safe_fetch("https://example.org:bad/", http_get=lambda *_args, **_kwargs: calls.append(1),
                        resolver=public_resolver)
    assert "blocked by policy" in result.error
    assert calls == []
