import sqlite3
from datetime import datetime, timezone

class Database:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)

        self.connection.execute("""  
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                cpu REAL,
                ram_total INTEGER,
                ram_pct REAL,
                ram_used INTEGER,
                disk_used INTEGER,
                disk_total INTEGER,
                disk_pct REAL,
                battery_pct REAL,
                power_plugged INTEGER
            )

        
        """)

        self.connection.commit()

        # Add the field to existing databases without deleting their history.
        columns = {
            row[1] for row in self.connection.execute("PRAGMA table_info(metrics)")
        }
        if "cpu_temp" not in columns:
            self.connection.execute("ALTER TABLE metrics ADD COLUMN cpu_temp REAL")
            self.connection.commit()
            columns = {
                row[1] for row in self.connection.execute("PRAGMA table_info(metrics)")
            }
        if "ram_used" not in columns:
            self.connection.execute("ALTER TABLE metrics ADD COLUMN ram_used INTEGER")
            self.connection.commit()
    
    def save(self, system):
        timestamp = datetime.now(timezone.utc).isoformat()

        ram_total = system.ram.total if system.ram is not None else None
        ram_pct = system.ram.percent if system.ram is not None else None
        ram_available = getattr(system.ram, "available", None)
        if ram_total is None:
            ram_used = None
        elif ram_available is not None:
            ram_used = ram_total - ram_available
        elif ram_pct is not None:
            # Compatibility for older/custom metric objects without available.
            ram_used = round(ram_total * ram_pct / 100)
        else:
            ram_used = None

        disk_used = system.disk.used if system.disk is not None else None
        disk_total = system.disk.total if system.disk is not None else None
        disk_pct = system.disk.percent if system.disk is not None else None

        battery_pct = system.battery.percent if system.battery is not None else None
        power_plugged = (
            int(system.battery.power_plugged)
            if system.battery is not None and system.battery.power_plugged is not None
            else None
        )

        self.connection.execute(
            """
            INSERT INTO metrics (
                timestamp, cpu, ram_total, ram_pct,
                disk_used, disk_total, disk_pct,
                battery_pct, power_plugged, cpu_temp, ram_used
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                system.cpu,
                ram_total,
                ram_pct,
                disk_used,
                disk_total,
                disk_pct,
                battery_pct,
                power_plugged,
                system.cpu_temp,
                ram_used,
            ),
        )
        self.connection.commit()

    def close(self):
        self.connection.close()

    def get_recent(self, limit=10):
        if limit < 1:
            raise ValueError("limit must be at least 1")

        rows = self.connection.execute(
            """
            SELECT
                timestamp, cpu, ram_total, ram_pct,
                disk_used, disk_total, disk_pct,
                battery_pct, power_plugged, cpu_temp, ram_used
            FROM metrics
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return rows
