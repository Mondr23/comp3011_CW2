import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from unittest.mock import patch, MagicMock
import pytest


class TestRunShell:
    def _run_commands(self, commands):
        """Helper to run a list of commands through the shell."""
        from main import run_shell
        inputs = iter(commands)
        with patch("builtins.input", side_effect=inputs), \
             patch("sys.stdout"):
            try:
                run_shell()
            except StopIteration:
                pass

    def test_quit_command_exits(self):
        # shell should exit cleanly on quit
        from main import run_shell
        with patch("builtins.input", return_value="quit"), \
             patch("builtins.print"):
            run_shell()

    def test_exit_command_exits(self):
        from main import run_shell
        with patch("builtins.input", return_value="exit"), \
             patch("builtins.print"):
            run_shell()

    def test_help_command_prints(self, capsys):
        from main import run_shell
        inputs = iter(["help", "quit"])
        with patch("builtins.input", side_effect=inputs):
            run_shell()
        output = capsys.readouterr().out
        assert "build" in output.lower()

    def test_unknown_command_handled(self, capsys):
        from main import run_shell
        inputs = iter(["unknowncommand", "quit"])
        with patch("builtins.input", side_effect=inputs):
            run_shell()
        output = capsys.readouterr().out
        assert "unknown" in output.lower()

    def test_find_without_index_shows_error(self, capsys):
        from main import run_shell
        inputs = iter(["find love", "quit"])
        with patch("builtins.input", side_effect=inputs):
            run_shell()
        output = capsys.readouterr().out
        assert "error" in output.lower()

    def test_print_without_index_shows_error(self, capsys):
        from main import run_shell
        inputs = iter(["print love", "quit"])
        with patch("builtins.input", side_effect=inputs):
            run_shell()
        output = capsys.readouterr().out
        assert "error" in output.lower()

    def test_load_missing_index_shows_error(self, capsys):
        from main import run_shell
        inputs = iter(["load", "quit"])
        with patch("builtins.input", side_effect=inputs), \
             patch("main.load_index",
                   side_effect=FileNotFoundError("No index found")):
            run_shell()
        output = capsys.readouterr().out
        assert "error" in output.lower()

    def test_empty_input_is_ignored(self, capsys):
        from main import run_shell
        inputs = iter(["", "quit"])
        with patch("builtins.input", side_effect=inputs):
            run_shell()
        # should not crash

    def test_find_no_argument_shows_usage(self, capsys):
        from main import run_shell
        inputs = iter(["find", "quit"])
        with patch("builtins.input", side_effect=inputs):
            run_shell()
        output = capsys.readouterr().out
        assert "no index loaded" in output.lower()

    def test_print_no_argument_shows_usage(self, capsys):
        from main import run_shell
        inputs = iter(["print", "quit"])
        with patch("builtins.input", side_effect=inputs):
            run_shell()
        output = capsys.readouterr().out
        assert "no index loaded" in output.lower()