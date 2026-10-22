import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace

from models.system_info import SystemInfo
from storage.database import Database

class TestDatabase(unittest.TestCase):
    def test_save_metrics(self):
        db = Database(":memory:")

        system = SystemInfo(
            cpu=42.5,
            ram=SimpleNamespace(
                total=16 * (1024 ** 3),
                percent=50.0,
            ),
            disk=SimpleNamespace(
                used=100 * (1024 ** 3),
                total=500 * (1024 ** 3),
                percent=20.0,
            ),
            battery=SimpleNamespace(
                percent=80.0,
                power_plugged=True,
            ),
            battery_status="Charging",
        )

        try:
            db.save(system)

            row = db.connection.execute(
                """
                SELECT
                    cpu, ram_total, ram_pct,
                    disk_used, disk_total, disk_pct,
                    battery_pct, power_plugged
                FROM metrics
                """
            ).fetchone()
        finally:
            db.close()

        expected = (
            42.5,
            16 * (1024 ** 3),
            50.0,
            100 * (1024 ** 3),
            500 * (1024 ** 3),
            20.0,
            80.0,
            1,
        )
        self.assertEqual(row, expected)


    def test_missing_metrics_are_saved_as_null(self):
        db = Database(":memory:")
        system = SystemInfo(
            cpu=None,
            ram=None,
            disk=None,
            battery=None,
            battery_status=None,
        )

        try:
            db.save(system)

            row = db.connection.execute(
                """
                SELECT
                    cpu, ram_total, ram_pct,
                    disk_used, disk_total, disk_pct,
                    battery_pct, power_plugged
                FROM metrics
                """
            ).fetchone()
        finally:
            db.close()

        self.assertEqual(row, (None, None, None, None, None, None, None, None))

    def test_multiple_saves_create_multiple_rows(self):
        db = Database(":memory:")

        first = SystemInfo(
            cpu=10.0, ram=None, disk=None,
            battery=None, battery_status=None,
        )
        second = SystemInfo(
            cpu=20.0, ram=None, disk=None,
            battery=None, battery_status=None,
        )

        try:
            db.save(first)
            db.save(second)

            rows = db.connection.execute(
                "SELECT cpu FROM metrics ORDER BY id"
            ).fetchall()
        finally:
            db.close()

        self.assertEqual(rows, [(10.0,), (20.0,)])

    def test_timestamp_is_iso_format_in_utc(self):
        db = Database(":memory:")
        system = SystemInfo(
            cpu=10.0,
            ram=None,
            disk=None,
            battery=None,
            battery_status=None,
        )

        try:
            db.save(system)
            timestamp = db.connection.execute(
                "SELECT timestamp FROM metrics"
            ).fetchone()[0]
        finally:
            db.close()

        parsed_timestamp = datetime.fromisoformat(timestamp)

        self.assertIsNotNone(parsed_timestamp.tzinfo)
        self.assertEqual(parsed_timestamp.utcoffset(), timedelta(0))


if __name__ == "__main__":
    unittest.main()
