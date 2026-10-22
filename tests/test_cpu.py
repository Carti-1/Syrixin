"""Testes para monitor/cpu.py"""

import unittest
from unittest.mock import patch

from monitor.cpu import get_cpu_use


class TestGetCpuUse(unittest.TestCase):

    @patch("monitor.cpu.psutil.cpu_percent", return_value=42.5)
    def test_returns_float(self, mock_cpu):
        result = get_cpu_use()
        self.assertEqual(result, 42.5)
        mock_cpu.assert_called_once_with(interval=1)

    @patch("monitor.cpu.psutil.cpu_percent", return_value=0.0)
    def test_zero_cpu(self, _):
        self.assertEqual(get_cpu_use(), 0.0)

    @patch("monitor.cpu.psutil.cpu_percent", return_value=100.0)
    def test_full_cpu(self, _):
        self.assertEqual(get_cpu_use(), 100.0)


if __name__ == "__main__":
    unittest.main()
