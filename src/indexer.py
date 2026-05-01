"""
indexer.py
----------
Builds an inverted index from crawled page data and handles
saving/loading the index to/from disk as JSON.

Index structure:
    {
        "word": {
            "https://example.com/page/": {
                "frequency": 3,
                "positions": [4, 17, 102]
            }
        }
    }

- Keys are lowercase words (case-insensitive search).
- frequency: how many times the word appears on that page.
- positions: word offsets (0-indexed) within the page's token list.
"""

import json
import os
import re
import string


INDEX_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "index.json"
)


def tokenise(text: str) -> list[str]:
    """
    Convert raw page text into a list of lowercase tokens.
    Strips punctuation and whitespace, removes empty tokens.
    """
    # Replace hyphens/apostrophes with space so "don't" → "don t"
    text = text.lower()
    text = re.sub(r"['''\-]", " ", text)
    # Remove all remaining punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    tokens = text.split()
    # Filter out purely numeric tokens and empty strings
    return [t for t in tokens if t and not t.isdigit()]


def build_index(pages: list[tuple[str, str]]) -> dict:
    """
    Build an inverted index from a list of (url, page_text) tuples.

    Args:
        pages: Output from crawler.crawl() — [(url, text), ...]

    Returns:
        Inverted index dict mapping word → {url → {frequency, positions}}.
    """
    index: dict = {}

    for url, text in pages:
        tokens = tokenise(text)

        for position, word in enumerate(tokens):
            if word not in index:
                index[word] = {}

            if url not in index[word]:
                index[word][url] = {"frequency": 0, "positions": []}

            index[word][url]["frequency"] += 1
            index[word][url]["positions"].append(position)

    return index


def save_index(index: dict, path: str = INDEX_PATH) -> None:
    """
    Serialise the inverted index to a JSON file.

    Args:
        index: The inverted index dict.
        path:  File path to save to (default: data/index.json).
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    print(f"Index saved to {path} ({len(index)} unique words).")


def load_index(path: str = INDEX_PATH) -> dict:
    """
    Load the inverted index from a JSON file.

    Args:
        path: File path to load from.

    Returns:
        The inverted index dict.

    Raises:
        FileNotFoundError: If no index file exists at the given path.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No index found at '{path}'. Run 'build' first."
        )
    with open(path, "r", encoding="utf-8") as f:
        index = json.load(f)
    print(f"Index loaded from {path} ({len(index)} unique words).")
    return index
