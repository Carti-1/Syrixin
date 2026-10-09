"""
Testes para o projeto Syrixin.
Usa unittest.mock para simular chamadas ao psutil, evitando dependência de hardware real.
"""

import unittest
from unittest.mock import patch, MagicMock

from monitor.cpu import get_cpu_use
from monitor.memory import get_ram_use
from monitor.disk import get_disk_use
from monitor.battery import get_battery, battery_status
from models.system_info import SystemInfo
from utils.formatter import format_cpu, format_ram, format_disk, format_battery


# ---------------------------------------------------------------------------
# Helpers — factories de mocks reutilizáveis
# ---------------------------------------------------------------------------

def _make_ram(total_gb=16, percent=50.0):
    ram = MagicMock()
    ram.total = total_gb * (1024 ** 3)
    ram.percent = percent
    return ram


def _make_disk(used_gb=100, total_gb=500, percent=20.0):
    disk = MagicMock()
    disk.used = used_gb * (1024 ** 3)
    disk.total = total_gb * (1024 ** 3)
    disk.percent = percent
    return disk


def _make_battery(percent=80.0, power_plugged=True):
    battery = MagicMock()
    battery.percent = percent
    battery.power_plugged = power_plugged
    return battery


# ---------------------------------------------------------------------------
# monitor/cpu.py
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# monitor/memory.py
# ---------------------------------------------------------------------------

class TestGetRamUse(unittest.TestCase):

    @patch("monitor.memory.psutil.virtual_memory")
    def test_returns_psutil_object(self, mock_vm):
        mock_vm.return_value = _make_ram(16, 60.0)
        result = get_ram_use()
        self.assertEqual(result.percent, 60.0)
        mock_vm.assert_called_once()


# ---------------------------------------------------------------------------
# monitor/disk.py
# ---------------------------------------------------------------------------

class TestGetDiskUse(unittest.TestCase):

    @patch("monitor.disk.psutil.disk_usage")
    def test_returns_psutil_object(self, mock_disk):
        mock_disk.return_value = _make_disk(100, 500, 20.0)
        result = get_disk_use()
        self.assertEqual(result.percent, 20.0)
        mock_disk.assert_called_once_with("/")


# ---------------------------------------------------------------------------
# monitor/battery.py
# ---------------------------------------------------------------------------

class TestGetBattery(unittest.TestCase):

    @patch("monitor.battery.psutil.sensors_battery")
    def test_returns_battery_when_present(self, mock_sb):
        mock_sb.return_value = _make_battery(75.0, True)
        result = get_battery()
        self.assertIsNotNone(result)
        self.assertEqual(result.percent, 75.0)

    @patch("monitor.battery.psutil.sensors_battery", return_value=None)
    def test_returns_none_when_no_battery(self, _):
        result = get_battery()
        self.assertIsNone(result)


class TestBatteryStatus(unittest.TestCase):

    def test_charging(self):
        battery = _make_battery(power_plugged=True)
        self.assertEqual(battery_status(battery), "Charging")

    def test_on_battery(self):
        battery = _make_battery(power_plugged=False)
        self.assertEqual(battery_status(battery), "On battery")

    def test_none_battery(self):
        result = battery_status(None)
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# models/system_info.py
# ---------------------------------------------------------------------------

class TestSystemInfo(unittest.TestCase):

    def _build(self, **kwargs):
        defaults = dict(
            cpu=55.0,
            ram=_make_ram(),
            disk=_make_disk(),
            battery=_make_battery(),
            battery_status="Charging",
        )
        defaults.update(kwargs)
        return SystemInfo(**defaults)

    def test_attributes_are_stored(self):
        info = self._build(cpu=72.3)
        self.assertEqual(info.cpu, 72.3)
        self.assertEqual(info.battery_status, "Charging")

    def test_none_battery_accepted(self):
        info = self._build(battery=None, battery_status=None)
        self.assertIsNone(info.battery)
        self.assertIsNone(info.battery_status)


# ---------------------------------------------------------------------------
# utils/formatter.py
# ---------------------------------------------------------------------------

class TestFormatCpu(unittest.TestCase):

    def test_normal(self):
        self.assertEqual(format_cpu(45.0), "45.0%")

    def test_zero(self):
        self.assertEqual(format_cpu(0.0), "0.0%")

    def test_hundred(self):
        self.assertEqual(format_cpu(100.0), "100.0%")


class TestFormatRam(unittest.TestCase):

    def test_output_format(self):
        ram = _make_ram(total_gb=8, percent=75.0)
        result = format_ram(ram)
        self.assertIn("8.00 GB", result)
        self.assertIn("75.0%", result)

    def test_16gb(self):
        ram = _make_ram(total_gb=16, percent=50.0)
        result = format_ram(ram)
        self.assertIn("16.00 GB", result)
        self.assertIn("50.0%", result)


class TestFormatDisk(unittest.TestCase):

    def test_output_format(self):
        disk = _make_disk(used_gb=200, total_gb=500, percent=40.0)
        result = format_disk(disk)
        self.assertIn("200.00 GB", result)
        self.assertIn("500.00 GB", result)
        self.assertIn("40.0%", result)

    def test_small_disk(self):
        disk = _make_disk(used_gb=1, total_gb=10, percent=10.0)
        result = format_disk(disk)
        self.assertIn("1.00 GB", result)
        self.assertIn("10.00 GB", result)


class TestFormatBattery(unittest.TestCase):

    def test_with_battery_charging(self):
        battery = _make_battery(percent=90.0, power_plugged=True)
        result = format_battery(battery, "Charging")
        self.assertIn("90.0%", result)
        self.assertIn("Charging", result)

    def test_with_battery_discharging(self):
        battery = _make_battery(percent=35.0, power_plugged=False)
        result = format_battery(battery, "On battery")
        self.assertIn("35.0%", result)
        self.assertIn("On battery", result)

    def test_no_battery(self):
        result = format_battery(None, None)
        self.assertEqual(result, "N/A")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
