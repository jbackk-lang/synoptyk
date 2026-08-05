# data/cache.py
import sqlite3
import pandas as pd
from datetime import datetime

class WeatherCache:
    def __init__(self, db_path="weather_cache.db"):
        self.conn = sqlite3.connect(db_path)
        self._init_db()
    
    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS hourly (
                datetime TEXT PRIMARY KEY,
                temp REAL,
                pressure REAL,
                humidity REAL,
                wind_speed REAL,
                wind_dir REAL,
                precip REAL,
                source TEXT,
                fetched_at TEXT
            )
        """)
        self.conn.commit()
    
    def save(self, df: pd.DataFrame, source="open-meteo"):
        df["fetched_at"] = datetime.now().isoformat()
        df["source"] = source
        df.to_sql("hourly", self.conn, if_exists="append", index=False)
    
    def load(self, start_date: str, end_date: str) -> pd.DataFrame:
        query = f"""
            SELECT * FROM hourly
            WHERE datetime BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY datetime
        """
        return pd.read_sql_query(query, self.conn)
    
    def close(self):
        self.conn.close()
