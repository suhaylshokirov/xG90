import duckdb
import pandas as pd
import s3fs
from pathlib import Path
from settings import config

class TacticalModel:
    def __init__(self):
        self.con = duckdb.connect(database=':memory:')
        self.fs = s3fs.S3FileSystem(
            key=config.AWS_ACCESS_KEY_ID,
            secret=config.AWS_SECRET_ACCESS_KEY
        )

    def compute_fingerprints(self, competition_id: int, season_id: int):
        print(f"Computing tactical fingerprints for season {season_id}...")
        
        # 1. Load Silver Events
        silver_events_path = f"s3://{config.S3_BUCKET_NAME}/{config.SILVER_PREFIX}/events/events.parquet"
        with self.fs.open(silver_events_path) as f:
            events_df = pd.read_parquet(f)
        self.con.register("raw_events", events_df)
        
        # 2. Load Silver Carries
        silver_carries_path = f"s3://{config.S3_BUCKET_NAME}/{config.SILVER_PREFIX}/carries/carries.parquet"
        with self.fs.open(silver_carries_path) as f:
            carries_df = pd.read_parquet(f)
        self.con.register("raw_carries", carries_df)
        
        # 2. Execute Gold SQL
        sql = Path("sql/gold_fingerprints.sql").read_text()
        gold_df = self.con.execute(sql).df()
        
        # Add metadata
        gold_df["competition_id"] = competition_id
        gold_df["season_id"] = season_id
        
        return gold_df
