"""Testes para monitor/disk.py"""

import unittest
from unittest.mock import patch, MagicMock

from monitor.disk import get_disk_use


def _make_disk(used_gb=100, total_gb=500, percent=20.0):
    disk = MagicMock()
    disk.used = used_gb * (1024 ** 3)
    disk.total = total_gb * (1024 ** 3)
    disk.percent = percent
    return disk


class TestGetDiskUse(unittest.TestCase):

    @patch("monitor.disk.psutil.disk_usage")
    def test_returns_psutil_object(self, mock_disk):
        mock_disk.return_value = _make_disk(100, 500, 20.0)
        result = get_disk_use()
        self.assertEqual(result.percent, 20.0)

    @patch("monitor.disk.psutil.disk_usage")
    def test_called_with_root_path(self, mock_disk):
        # A implementação usa '/' como caminho fixo.
        # No Windows, isso pode não representar a unidade desejada.
        # Futuro: tornar o caminho configurável por plataforma.
        mock_disk.return_value = _make_disk()
        get_disk_use()
        mock_disk.assert_called_once_with("/")

    @patch("monitor.disk.psutil.disk_usage")
    def test_used_and_total_preserved(self, mock_disk):
        mock_disk.return_value = _make_disk(used_gb=200, total_gb=1000, percent=20.0)
        result = get_disk_use()
        self.assertEqual(result.used, 200 * (1024 ** 3))
        self.assertEqual(result.total, 1000 * (1024 ** 3))


if __name__ == "__main__":
    unittest.main()
