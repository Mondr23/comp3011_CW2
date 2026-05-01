"""
search.py
---------
Implements the 'print' and 'find' commands for the search engine.

- print <word>         : Show all pages containing that word + stats.
- find <word> [words…] : Return pages containing ALL the given words
                         (AND logic for multi-word queries).
"""

from indexer import tokenise


def print_word(index: dict, word: str) -> None:
    """
    Print the inverted index entry for a single word.

    Args:
        index: The loaded inverted index.
        word:  The word to look up (case-insensitive).
    """
    normalised = tokenise(word)

    if not normalised:
        print("Invalid word.")
        return

    key = normalised[0]  # use the first token after normalisation

    if key not in index:
        print(f"Word '{key}' not found in index.")
        return

    entries = index[key]
    print(f"\nWord: '{key}'  ({len(entries)} page(s))\n")
    for url, stats in entries.items():
        freq = stats["frequency"]
        positions = stats["positions"]
        print(f"  URL      : {url}")
        print(f"  Frequency: {freq}")
        print(f"  Positions: {positions}")
        print()


def find_pages(index: dict, query: str) -> list[str]:
    """
    Find all pages that contain ALL words in the query (AND logic).

    Args:
        index: The loaded inverted index.
        query: One or more words to search for (space-separated).

    Returns:
        Sorted list of matching URLs. Empty list if no matches or
        the query is empty/invalid.
    """
    words = tokenise(query)

    if not words:
        return []

    # Start with the set of pages for the first word
    first_word = words[0]
    if first_word not in index:
        return []

    # Set intersection across all query words
    matching_pages = set(index[first_word].keys())

    for word in words[1:]:
        if word not in index:
            return []  # AND logic: any missing word → no results
        matching_pages &= set(index[word].keys())

    return sorted(matching_pages)


def cmd_find(index: dict, query: str) -> None:
    """
    CLI wrapper for find_pages — prints results in a human-friendly way.
    """
    words = tokenise(query)

    if not words:
        print("Please provide at least one search term.")
        return

    print(f"\nSearching for: {words}")
    results = find_pages(index, query)

    if not results:
        print("No pages found.")
    else:
        print(f"\n{len(results)} page(s) found:\n")
        for url in results:
            print(f"  {url}")
    print()
