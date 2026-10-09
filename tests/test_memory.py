"""Testes para monitor/memory.py"""

import unittest
from unittest.mock import patch, MagicMock

from monitor.memory import get_ram_use


def _make_ram(total_gb=16, percent=50.0):
    ram = MagicMock()
    ram.total = total_gb * (1024 ** 3)
    ram.percent = percent
    return ram


class TestGetRamUse(unittest.TestCase):

    @patch("monitor.memory.psutil.virtual_memory")
    def test_returns_psutil_object(self, mock_vm):
        mock_vm.return_value = _make_ram(16, 60.0)
        result = get_ram_use()
        self.assertEqual(result.percent, 60.0)
        mock_vm.assert_called_once()

    @patch("monitor.memory.psutil.virtual_memory")
    def test_total_is_preserved(self, mock_vm):
        mock_vm.return_value = _make_ram(total_gb=32, percent=80.0)
        result = get_ram_use()
        self.assertEqual(result.total, 32 * (1024 ** 3))


if __name__ == "__main__":
    unittest.main()
