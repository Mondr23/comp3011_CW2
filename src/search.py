from indexer import tokenise
import math
import difflib

def suggest_similar(word: str, index: dict, max_suggestions: int = 3) -> list[str]:
    """
    Suggest similar words when a search word is not found.

    It checks the words in the index and returns the closest matches.

    Example:
        "mondr" might suggest "modern"

    Args:
        word: The word to find suggestions for.
        index: The inverted index.
        max_suggestions: How many suggestions to return.

    Returns:
        A list of suggested words, or an empty list if none are found.
    """
    all_words = list(index.keys())
 
    suggestions = difflib.get_close_matches(
        word,
        all_words,
        n=max_suggestions,
        cutoff=0.6,   # similarity threshold — 0.6 means 60% similar
    )
 
    return suggestions

def tf_idf(index: math.dist, word: str,url: str, total_pages: int) -> float:
    """
        Calculate how important a word is on a page.

        TF-IDF gives a higher score when:
        - the word appears often on this page
        - the word does not appear on many other pages

        Args:
            index: The inverted index.
            word: The word to score.
            url: The page URL.
            total_pages: Total number of pages.

        Returns:
            The TF-IDF score. Returns 0.0 if the word or URL is not found.
    """
    if word not in  index or url not in index[word]:
        return 0.0
    
    frequency = index[word][url]["frequency"]
    positions = index[word][url]["positions"]
 
    # Approximate total words on page using the highest word position
    total_words_on_page = max(positions) + 1
 
    tf = frequency / total_words_on_page
 
    # How many pages contain this word
    pages_with_word = len(index[word])
 
    if pages_with_word == 0:
        return 0.0
 
    idf = math.log(total_pages / pages_with_word)
 
    return tf * idf

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

    # Total pages in index 
    total_pages = max(len(urls) for urls in index.values())
 
    # Score each matching page
    scored = []
    for url in matching_pages:
        score = sum(
            tf_idf(index, word, url, total_pages)
            for word in words
        )
        scored.append((score, url))
 
    # Sort highest score first
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored

    return sorted(matching_pages)

def is_phrase_query(query: str) -> bool:
    """
    Check if the user is searching for an exact phrase

    A phrase search starts and ends with quote marks
    """
    query = query.strip()
    return (
        len(query) >= 2
        and query[0] in ('"', "'")
        and query[-1] in ('"', "'")
    )
 
def phrase_search(index: dict, phrase: str, pagerank: dict = None) -> list:
    """
    Find pages that contain the exact phrase.

    The words must appear next to each other and in the same order.

    Args:
        index: The inverted index.
        phrase: The phrase to search for.
        pagerank: Optional PageRank scores used to rank results.

    Returns:
        A list of matching pages with their scores, sorted from best to worst.
        Returns an empty list if no matches are found.
    """
    words = tokenise(phrase)
 
    if not words:
        return []
 
    # Single word phrase
    if len(words) == 1:
        return find_pages(index, words[0], pagerank)
 
    # Step 1: find pages containing ALL words (AND logic)
    if words[0] not in index:
        return []
 
    candidate_pages = set(index[words[0]].keys())
    for word in words[1:]:
        if word not in index:
            return []
        candidate_pages &= set(index[word].keys())
 
    if not candidate_pages:
        return []
 
    # Step 2: for each candidate page, check consecutive positions
    matching_pages = []
    total_pages = max(len(urls) for urls in index.values())
 
    for url in candidate_pages:
 
        # Get positions of the first word on this page
        first_word_positions = index[words[0]][url]["positions"]
 
        # Try each starting position of the first word
        phrase_found = False
        for start_pos in first_word_positions:
 
            # Check every subsequent word appears at start_pos + offset
            consecutive = True
            for offset, word in enumerate(words[1:], start=1):
                expected_pos = start_pos + offset
                actual_positions = index[word][url]["positions"]
 
                if expected_pos not in actual_positions:
                    consecutive = False
                    break   # this starting position doesn't work
 
            if consecutive:
                phrase_found = True
                break       # found at least one match 
 
        if phrase_found:
            # Score using TF-IDF + PageRank same as regular search
            score = sum(
                tf_idf(index, word, url, total_pages)
                for word in words
            )
            matching_pages.append((score, url))
 
    # Sort highest score first
    matching_pages.sort(key=lambda x: x[0], reverse=True)
    return matching_pages
 
def cmd_find(index: dict, query: str) -> None:
    """
    CLI wrapper for find_pages 
    """
        # ── Phrase search ──────────────────────────────────────────────────────
    if is_phrase_query(query):
        phrase = query.strip()[1:-1].strip()
        if not phrase:
            print("Please provide a phrase inside the quotes.\n")
            return
        print(f'\nPhrase search: "{phrase}"')
        results = phrase_search(index, phrase)
        if not results:
            print(f'  No pages found containing the exact phrase "{phrase}".')
        else:
            print(f"\n{len(results)} page(s) contain the exact phrase:\n")
            for rank, (score, url) in enumerate(results, start=1):
                print(f"  {rank}. {url}")
                print(f"     Score: {score:.4f}")
        print()
        return
    
    # Normal search
    words = tokenise(query)

    if not words:
        print("Please provide at least one search term.")
        return

    print(f"\nSearching for: {words}")

        # Check  alternatives for unknown words
    for word in words:
        if word not in index:
            suggestions = suggest_similar(word, index)
            if suggestions:
                print(f"\n  Word '{word}' not found in index.")
                print(f"  Did you mean: {', '.join(suggestions)} ?")
            else:
                print(f"\n  Word '{word}' not found in index. No similar words found.")
            print()
            return

    results = find_pages(index, query)

    if not results:
        print("No pages found.")
    else:
        print(f"\n{len(results)} page(s) found (ranked by relevance):\n")
        for rank, (score, url) in enumerate(results, start=1): 
            print(f"  {rank}. {url}")                           
            print(f"     Relevance score: {score:.4f}")         
    print()
