"""
crawler.py
----------
Crawls all pages of https://quotes.toscrape.com/ with a configurable
politeness window (default: 6 seconds) between requests.

Returns a list of (url, page_text) tuples for the indexer to process.
"""

import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


BASE_URL = "https://quotes.toscrape.com/"
POLITENESS_WINDOW = 6  # seconds between requests


def get_page(url: str, session: requests.Session) -> BeautifulSoup | None:
    """
    Fetch a single page and return a BeautifulSoup object.
    Returns None if the request fails.
    """
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")
    except requests.RequestException as e:
        print(f"  [WARNING] Failed to fetch {url}: {e}")
        return None


def extract_text(soup: BeautifulSoup) -> str:
    """
    Extract visible text content from a parsed page.
    Focuses on the main content area (quotes, authors, tags).
    """
    # Remove script and style elements
    for tag in soup(["script", "style", "head"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def extract_links(soup: BeautifulSoup, current_url: str) -> list[str]:
    """
    Extract all internal links from a page, resolved to absolute URLs.
    Only follows links within the same domain.
    """
    links = []
    base_domain = urlparse(BASE_URL).netloc

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        absolute = urljoin(current_url, href)

        # Only keep links within the same domain
        if urlparse(absolute).netloc == base_domain:
            # Strip fragments and query strings for deduplication
            clean = absolute.split("#")[0].split("?")[0]
            if clean not in links:
                links.append(clean)

    return links


def crawl(
    start_url: str = BASE_URL,
    politeness: float = POLITENESS_WINDOW,
    verbose: bool = True,
) -> list[tuple[str, str]]:
    """
    Crawl all reachable pages from start_url.

    Args:
        start_url:   The URL to begin crawling from.
        politeness:  Seconds to wait between requests.
        verbose:     Print progress to stdout if True.

    Returns:
        A list of (url, page_text) tuples, one per page crawled.
    """
    session = requests.Session()
    session.headers.update({"User-Agent": "COMP3011-SearchBot/1.0"})

    visited: set[str] = set()
    queue: list[str] = [start_url]
    results: list[tuple[str, str]] = []

    page_count = 0

    while queue:
        url = queue.pop(0)

        if url in visited:
            continue
        visited.add(url)

        page_count += 1
        if verbose:
            print(f"  [Page {page_count}] Crawling: {url}")

        soup = get_page(url, session)
        if soup is None:
            continue

        # Extract and store page text
        text = extract_text(soup)
        results.append((url, text))

        # Discover new links
        new_links = extract_links(soup, url)
        for link in new_links:
            if link not in visited and link not in queue:
                queue.append(link)

        # Politeness window — always wait between requests
        if queue:
            if verbose:
                print(f"  [Waiting {politeness}s before next request...]")
            time.sleep(politeness)

    if verbose:
        print(f"\nCrawl complete. {len(results)} pages indexed.")

    return results
