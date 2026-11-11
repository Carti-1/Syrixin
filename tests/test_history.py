"""Tests for the history command in main.py."""

import unittest
from unittest.mock import patch

from main import show_history


class TestShowHistory(unittest.TestCase):

    @patch("builtins.print")
    @patch("main.Database")
    def test_reads_requested_number_of_rows_prints_and_closes(self, database_class, mock_print):
        database = database_class.return_value
        rows = [("2026-11-11T12:00:00+00:00", 42.5, None, None, None, None, None, None, None)]
        database.get_recent.return_value = rows

        show_history(limit=3)

        database.get_recent.assert_called_once_with(3)
        mock_print.assert_called_once()
        self.assertIn("CPU: 42.5%", mock_print.call_args.args[0])
        database.close.assert_called_once()

    @patch("main.Database")
    def test_closes_database_if_history_query_fails(self, database_class):
        database = database_class.return_value
        database.get_recent.side_effect = RuntimeError("query failed")

        with self.assertRaisesRegex(RuntimeError, "query failed"):
            show_history()

        database.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
