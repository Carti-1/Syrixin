"""
Documents how each component behaves when psutil raises errors
or receives malformed input. These tests verify current behavior
without changing any implementation.
"""

import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from monitor.cpu import get_cpu_use
from monitor.memory import get_ram_use
from monitor.disk import get_disk_use
from monitor.battery import get_battery
from utils.formatter import format_ram
from main import check_alerts
from models.system_info import SystemInfo


class TestMonitorFailures(unittest.TestCase):

    def test_cpu_os_error_propagates(self):
        """get_cpu_use propagates OSError from psutil.cpu_percent (no try/except)."""
        with patch('monitor.cpu.psutil.cpu_percent', side_effect=OSError('CPU error')):
            with self.assertRaises(OSError):
                get_cpu_use()

    def test_ram_os_error_propagates(self):
        """get_ram_use propagates OSError from psutil.virtual_memory."""
        with patch('monitor.memory.psutil.virtual_memory', side_effect=OSError('RAM error')):
            with self.assertRaises(OSError):
                get_ram_use()

    def test_disk_os_error_propagates(self):
        """get_disk_use propagates OSError from psutil.disk_usage."""
        with patch('monitor.disk.psutil.disk_usage', side_effect=OSError('Disk error')):
            with self.assertRaises(OSError):
                get_disk_use()

    def test_battery_os_error_propagates(self):
        """get_battery propagates OSError from psutil.sensors_battery (no try/except).
        If this test fails because get_battery now handles OSError, update accordingly.
        """
        with patch('monitor.battery.psutil.sensors_battery', side_effect=OSError('Battery error')):
            with self.assertRaises(OSError):
                get_battery()

    def test_check_alerts_cpu_none_raises_type_error(self):
        """check_alerts raises TypeError when cpu is None (None > 90 is not valid in Python 3)."""
        ram = SimpleNamespace(total=16 * (1024 ** 3), percent=50.0)
        disk = SimpleNamespace(used=100 * (1024 ** 3), total=500 * (1024 ** 3), percent=50.0)
        battery = SimpleNamespace(percent=80.0, power_plugged=True)
        system = SystemInfo(cpu=None, ram=ram, disk=disk, battery=battery, battery_status='Charging')
        with self.assertRaises(TypeError):
            check_alerts(system)

    def test_format_ram_missing_total_raises_attribute_error(self):
        """format_ram raises AttributeError when the object has no 'total' attribute."""
        bad_ram = SimpleNamespace(percent=50.0)  # no 'total'
        with self.assertRaises(AttributeError):
            format_ram(bad_ram)


if __name__ == '__main__':
    unittest.main()
