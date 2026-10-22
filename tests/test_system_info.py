"""Testes para models/system_info.py"""

import unittest
from types import SimpleNamespace

from models.system_info import SystemInfo


def _make_system(**overrides):
    defaults = dict(
        cpu=55.0,
        ram=SimpleNamespace(total=16 * (1024 ** 3), percent=50.0),
        disk=SimpleNamespace(used=100 * (1024 ** 3), total=500 * (1024 ** 3), percent=20.0),
        battery=SimpleNamespace(percent=80.0, power_plugged=True),
        battery_status="Charging",
    )
    defaults.update(overrides)
    return SystemInfo(**defaults)


class TestSystemInfo(unittest.TestCase):

    def test_all_attributes_stored(self):
        info = _make_system(cpu=72.3)
        self.assertEqual(info.cpu, 72.3)
        self.assertEqual(info.battery_status, "Charging")
        self.assertIsNotNone(info.ram)
        self.assertIsNotNone(info.disk)
        self.assertIsNotNone(info.battery)

    def test_none_battery_accepted(self):
        info = _make_system(battery=None, battery_status=None)
        self.assertIsNone(info.battery)
        self.assertIsNone(info.battery_status)

    def test_cpu_stored_as_given(self):
        info = _make_system(cpu=0.0)
        self.assertEqual(info.cpu, 0.0)


if __name__ == "__main__":
    unittest.main()
