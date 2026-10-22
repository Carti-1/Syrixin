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
                disk_used INTEGER,
                disk_total INTEGER,
                disk_pct REAL,
                battery_pct REAL,
                power_plugged INTEGER
            )

        
        """)    

        self.connection.commit()
    
    def save(self, system):
        timestamp = datetime.now(timezone.utc).isoformat()

        ram_total = system.ram.total if system.ram is not None else None
        ram_pct = system.ram.percent if system.ram is not None else None

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
                battery_pct, power_plugged
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            ),
        )
        self.connection.commit()

    def close(self):
        self.connection.close()
    