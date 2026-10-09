"""
Documents how each component behaves when psutil raises errors
or receives malformed input.

Classes:
  TestCollectorFailures        — collectors still propagate OSError unchanged
  TestCollectMetrics           — collect_metrics() stores None and calls log_error
  TestCheckAlertsFailures      — check_alerts handles None metrics gracefully
  TestFormatterFailures        — formatter raises AttributeError for malformed objects
"""

import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from monitor.cpu import get_cpu_use
from monitor.memory import get_ram_use
from monitor.disk import get_disk_use
from monitor.battery import get_battery
from utils.formatter import format_ram
from main import check_alerts, collect_metrics
from models.system_info import SystemInfo


# ---------------------------------------------------------------------------
# Collector-level failures — collectors still propagate exceptions unchanged
# ---------------------------------------------------------------------------

class TestCollectorFailures(unittest.TestCase):

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
        """get_battery propagates OSError from psutil.sensors_battery (no try/except)."""
        with patch('monitor.battery.psutil.sensors_battery', side_effect=OSError('Battery error')):
            with self.assertRaises(OSError):
                get_battery()


# ---------------------------------------------------------------------------
# collect_metrics() — None stored and log_error called on collector failure
# ---------------------------------------------------------------------------

class TestCollectMetrics(unittest.TestCase):

    def test_cpu_failure_stores_none_and_calls_log_error(self):
        """When get_cpu_use raises, collect_metrics stores None for cpu and calls log_err."""
        log_err = MagicMock()
        with patch('monitor.cpu.psutil.cpu_percent', side_effect=OSError('CPU error')):
            cpu, ram, disk, battery = collect_metrics(log_err=log_err)
        self.assertIsNone(cpu)
        log_err.assert_any_call("Failed to collect CPU data: CPU error")

    def test_ram_failure_stores_none_and_calls_log_error(self):
        """When get_ram_use raises, collect_metrics stores None for ram and calls log_err."""
        log_err = MagicMock()
        with patch('monitor.memory.psutil.virtual_memory', side_effect=OSError('RAM error')):
            cpu, ram, disk, battery = collect_metrics(log_err=log_err)
        self.assertIsNone(ram)
        log_err.assert_any_call("Failed to collect RAM data: RAM error")

    def test_disk_failure_stores_none_and_calls_log_error(self):
        """When get_disk_use raises, collect_metrics stores None for disk and calls log_err."""
        log_err = MagicMock()
        with patch('monitor.disk.psutil.disk_usage', side_effect=OSError('Disk error')):
            cpu, ram, disk, battery = collect_metrics(log_err=log_err)
        self.assertIsNone(disk)
        log_err.assert_any_call("Failed to collect disk data: Disk error")

    def test_battery_failure_stores_none_and_calls_log_error(self):
        """When get_battery raises, collect_metrics stores None for battery and calls log_err."""
        log_err = MagicMock()
        with patch('monitor.battery.psutil.sensors_battery', side_effect=OSError('Battery error')):
            cpu, ram, disk, battery = collect_metrics(log_err=log_err)
        self.assertIsNone(battery)
        log_err.assert_any_call("Failed to collect battery data: Battery error")

    def test_one_failure_does_not_prevent_other_metrics(self):
        """A CPU failure does not stop RAM, disk, or battery from being collected."""
        log_err = MagicMock()
        with patch('monitor.cpu.psutil.cpu_percent', side_effect=OSError('CPU error')):
            cpu, ram, disk, battery = collect_metrics(log_err=log_err)
        self.assertIsNone(cpu)
        # The other three are still attempted and should not be None
        # (unless the environment itself lacks them; we just verify log_err was
        #  called exactly once — only for CPU)
        log_err.assert_called_once()


# ---------------------------------------------------------------------------
# check_alerts failures — None metrics must not raise
# ---------------------------------------------------------------------------

class TestCheckAlertsFailures(unittest.TestCase):

    def test_check_alerts_cpu_none_does_not_raise(self):
        """check_alerts does not raise when cpu=None; no CPU alert in result."""
        ram = SimpleNamespace(total=16 * (1024 ** 3), percent=50.0)
        disk = SimpleNamespace(used=100 * (1024 ** 3), total=500 * (1024 ** 3), percent=50.0)
        battery = SimpleNamespace(percent=80.0, power_plugged=True)
        system = SystemInfo(cpu=None, ram=ram, disk=disk, battery=battery, battery_status='Charging')
        result = check_alerts(system)
        self.assertIsInstance(result, list)
        self.assertTrue(all("CPU" not in a for a in result))

    def test_check_alerts_ram_none_does_not_raise(self):
        """check_alerts does not raise when ram=None; no RAM alert in result."""
        disk = SimpleNamespace(used=100 * (1024 ** 3), total=500 * (1024 ** 3), percent=50.0)
        battery = SimpleNamespace(percent=80.0, power_plugged=True)
        system = SystemInfo(cpu=50.0, ram=None, disk=disk, battery=battery, battery_status='Charging')
        result = check_alerts(system)
        self.assertIsInstance(result, list)
        self.assertTrue(all("RAM" not in a for a in result))

    def test_check_alerts_disk_none_does_not_raise(self):
        """check_alerts does not raise when disk=None; no disk alert in result."""
        ram = SimpleNamespace(total=16 * (1024 ** 3), percent=50.0)
        battery = SimpleNamespace(percent=80.0, power_plugged=True)
        system = SystemInfo(cpu=50.0, ram=ram, disk=None, battery=battery, battery_status='Charging')
        result = check_alerts(system)
        self.assertIsInstance(result, list)
        self.assertTrue(all("Disk" not in a for a in result))


# ---------------------------------------------------------------------------
# Formatter failures — malformed objects (not None) still raise
# ---------------------------------------------------------------------------

class TestFormatterFailures(unittest.TestCase):

    def test_format_ram_missing_total_raises_attribute_error(self):
        """format_ram raises AttributeError when the object has no 'total' attribute."""
        bad_ram = SimpleNamespace(percent=50.0)  # no 'total'
        with self.assertRaises(AttributeError):
            format_ram(bad_ram)


if __name__ == '__main__':
    unittest.main()
