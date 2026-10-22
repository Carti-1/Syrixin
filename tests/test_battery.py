"""Testes para monitor/battery.py"""

import unittest
from unittest.mock import patch, MagicMock

from monitor.battery import get_battery, battery_status


def _make_battery(percent=80.0, power_plugged=True):
    battery = MagicMock()
    battery.percent = percent
    battery.power_plugged = power_plugged
    return battery


class TestGetBattery(unittest.TestCase):

    @patch("monitor.battery.psutil.sensors_battery")
    def test_returns_battery_when_present(self, mock_sb):
        mock_sb.return_value = _make_battery(75.0, True)
        result = get_battery()
        self.assertIsNotNone(result)
        self.assertEqual(result.percent, 75.0)

    @patch("monitor.battery.psutil.sensors_battery", return_value=None)
    def test_returns_none_when_no_battery(self, _):
        # Máquinas sem bateria (desktops) retornam None
        result = get_battery()
        self.assertIsNone(result)


class TestBatteryStatus(unittest.TestCase):
    """
    battery_status retorna "Charging" ou "On battery".
    Quando battery=None, a função retorna None implicitamente
    (nenhum branch é executado).
    """

    def test_charging(self):
        battery = _make_battery(power_plugged=True)
        self.assertEqual(battery_status(battery), "Charging")

    def test_on_battery(self):
        battery = _make_battery(power_plugged=False)
        self.assertEqual(battery_status(battery), "On battery")

    def test_none_returns_none(self):
        # battery_status(None) não entra em nenhum branch — retorna None
        result = battery_status(None)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
