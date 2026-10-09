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


if __name__ == "__main__":
    unittest.main()
