"""
Testes para a lógica de alertas de main.check_alerts().

Cada teste injeta um log_warn falso para capturar mensagens sem
escrever no arquivo de log real.
"""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from main import check_alerts
from models.system_info import SystemInfo


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_system(cpu=50.0, ram_percent=50.0, disk_percent=50.0,
                 battery_percent=80.0, power_plugged=True):
    """Constrói um SystemInfo com valores padrão seguros (sem alertas)."""
    ram = SimpleNamespace(
        total=16 * (1024 ** 3),
        percent=ram_percent,
    )
    disk = SimpleNamespace(
        used=100 * (1024 ** 3),
        total=500 * (1024 ** 3),
        percent=disk_percent,
    )
    battery = SimpleNamespace(percent=battery_percent, power_plugged=power_plugged)
    status = "Charging" if power_plugged else "On battery"
    return SystemInfo(cpu=cpu, ram=ram, disk=disk, battery=battery, battery_status=status)


def _make_system_no_battery(cpu=50.0, ram_percent=50.0, disk_percent=50.0):
    """Constrói um SystemInfo sem bateria (desktop)."""
    ram = SimpleNamespace(total=16 * (1024 ** 3), percent=ram_percent)
    disk = SimpleNamespace(
        used=100 * (1024 ** 3),
        total=500 * (1024 ** 3),
        percent=disk_percent,
    )
    return SystemInfo(cpu=cpu, ram=ram, disk=disk, battery=None, battery_status=None)


# ---------------------------------------------------------------------------
# CPU
# ---------------------------------------------------------------------------

class TestCpuAlerts(unittest.TestCase):

    def test_no_alert_below_threshold(self):
        warn = MagicMock()
        system = _make_system(cpu=90.0)   # exatamente 90 — não dispara
        alerts = check_alerts(system, log_warn=warn)
        cpu_alerts = [a for a in alerts if "CPU" in a]
        self.assertEqual(cpu_alerts, [])
        warn.assert_not_called()

    def test_alert_above_threshold(self):
        warn = MagicMock()
        system = _make_system(cpu=90.1)
        alerts = check_alerts(system, log_warn=warn)
        cpu_alerts = [a for a in alerts if "CPU" in a]
        self.assertEqual(len(cpu_alerts), 1)
        warn.assert_called()

    def test_alert_at_100(self):
        warn = MagicMock()
        system = _make_system(cpu=100.0)
        alerts = check_alerts(system, log_warn=warn)
        self.assertTrue(any("CPU" in a for a in alerts))


# ---------------------------------------------------------------------------
# RAM
# ---------------------------------------------------------------------------

class TestRamAlerts(unittest.TestCase):

    def test_no_alert_at_threshold(self):
        warn = MagicMock()
        system = _make_system(ram_percent=85.0)   # exatamente 85 — não dispara
        alerts = check_alerts(system, log_warn=warn)
        ram_alerts = [a for a in alerts if "RAM" in a]
        self.assertEqual(ram_alerts, [])

    def test_alert_above_threshold(self):
        warn = MagicMock()
        system = _make_system(ram_percent=85.1)
        alerts = check_alerts(system, log_warn=warn)
        ram_alerts = [a for a in alerts if "RAM" in a]
        self.assertEqual(len(ram_alerts), 1)

    def test_alert_at_100(self):
        warn = MagicMock()
        system = _make_system(ram_percent=100.0)
        alerts = check_alerts(system, log_warn=warn)
        self.assertTrue(any("RAM" in a for a in alerts))


# ---------------------------------------------------------------------------
# Disco
# ---------------------------------------------------------------------------

class TestDiskAlerts(unittest.TestCase):

    def test_no_alert_at_threshold(self):
        warn = MagicMock()
        system = _make_system(disk_percent=90.0)   # exatamente 90 — não dispara
        alerts = check_alerts(system, log_warn=warn)
        disk_alerts = [a for a in alerts if "Disk" in a]
        self.assertEqual(disk_alerts, [])

    def test_alert_above_threshold(self):
        warn = MagicMock()
        system = _make_system(disk_percent=90.1)
        alerts = check_alerts(system, log_warn=warn)
        disk_alerts = [a for a in alerts if "Disk" in a]
        self.assertEqual(len(disk_alerts), 1)

    def test_alert_at_full(self):
        warn = MagicMock()
        system = _make_system(disk_percent=100.0)
        alerts = check_alerts(system, log_warn=warn)
        self.assertTrue(any("Disk" in a for a in alerts))


