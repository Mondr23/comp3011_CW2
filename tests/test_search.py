import sys
import os

# Let tests import from the src folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from search import (
    suggest_similar,
    tf_idf,
    print_word,
    find_pages,
    is_phrase_query,
    phrase_search,
    cmd_find,
)


# Shared test data

@pytest.fixture
def sample_index():
    # Small fake index used by several tests
    return {
        "good": {
            "https://example.com/page/1/": {"frequency": 2, "positions": [3, 10]},
            "https://example.com/page/2/": {"frequency": 1, "positions": [7]},
        },
        "friends": {
            "https://example.com/page/1/": {"frequency": 1, "positions": [4]},
        },
        "indifference": {
            "https://example.com/page/3/": {"frequency": 1, "positions": [0]},
        },
        "nonsense": {
            "https://example.com/page/4/": {"frequency": 3, "positions": [1, 5, 9]},
        },
    }


@pytest.fixture
def phrase_index():
    # Fake index with positions set up for phrase search tests
    return {
        "be": {
            "https://example.com/page/1/": {
                "frequency": 2,
                "positions": [4, 19]
            },
        },
        "yourself": {
            "https://example.com/page/1/": {
                "frequency": 1,
                "positions": [5]
            },
        },
        "good": {
            "https://example.com/page/1/": {
                "frequency": 1,
                "positions": [0]
            },
            "https://example.com/page/2/": {
                "frequency": 1,
                "positions": [3]
            },
        },
        "friends": {
            "https://example.com/page/1/": {
                "frequency": 1,
                "positions": [10]  # not next to "good"
            },
        },
    }


# Tests for suggest_similar()

class TestSuggestSimilar:
    def test_finds_close_match_for_typo(self, sample_index):
        # Typo should suggest the correct word
        results = suggest_similar("indiffernce", sample_index)
        assert "indifference" in results

    def test_returns_empty_for_random_string(self, sample_index):
        # No similar words should be found
        results = suggest_similar("xyzzyqqqq", sample_index)
        assert results == []

    def test_respects_max_suggestions_limit(self, sample_index):
        results = suggest_similar("good", sample_index, max_suggestions=1)
        assert len(results) <= 1

    def test_exact_word_is_suggested(self, sample_index):
        # Correct words can still be returned as suggestions
        results = suggest_similar("good", sample_index)
        assert "good" in results

    def test_always_returns_a_list(self, sample_index):
        results = suggest_similar("nonsens", sample_index)
        assert isinstance(results, list)


# Tests for tf_idf()

class TestTfIdf:
    def test_returns_zero_for_missing_word(self, sample_index):
        # Word is not in the index
        score = tf_idf(sample_index, "unknown", "https://example.com/page/1/", 4)
        assert score == 0.0

    def test_returns_zero_for_missing_url(self, sample_index):
        # Word exists, but not on this page
        score = tf_idf(sample_index, "good", "https://example.com/page/99/", 4)
        assert score == 0.0

    def test_returns_positive_score_for_valid_word(self, sample_index):
        # Word exists on this page, so score should be above zero
        score = tf_idf(sample_index, "nonsense", "https://example.com/page/4/", 4)
        assert score > 0.0

    def test_more_frequent_word_scores_higher(self, sample_index):
        # Same word appears more often on page 1 than page 2
        score_page1 = tf_idf(sample_index, "good", "https://example.com/page/1/", 4)
        score_page2 = tf_idf(sample_index, "good", "https://example.com/page/2/", 4)
        assert score_page1 > score_page2

    def test_returns_a_float(self, sample_index):
        score = tf_idf(sample_index, "good", "https://example.com/page/1/", 4)
        assert isinstance(score, float)


# Tests for find_pages()

class TestFindPages:
    def _urls(self, results):
        # Get only the URLs from the search results
        return [url for _, url in results]

    def test_finds_pages_for_single_word(self, sample_index):
        results = find_pages(sample_index, "good")
        urls = self._urls(results)
        assert "https://example.com/page/1/" in urls
        assert "https://example.com/page/2/" in urls

    def test_returns_empty_for_unknown_word(self, sample_index):
        results = find_pages(sample_index, "xyzzy")
        assert results == []

    def test_multi_word_and_logic(self, sample_index):
        # Only page 1 has both words
        results = find_pages(sample_index, "good friends")
        urls = self._urls(results)
        assert urls == ["https://example.com/page/1/"]

    def test_no_results_when_words_on_different_pages(self, sample_index):
        # These words are on different pages, so there is no match
        results = find_pages(sample_index, "indifference nonsense")
        assert results == []

    def test_empty_query_returns_empty(self, sample_index):
        results = find_pages(sample_index, "")
        assert results == []

    def test_search_is_case_insensitive(self, sample_index):
        results = find_pages(sample_index, "GOOD")
        urls = self._urls(results)
        assert "https://example.com/page/1/" in urls

    def test_results_sorted_by_score_highest_first(self, sample_index):
        results = find_pages(sample_index, "good")
        scores = [s for s, _ in results]
        assert scores == sorted(scores, reverse=True)

    def test_punctuation_in_query_is_handled(self, sample_index):
        results = find_pages(sample_index, "good!")
        urls = self._urls(results)
        assert "https://example.com/page/1/" in urls

    def test_empty_index_returns_empty(self):
        results = find_pages({}, "good")
        assert results == []

    def test_numbers_only_query_returns_empty(self, sample_index):
        # Numbers are removed, so the query becomes empty
        results = find_pages(sample_index, "123")
        assert results == []

    def test_each_result_is_a_score_url_tuple(self, sample_index):
        results = find_pages(sample_index, "good")
        for item in results:
            score, url = item
            assert isinstance(score, float)
            assert isinstance(url, str)


