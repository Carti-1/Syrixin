from storage.database import Database


class MetricsHistoryService:
    def __init__(self, path="syrixin.db"):
        self.database = Database(path)

    def save_snapshot(self, system):
        self.database.save(system)

    def get_recent(self, limit=10):
        return self.database.get_recent(limit)

    def close(self):
        self.database.close()