# ---------------------------------------------------------------------------
# Bateria
# ---------------------------------------------------------------------------

class TestBatteryAlerts(unittest.TestCase):

    def test_low_battery_unplugged_triggers_alert(self):
        warn = MagicMock()
        system = _make_system(battery_percent=19.9, power_plugged=False)
        alerts = check_alerts(system, log_warn=warn)
        battery_alerts = [a for a in alerts if "battery" in a.lower() and "Low" in a]
        self.assertEqual(len(battery_alerts), 1)

    def test_battery_at_20_no_alert(self):
        warn = MagicMock()
        system = _make_system(battery_percent=20.0, power_plugged=False)
        alerts = check_alerts(system, log_warn=warn)
        low_alerts = [a for a in alerts if "Low battery" in a]
        self.assertEqual(low_alerts, [])

    def test_low_battery_but_plugged_no_alert(self):
        # Bateria baixa mas conectada não deve disparar
        warn = MagicMock()
        system = _make_system(battery_percent=5.0, power_plugged=True)
        alerts = check_alerts(system, log_warn=warn)
        low_alerts = [a for a in alerts if "Low battery" in a]
        self.assertEqual(low_alerts, [])

    def test_no_battery_triggers_missing_alert(self):
        # Desktop sem bateria — aviso específico, sem exceção
        warn = MagicMock()
        system = _make_system_no_battery()
        alerts = check_alerts(system, log_warn=warn)
        missing = [a for a in alerts if "Battery not" in a]
        self.assertEqual(len(missing), 1)

    def test_no_battery_does_not_trigger_low_battery_alert(self):
        warn = MagicMock()
        system = _make_system_no_battery()
        alerts = check_alerts(system, log_warn=warn)
        low_alerts = [a for a in alerts if "Low battery" in a]
        self.assertEqual(low_alerts, [])


# ---------------------------------------------------------------------------
# Sem alertas
# ---------------------------------------------------------------------------

class TestNoAlerts(unittest.TestCase):

    def test_all_normal_produces_no_alerts(self):
        warn = MagicMock()
        system = _make_system(cpu=50.0, ram_percent=50.0, disk_percent=50.0,
                              battery_percent=80.0, power_plugged=True)
        alerts = check_alerts(system, log_warn=warn)
        self.assertEqual(alerts, [])
        warn.assert_not_called()


# ---------------------------------------------------------------------------
# None metrics — no exceptions when a metric could not be collected
# ---------------------------------------------------------------------------

class TestNoneMetrics(unittest.TestCase):

    def test_cpu_none_does_not_raise(self):
        """check_alerts does not raise when cpu=None; no CPU alert appended."""
        warn = MagicMock()
        system = _make_system_no_battery()
        system.cpu = None
        result = check_alerts(system, log_warn=warn)
        self.assertIsInstance(result, list)
        self.assertTrue(all("CPU" not in a for a in result))

    def test_ram_none_does_not_raise(self):
        """check_alerts does not raise when ram=None; no RAM alert appended."""
        warn = MagicMock()
        system = _make_system_no_battery()
        system.ram = None
        result = check_alerts(system, log_warn=warn)
        self.assertIsInstance(result, list)
        self.assertTrue(all("RAM" not in a for a in result))

    def test_disk_none_does_not_raise(self):
        """check_alerts does not raise when disk=None; no disk alert appended."""
        warn = MagicMock()
        system = _make_system_no_battery()
        system.disk = None
        result = check_alerts(system, log_warn=warn)
        self.assertIsInstance(result, list)
        self.assertTrue(all("Disk" not in a for a in result))


if __name__ == "__main__":
    unittest.main()