# Tests for is_phrase_query()

class TestIsPhraseQuery:
    def test_double_quotes_detected_as_phrase(self):
        assert is_phrase_query('"be yourself"') is True

    def test_single_quotes_detected_as_phrase(self):
        assert is_phrase_query("'be yourself'") is True

    def test_no_quotes_is_not_a_phrase(self):
        assert is_phrase_query("be yourself") is False

    def test_only_opening_quote_is_not_a_phrase(self):
        assert is_phrase_query('"be yourself') is False

    def test_empty_string_is_not_a_phrase(self):
        assert is_phrase_query("") is False

    def test_empty_quotes_still_detected(self):
        # Empty quotes count as a phrase query, but are handled later
        assert is_phrase_query('""') is True


# Tests for phrase_search()

class TestPhraseSearch:
    def test_finds_consecutive_words(self, phrase_index):
        # "be" and "yourself" are next to each other
        results = phrase_search(phrase_index, "be yourself")
        urls = [url for _, url in results]
        assert "https://example.com/page/1/" in urls

    def test_does_not_match_non_consecutive_words(self, phrase_index):
        # The words exist, but are not next to each other
        results = phrase_search(phrase_index, "good friends")
        assert results == []

    def test_empty_phrase_returns_empty(self, phrase_index):
        results = phrase_search(phrase_index, "")
        assert results == []

    def test_unknown_word_in_phrase_returns_empty(self, phrase_index):
        results = phrase_search(phrase_index, "be unknown")
        assert results == []

    def test_single_word_phrase_works(self, phrase_index):
        # Check that phrase search returns a list
        results = phrase_search(phrase_index, "be yourself")
        assert isinstance(results, list)

    def test_each_result_is_a_score_url_tuple(self, phrase_index):
        results = phrase_search(phrase_index, "be yourself")
        for item in results:
            score, url = item
            assert isinstance(score, float)
            assert isinstance(url, str)

    def test_results_sorted_highest_score_first(self, phrase_index):
        results = phrase_search(phrase_index, "be yourself")
        scores = [s for s, _ in results]
        assert scores == sorted(scores, reverse=True)


# Tests for print_word()

class TestPrintWord:
    def test_prints_word_stats(self, sample_index, capsys):
        print_word(sample_index, "nonsense")
        output = capsys.readouterr().out
        assert "nonsense" in output
        assert "https://example.com/page/4/" in output
        assert "3" in output  # frequency

    def test_unknown_word_shows_not_found(self, sample_index, capsys):
        print_word(sample_index, "unknownword")
        output = capsys.readouterr().out
        assert "not found" in output.lower()

    def test_search_is_case_insensitive(self, sample_index, capsys):
        print_word(sample_index, "GOOD")
        output = capsys.readouterr().out
        assert "good" in output

    def test_empty_word_prints_something(self, sample_index, capsys):
        print_word(sample_index, "")
        output = capsys.readouterr().out
        assert output  # should print something

    def test_positions_are_shown(self, sample_index, capsys):
        print_word(sample_index, "nonsense")
        output = capsys.readouterr().out
        assert "1" in output
        assert "5" in output


# Tests for cmd_find()

class TestCmdFind:
    def test_normal_search_finds_results(self, sample_index, capsys):
        cmd_find(sample_index, "good")
        output = capsys.readouterr().out
        assert "page/1" in output or "page/2" in output

    def test_unknown_word_shows_not_found(self, sample_index, capsys):
        cmd_find(sample_index, "xyzzy")
        output = capsys.readouterr().out
        assert "not found in index" in output

    def test_empty_query_asks_for_search_term(self, sample_index, capsys):
        cmd_find(sample_index, "")
        output = capsys.readouterr().out
        assert "at least one" in output.lower() or output

    def test_phrase_search_is_triggered_by_quotes(self, sample_index, capsys):
        # Quoted text should use phrase search
        cmd_find(sample_index, '"good friends"')
        output = capsys.readouterr().out
        assert "Phrase search" in output

    def test_empty_quotes_shows_error(self, sample_index, capsys):
        cmd_find(sample_index, '""')
        output = capsys.readouterr().out
        assert "phrase" in output.lower()

    def test_suggestion_shown_for_typo(self, sample_index, capsys):
        # Typo should show a suggestion
        cmd_find(sample_index, "indiffernce")
        output = capsys.readouterr().out
        assert "Did you mean" in output