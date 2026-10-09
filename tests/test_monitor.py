"""Tests for run_monitor() in main.py."""

import unittest
from unittest.mock import MagicMock, patch

from main import run_monitor


def _make_collect():
    """Returns a mock collect_metrics that yields safe dummy data."""
    mock = MagicMock()
    mock.return_value = (50.0, None, None, None)
    return mock


def _sleep_raises_after(n: int) -> MagicMock:
    """Returns a mock time.sleep that raises KeyboardInterrupt on the nth call."""
    calls = []

    def side_effect(interval):
        calls.append(interval)
        if len(calls) >= n:
            raise KeyboardInterrupt

    m = MagicMock(side_effect=side_effect)
    return m


class TestRunMonitor(unittest.TestCase):

    def test_collect_called_correct_number_of_times(self):
        """run_monitor calls collect_metrics once per cycle before interrupt."""
        collect = _make_collect()
        check   = MagicMock(return_value=[])
        sleep   = _sleep_raises_after(3)
        clear   = MagicMock()

        with patch('main.log_info'), patch('main.display'):
            run_monitor(interval=1, _collect=collect, _check=check,
                        _sleep=sleep, _clear=clear)

        self.assertEqual(collect.call_count, 3)

    def test_keyboard_interrupt_logs_stopped_message(self):
        """KeyboardInterrupt is caught and log_info is called with the stop message."""
        collect = _make_collect()
        sleep   = _sleep_raises_after(1)

        with patch('main.log_info') as mock_log, patch('main.display'):
            run_monitor(interval=1, _collect=collect,
                        _check=MagicMock(return_value=[]),
                        _sleep=sleep, _clear=MagicMock())

        mock_log.assert_any_call('Monitor stopped by user.')

    def test_clear_called_each_cycle(self):
        """The clear callable is called once per cycle."""
        collect = _make_collect()
        sleep   = _sleep_raises_after(3)
        clear   = MagicMock()

        with patch('main.log_info'), patch('main.display'):
            run_monitor(interval=1, _collect=collect,
                        _check=MagicMock(return_value=[]),
                        _sleep=sleep, _clear=clear)

        self.assertEqual(clear.call_count, 3)

    def test_sleep_called_with_interval(self):
        """time.sleep is called with the interval value passed to run_monitor."""
        collect = _make_collect()
        sleep   = _sleep_raises_after(1)

        with patch('main.log_info'), patch('main.display'):
            run_monitor(interval=7, _collect=collect,
                        _check=MagicMock(return_value=[]),
                        _sleep=sleep, _clear=MagicMock())

        sleep.assert_called_with(7)

    def test_check_alerts_called_each_cycle(self):
        """check_alerts is called once per cycle."""
        collect = _make_collect()
        check   = MagicMock(return_value=[])
        sleep   = _sleep_raises_after(2)

        with patch('main.log_info'), patch('main.display'):
            run_monitor(interval=1, _collect=collect, _check=check,
                        _sleep=sleep, _clear=MagicMock())

        self.assertEqual(check.call_count, 2)

    # ------------------------------------------------------------------
    # Problem 1 — battery_status is injectable via _battery_status param
    # ------------------------------------------------------------------

    def test_battery_status_injectable_in_run_monitor(self):
        """_battery_status parameter is used instead of the real battery_status."""
        collect = _make_collect()
        fake_status = MagicMock(return_value="Mocked")
        sleep = _sleep_raises_after(1)

        with patch('main.log_info'), patch('main.display'):
            run_monitor(interval=1, _collect=collect,
                        _check=MagicMock(return_value=[]),
                        _sleep=sleep, _clear=MagicMock(),
                        _battery_status=fake_status)

        fake_status.assert_called_once()

    # ------------------------------------------------------------------
    # Problem 2 — non-KeyboardInterrupt exceptions are logged; loop continues
    # ------------------------------------------------------------------

    def test_unexpected_exception_is_logged_and_loop_continues(self):
        """An OSError mid-cycle is caught, logged via log_error, and the loop continues."""
        # First cycle raises OSError, second cycle completes, then sleep raises KI
        collect = MagicMock(side_effect=[OSError("boom"), (50.0, None, None, None)])
        sleep = _sleep_raises_after(1)   # raises KeyboardInterrupt on the 1st sleep call

        with patch('main.log_info'), patch('main.log_error') as mock_log_err, \
             patch('main.display'):
            run_monitor(interval=1, _collect=collect,
                        _check=MagicMock(return_value=[]),
                        _sleep=sleep, _clear=MagicMock())

        mock_log_err.assert_any_call("Unexpected error during monitoring cycle: boom")

    def test_loop_does_not_exit_on_first_exception(self):
        """run_monitor keeps running after an exception; collect is called again."""
        collect = MagicMock(side_effect=[
            OSError("cycle 1 error"),
            (50.0, None, None, None),   # cycle 2 succeeds
        ])
        sleep = _sleep_raises_after(1)

        with patch('main.log_info'), patch('main.log_error'), patch('main.display'):
            run_monitor(interval=1, _collect=collect,
                        _check=MagicMock(return_value=[]),
                        _sleep=sleep, _clear=MagicMock())

        self.assertEqual(collect.call_count, 2)

    # ------------------------------------------------------------------
    # Problem 3 — header/timestamp print has test coverage
    # ------------------------------------------------------------------

    def test_header_print_contains_monitor_label(self):
        """run_monitor prints a header containing 'Syrixin Monitor' each cycle."""
        collect = _make_collect()
        sleep = _sleep_raises_after(1)

        with patch('main.log_info'), patch('main.display'), \
             patch('builtins.print') as mock_print:
            run_monitor(interval=1, _collect=collect,
                        _check=MagicMock(return_value=[]),
                        _sleep=sleep, _clear=MagicMock())

        printed = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(
            any("Syrixin Monitor" in s for s in printed),
            "Expected 'Syrixin Monitor' in at least one print call"
        )


if __name__ == "__main__":
    unittest.main()
