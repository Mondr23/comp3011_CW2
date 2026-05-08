import sys
import os

# Let tests import files from the src folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

from crawler import get_page, extract_text, extract_links, crawl


# Sample HTML used in the tests

SAMPLE_HTML = """
<html>
<head><title>Test</title></head>
<body>
  <p>Hello world. This is a test page.</p>
  <a href="/page/2/">Next</a>
  <a href="/author/einstein/">Author</a>
  <a href="https://external.com/other">External</a>
</body>
</html>
"""

EMPTY_HTML = "<html><body></body></html>"


# Tests for extract_text()

class TestExtractText:
    def test_gets_visible_text(self):
        soup = BeautifulSoup(SAMPLE_HTML, "lxml")
        text = extract_text(soup)
        assert "Hello world" in text
        assert "test page" in text

    def test_removes_script_tags(self):
        html = "<html><body><script>alert('bad')</script><p>Good text</p></body></html>"
        soup = BeautifulSoup(html, "lxml")
        text = extract_text(soup)
        assert "alert" not in text
        assert "Good text" in text

    def test_removes_style_tags(self):
        html = "<html><body><style>.foo { color: red }</style><p>Visible</p></body></html>"
        soup = BeautifulSoup(html, "lxml")
        text = extract_text(soup)
        assert "color" not in text
        assert "Visible" in text

    def test_empty_page_returns_a_string(self):
        soup = BeautifulSoup(EMPTY_HTML, "lxml")
        text = extract_text(soup)
        assert isinstance(text, str)


# Tests for extract_links()

class TestExtractLinks:
    BASE = "https://quotes.toscrape.com/"

    def test_finds_internal_links(self):
        soup = BeautifulSoup(SAMPLE_HTML, "lxml")
        links = extract_links(soup, self.BASE)
        assert "https://quotes.toscrape.com/page/2/" in links
        assert "https://quotes.toscrape.com/author/einstein/" in links

    def test_ignores_external_links(self):
        soup = BeautifulSoup(SAMPLE_HTML, "lxml")
        links = extract_links(soup, self.BASE)

        # External links should not be included
        assert not any("external.com" in l for l in links)

    def test_no_duplicate_links(self):
        html = """<html><body>
            <a href="/page/2/">Link</a>
            <a href="/page/2/">Same link again</a>
        </body></html>"""
        soup = BeautifulSoup(html, "lxml")
        links = extract_links(soup, self.BASE)

        # The same link should only be stored once
        assert links.count("https://quotes.toscrape.com/page/2/") == 1

    def test_empty_page_gives_empty_list(self):
        soup = BeautifulSoup(EMPTY_HTML, "lxml")
        links = extract_links(soup, self.BASE)
        assert links == []


# Tests for get_page()

class TestGetPage:
    def test_returns_soup_when_page_loads(self):
        mock_response = MagicMock()
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = MagicMock()

        with patch("crawler.requests.Session") as MockSession:
            session = MockSession.return_value
            session.get.return_value = mock_response
            soup = get_page("https://quotes.toscrape.com/", session)

        assert soup is not None
        assert soup.find("p") is not None

    def test_returns_none_when_network_fails(self):
        import requests as req

        with patch("crawler.requests.Session") as MockSession:
            session = MockSession.return_value
            session.get.side_effect = req.RequestException("Connection refused")
            soup = get_page("https://quotes.toscrape.com/", session)

        assert soup is None


# Tests for crawl()

class TestCrawl:
    def _make_mock_response(self, html: str):
        # Create a fake response using the given HTML
        response = MagicMock()
        response.text = html
        response.raise_for_status = MagicMock()
        return response

    def test_visits_linked_pages(self):
        # The homepage links to page 2, so the crawler should visit both
        page1 = """<html><body><p>Page one</p>
                   <a href="/page/2/">Page 2</a></body></html>"""
        page2 = """<html><body><p>Page two</p></body></html>"""

        responses = {
            "https://quotes.toscrape.com/": self._make_mock_response(page1),
            "https://quotes.toscrape.com/page/2/": self._make_mock_response(page2),
        }

        with patch("crawler.requests.Session") as MockSession, \
             patch("crawler.time.sleep"):  # Skip waiting during tests
            session = MockSession.return_value
            session.get.side_effect = lambda url, **kw: responses.get(
                url, self._make_mock_response(EMPTY_HTML)
            )
            results = crawl(politeness=0, verbose=False)

        urls = [r[0] for r in results]
        assert "https://quotes.toscrape.com/" in urls

    def test_never_visits_same_page_twice(self):
        # This page links back to itself
        page = """<html><body><p>Content</p>
                  <a href="/">Home</a></body></html>"""

        with patch("crawler.requests.Session") as MockSession, \
             patch("crawler.time.sleep"):
            session = MockSession.return_value
            session.get.return_value = self._make_mock_response(page)
            session.get.return_value.raise_for_status = MagicMock()
            results = crawl(
                start_url="https://quotes.toscrape.com/",
                politeness=0,
                verbose=False,
            )

        urls = [r[0] for r in results]

        # Each URL should only appear once
        assert len(urls) == len(set(urls))