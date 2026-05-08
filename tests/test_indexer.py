import sys
import os
import json
import tempfile

# Let tests import files from the src folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from indexer import tokenise, build_index, save_index, load_index


# Tests for tokenise()

class TestTokenise:
    def test_makes_words_lowercase(self):
        assert tokenise("Hello World") == ["hello", "world"]

    def test_removes_punctuation(self):
        tokens = tokenise("Hello, world!")
        assert "hello" in tokens
        assert "world" in tokens
        assert "," not in tokens

    def test_removes_numbers(self):
        tokens = tokenise("There are 3 apples")
        assert "3" not in tokens
        assert "apples" in tokens

    def test_handles_apostrophes(self):
        # Apostrophes should be removed
        tokens = tokenise("don't")
        assert "'" not in tokens

    def test_empty_string_gives_empty_list(self):
        assert tokenise("") == []

    def test_whitespace_only_gives_empty_list(self):
        assert tokenise("   \t\n  ") == []

    def test_handles_hyphenated_words(self):
        tokens = tokenise("The quick-brown fox.")
        assert "the" in tokens
        assert "quick" in tokens
        assert "fox" in tokens


# Tests for build_index()

class TestBuildIndex:
    PAGES = [
        ("https://example.com/page/1/", "The quick brown fox"),
        ("https://example.com/page/2/", "The lazy fox"),
    ]

    def test_words_appear_in_index(self):
        index = build_index(self.PAGES)
        assert "fox" in index
        assert "quick" in index

    def test_frequency_is_counted_correctly(self):
        pages = [("https://example.com/", "hello hello world")]
        index = build_index(pages)
        assert index["hello"]["https://example.com/"]["frequency"] == 2
        assert index["world"]["https://example.com/"]["frequency"] == 1

    def test_positions_are_recorded_correctly(self):
        pages = [("https://example.com/", "alpha beta alpha")]
        index = build_index(pages)

        # alpha appears first and third
        assert 0 in index["alpha"]["https://example.com/"]["positions"]
        assert 2 in index["alpha"]["https://example.com/"]["positions"]

        # beta appears second
        assert 1 in index["beta"]["https://example.com/"]["positions"]

    def test_same_word_across_multiple_pages(self):
        index = build_index(self.PAGES)

        # fox should be stored for both pages
        assert "https://example.com/page/1/" in index["fox"]
        assert "https://example.com/page/2/" in index["fox"]

    def test_empty_pages_list_gives_empty_index(self):
        assert build_index([]) == {}

    def test_indexing_is_case_insensitive(self):
        pages = [("https://example.com/", "Hello hello HELLO")]
        index = build_index(pages)

        # All versions of hello should count as one word
        assert index["hello"]["https://example.com/"]["frequency"] == 3

    def test_common_words_like_the_are_indexed(self):
        # Stopwords are not removed
        pages = [("https://example.com/", "the quick brown fox")]
        index = build_index(pages)
        assert "the" in index


# Tests for saving and loading the index

class TestIndexPersistence:
    SAMPLE_INDEX = {
        "hello": {
            "https://example.com/": {"frequency": 2, "positions": [0, 5]}
        }
    }

    def test_save_then_load_gives_same_data(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            tmp_path = f.name

        try:
            save_index(self.SAMPLE_INDEX)

            from indexer import INDEX_PATH
            loaded = load_index(INDEX_PATH)

            assert loaded == self.SAMPLE_INDEX
        finally:
            os.unlink(tmp_path)

    def test_loading_missing_file_raises_error(self):
        with pytest.raises(FileNotFoundError):
            load_index("/tmp/this_file_does_not_exist_12345.json")

    def test_saved_file_is_valid_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            tmp_path = f.name

        try:
            save_index(self.SAMPLE_INDEX)

            from indexer import INDEX_PATH
            with open(INDEX_PATH) as f:
                data = json.load(f)

            assert isinstance(data, dict)
        finally:
            os.unlink(tmp_path)