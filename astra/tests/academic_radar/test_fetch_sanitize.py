import pytest
from unittest.mock import Mock, MagicMock
import socket

from academic_radar.security.fetch import safe_fetch, FetchResult
from academic_radar.security.sanitize import html_to_safe_text


def mock_resolver_public(hostname, family):
    """Mock resolver for public addresses."""
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))]


class TestSafeFetch:

    def test_private_url_blocked_and_http_get_not_called(self):
        mock_http_get = Mock()

        result = safe_fetch(
            "http://127.0.0.1:8000/private",
            http_get=mock_http_get,
        )

        assert result.error is not None
        assert "blocked by policy" in result.error.lower()
        mock_http_get.assert_not_called()

    def test_loopback_url_blocked_and_http_get_not_called(self):
        mock_http_get = Mock()

        def mock_resolver(hostname, family):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))]

        result = safe_fetch(
            "http://localhost/admin",
            http_get=mock_http_get,
            resolver=mock_resolver,
        )

        assert result.error is not None
        mock_http_get.assert_not_called()

    def test_metadata_endpoint_blocked(self):
        mock_http_get = Mock()

        result = safe_fetch(
            "http://169.254.169.254/latest/meta-data/",
            http_get=mock_http_get,
        )

        assert result.error is not None
        assert "blocked" in result.error.lower()
        mock_http_get.assert_not_called()

    def test_oversize_body_rejected(self):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'text/html'}
        mock_resp.content = b'x' * 3_000_000

        mock_http_get = Mock(return_value=mock_resp)

        result = safe_fetch(
            "http://example.com/large",
            http_get=mock_http_get,
            max_bytes=2_000_000,
            resolver=mock_resolver_public,
        )

        assert result.error is not None
        assert "too large" in result.error.lower()
        assert result.body_bytes is None

    def test_disallowed_content_type_rejected(self):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/exe'}
        mock_resp.content = b'MZ\x90\x00'

        mock_http_get = Mock(return_value=mock_resp)

        result = safe_fetch(
            "http://example.com/binary",
            http_get=mock_http_get,
            allowed_types=('text/html', 'application/pdf', 'application/json', 'text/plain'),
            resolver=mock_resolver_public,
        )

        assert result.error is not None
        assert "not allowed" in result.error.lower()
        assert result.body_bytes is None

    def test_allowed_content_types_accepted(self):
        for ct in ('text/html', 'application/pdf', 'application/json', 'text/plain'):
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.headers = {'content-type': ct}
            mock_resp.content = b'valid content'

            mock_http_get = Mock(return_value=mock_resp)

            result = safe_fetch(
                "http://example.com/test",
                http_get=mock_http_get,
                allowed_types=('text/html', 'application/pdf', 'application/json', 'text/plain'),
                resolver=mock_resolver_public,
            )

            assert result.error is None
            assert result.body_bytes == b'valid content'
            assert result.status == 200

    def test_content_type_with_charset_accepted(self):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'text/html; charset=utf-8'}
        mock_resp.content = b'<html>test</html>'

        mock_http_get = Mock(return_value=mock_resp)

        result = safe_fetch(
            "http://example.com/page",
            http_get=mock_http_get,
            resolver=mock_resolver_public,
        )

        assert result.error is None
        assert result.body_bytes == b'<html>test</html>'

    def test_http_error_status_returned(self):
        mock_resp = Mock()
        mock_resp.status_code = 404

        mock_http_get = Mock(return_value=mock_resp)

        result = safe_fetch(
            "http://example.com/notfound",
            http_get=mock_http_get,
            resolver=mock_resolver_public,
        )

        assert result.error is not None
        assert "404" in result.error
        assert result.body_bytes is None

    def test_http_request_exception_caught(self):
        mock_http_get = Mock(side_effect=Exception("Connection timeout"))

        result = safe_fetch(
            "http://example.com/timeout",
            http_get=mock_http_get,
            resolver=mock_resolver_public,
        )

        assert result.error is not None
        assert "Connection timeout" in result.error

    def test_public_url_allowed(self):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'text/html'}
        mock_resp.content = b'<html>content</html>'

        mock_http_get = Mock(return_value=mock_resp)

        result = safe_fetch(
            "http://example.com/public",
            http_get=mock_http_get,
            resolver=mock_resolver_public,
        )

        assert result.error is None
        assert result.status == 200
        assert result.body_bytes == b'<html>content</html>'


class TestHtmlToSafeText:

    def test_removes_script_tags(self):
        html = '<html><body><p>Hello</p><script>alert(1)</script></body></html>'

        text = html_to_safe_text(html)

        assert 'alert' not in text
        assert 'Hello' in text

    def test_removes_style_tags(self):
        html = '<html><head><style>body { color: red; }</style></head><body>Text</body></html>'

        text = html_to_safe_text(html)

        assert 'color' not in text
        assert 'red' not in text
        assert 'Text' in text

    def test_removes_iframe_tags(self):
        html = '<html><body><p>Safe</p><iframe src="evil.com"></iframe></body></html>'

        text = html_to_safe_text(html)

        assert 'evil.com' not in text
        assert 'Safe' in text

    def test_removes_object_and_embed_tags(self):
        html = '<html><body><p>Text</p><object data="malware.swf"></object><embed src="evil.swf"/></body></html>'

        text = html_to_safe_text(html)

        assert 'malware' not in text
        assert 'evil' not in text
        assert 'Text' in text

    def test_removes_onclick_handlers(self):
        html = '<html><body><p onclick="doEvil()">Click me</p></body></html>'

        text = html_to_safe_text(html)

        assert 'doEvil' not in text
        assert 'Click me' in text

    def test_removes_onerror_handlers(self):
        html = '<html><body><img src="x" onerror="alert(1)"/><p>Text</p></body></html>'

        text = html_to_safe_text(html)

        assert 'alert' not in text
        assert 'Text' in text

    def test_removes_javascript_hrefs(self):
        html = '<html><body><a href="javascript:alert(1)">Link</a></body></html>'

        text = html_to_safe_text(html)

        assert 'javascript' not in text
        assert 'alert' not in text
        assert 'Link' in text

    def test_preserves_normal_links(self):
        html = '<html><body><a href="http://example.com">Visit</a></body></html>'

        text = html_to_safe_text(html)

        assert 'Visit' in text

    def test_multiple_event_handlers_removed(self):
        html = '<div onclick="x" onmouseover="y" onload="z">Content</div>'

        text = html_to_safe_text(html)

        assert 'onclick' not in html_to_safe_text(html).lower()
        assert 'onmouseover' not in html_to_safe_text(html).lower()
        assert 'onload' not in html_to_safe_text(html).lower()
        assert 'Content' in text

    def test_preserves_visible_text_only(self):
        html = '<html><body><p>Visible</p><!-- comment --><p>Also visible</p></body></html>'

        text = html_to_safe_text(html)

        assert 'Visible' in text
        assert 'Also visible' in text
        assert 'comment' not in text

    def test_complex_nested_structure(self):
        html = '''
        <html>
            <head><style>* { margin: 0; }</style></head>
            <body>
                <div onclick="evil()">
                    <h1>Title</h1>
                    <p>First paragraph</p>
                    <script>var x = 1;</script>
                    <p>Second paragraph</p>
                    <a href="javascript:void(0)">Evil link</a>
                </div>
            </body>
        </html>
        '''

        text = html_to_safe_text(html)

        assert 'Title' in text
        assert 'First paragraph' in text
        assert 'Second paragraph' in text
        assert 'Evil link' in text
        assert 'evil()' not in text
        assert 'var x = 1' not in text
        assert 'margin' not in text
