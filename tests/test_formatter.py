"""Testes para utils/formatter.py"""

import unittest
from types import SimpleNamespace

from utils.formatter import (
    format_cpu,
    format_ram,
    format_disk,
    format_battery,
    format_history,
)


def _ram(total_gb, percent):
    return SimpleNamespace(total=total_gb * (1024 ** 3), percent=percent)


def _disk(used_gb, total_gb, percent):
    return SimpleNamespace(
        used=used_gb * (1024 ** 3),
        total=total_gb * (1024 ** 3),
        percent=percent,
    )


def _battery(percent):
    return SimpleNamespace(percent=percent)


class TestFormatCpu(unittest.TestCase):

    def test_normal(self):
        self.assertEqual(format_cpu(45.0), "45.0%")

    def test_zero(self):
        self.assertEqual(format_cpu(0.0), "0.0%")

    def test_hundred(self):
        self.assertEqual(format_cpu(100.0), "100.0%")

    def test_none_returns_na(self):
        self.assertEqual(format_cpu(None), "N/A")


class TestFormatRam(unittest.TestCase):

    def test_8gb_75_percent(self):
        result = format_ram(_ram(8, 75.0))
        self.assertIn("8.00 GB", result)
        self.assertIn("75.0%", result)

    def test_16gb_50_percent(self):
        result = format_ram(_ram(16, 50.0))
        self.assertIn("16.00 GB", result)
        self.assertIn("50.0%", result)

    def test_none_returns_na(self):
        self.assertEqual(format_ram(None), "N/A")


class TestFormatDisk(unittest.TestCase):

    def test_used_total_percent_present(self):
        result = format_disk(_disk(200, 500, 40.0))
        self.assertIn("200.00 GB", result)
        self.assertIn("500.00 GB", result)
        self.assertIn("40.0%", result)

    def test_small_disk(self):
        result = format_disk(_disk(1, 10, 10.0))
        self.assertIn("1.00 GB", result)
        self.assertIn("10.00 GB", result)

    def test_none_returns_na(self):
        self.assertEqual(format_disk(None), "N/A")


class TestFormatBattery(unittest.TestCase):

    def test_charging(self):
        result = format_battery(_battery(90.0), "Charging")
        self.assertIn("90.0%", result)
        self.assertIn("Charging", result)

    def test_discharging(self):
        result = format_battery(_battery(35.0), "On battery")
        self.assertIn("35.0%", result)
        self.assertIn("On battery", result)

    def test_no_battery_returns_na(self):
        self.assertEqual(format_battery(None, None), "N/A")


class TestFormatHistory(unittest.TestCase):

    def test_empty_rows_returns_friendly_message(self):
        self.assertEqual(
            format_history([]),
            "Nenhum registro de métricas encontrado.",
        )

    def test_formats_all_metrics(self):
        row = (
            "2026-11-11T12:00:00+00:00",
            42.5,
            8 * (1024 ** 3),
            50.0,
            100 * (1024 ** 3),
            500 * (1024 ** 3),
            20.0,
            80.0,
            1,
        )

        result = format_history([row])

        self.assertIn("2026-11-11T12:00:00+00:00", result)
        self.assertIn("CPU: 42.5%", result)
        self.assertIn("RAM: 8.00 GB / 4.00 GB (50.0%)", result)
        self.assertIn("Disco: 100.00 GB / 500.00 GB (20.0%)", result)
        self.assertIn("Bateria: 80.0% (conectado à energia)", result)

    def test_missing_metrics_are_shown_as_na(self):
        row = ("2026-11-11T12:00:00+00:00", None, None, None, None, None, None, None, None)

        result = format_history([row])

        self.assertIn("CPU: N/A", result)
        self.assertIn("RAM: N/A / N/A (N/A)", result)
        self.assertIn("Disco: N/A / N/A (N/A)", result)
        self.assertIn("Bateria: N/A (energia: N/A)", result)


if __name__ == "__main__":
    unittest.main()
