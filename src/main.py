import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from crawler import crawl, BASE_URL
from indexer import build_index, save_index, load_index, INDEX_PATH
from search import print_word, cmd_find

BANNER = """
╔══════════════════════════════════════════╗
║               Search Engine              ║
╚══════════════════════════════════════════╝
Type 'help' for available commands.
"""

HELP_TEXT = """
Commands:
  build          Crawl the site and build/save the inverted index
  load           Load a previously saved index from disk
  print <word>   Show the inverted index entry for <word>
  find <query>   Find pages containing all words in <query>
  help           Show this help message
  quit / exit    Exit the shell
"""


def run_shell() -> None:
    """Main REPL loop for the search engine CLI."""
    print(BANNER)

    index: dict | None = None

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not raw:
            continue

        parts = raw.split(maxsplit=1)
        command = parts[0].lower()
        argument = parts[1] if len(parts) > 1 else ""

        #  build 
        if command == "build":
            print(f"\nCrawling {BASE_URL} …\n")
            pages = crawl(verbose=True)
            if not pages:
                print("No pages crawled. Check your network connection.")
                continue
            index = build_index(pages)
            save_index(index, INDEX_PATH)
            print(f"\nDone. Index contains {len(index)} unique words.\n")

        #  load 
        elif command == "load":
            try:
                index = load_index(INDEX_PATH)
                print(f"Ready. {len(index)} words in index.\n")
            except FileNotFoundError as e:
                print(f"[ERROR] {e}\n")

        #  print 
        elif command == "print":
            if index is None:
                print("[ERROR] No index loaded. Run 'build' or 'load' first.\n")
            elif not argument:
                print("Usage: print <word>\n")
            else:
                print_word(index, argument)

        #  find 
        elif command == "find":
            if index is None:
                print("[ERROR] No index loaded. Run 'build' or 'load' first.\n")
            elif not argument:
                print("Please provide at least one search term.\n")
            else:
                cmd_find(index, argument)

        #  help 
        elif command in ("help", "?"):
            print(HELP_TEXT)

        #  quit 
        elif command in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        #  unknown 
        else:
            print(f"Unknown command: '{command}'. Type 'help' for usage.\n")


if __name__ == "__main__":
    run_shell()
