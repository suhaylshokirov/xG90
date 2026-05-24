import duckdb
import os
from pathlib import Path
from settings import config

class SilverTransformer:
    def __init__(self):
        self.con = duckdb.connect(database=':memory:')
        self._setup_duckdb()

    def _setup_duckdb(self):
        self.con.execute("INSTALL httpfs;")
        self.con.execute("LOAD httpfs;")
        self.con.execute(f"SET s3_region='{config.AWS_REGION}';")
        self.con.execute(f"SET s3_access_key_id='{config.AWS_ACCESS_KEY_ID}';")
        self.con.execute(f"SET s3_secret_access_key='{config.AWS_SECRET_ACCESS_KEY}';")

    def transform_table(self, sql_file: str, bronze_path: str, silver_key: str):
        print(f"Transforming {silver_key}...")
        
        # Read SQL file
        sql = Path(f"sql/{sql_file}").read_text()
        
        # Use Pandas to read from S3 (bypassing DuckDB S3 read issue)
        # We need to use glob to handle the wildcards for pandas/pyarrow
        import s3fs
        fs = s3fs.S3FileSystem(
            key=config.AWS_ACCESS_KEY_ID,
            secret=config.AWS_SECRET_ACCESS_KEY
        )
        
        # Strip 's3://bucket/' from path for s3fs
        bucket_prefix = f"s3://{config.S3_BUCKET_NAME}/"
        path_for_fs = bronze_path.replace(bucket_prefix, "")
        files = fs.glob(f"{config.S3_BUCKET_NAME}/{path_for_fs}")
        
        if not files:
            print(f"Warning: No files found for {bronze_path}")
            return
            
        import pandas as pd
        # Read files into a single dataframe
        dfs = []
        for f_path in files:
            # Open file object directly to avoid pyarrow.dataset issues with S3 URLs
            with fs.open(f"s3://{f_path}") as f:
                df_part = pd.read_parquet(f, engine="pyarrow")
            
            # Ensure match_id is int64
            if "match_id" in df_part.columns:
                df_part["match_id"] = df_part["match_id"].astype("int64")
            
            dfs.append(df_part)
            
        raw_df = pd.concat(dfs, ignore_index=True)

        # Register raw_df in DuckDB
        self.con.register("raw_data", raw_df)
        
        # Replace read_parquet(?) with the registered table name
        sql = sql.replace("read_parquet(?)", "raw_data")
        
        # Execute transformation
        df = self.con.execute(sql).df()
        
        if df.empty:
            print(f"Warning: No data produced for {silver_key}")
            return

        # Write back to S3 as Parquet
        output_path = f"s3://{config.S3_BUCKET_NAME}/{silver_key}"
        self.con.execute(f"COPY df TO '{output_path}' (FORMAT PARQUET);")
        print(f"Successfully wrote: {output_path} (Rows: {len(df)})")

    def run_all_transforms(self, competition_id: int, season_id: int):
        # Paths for La Liga 2015/16
        base_bronze = f"s3://{config.S3_BUCKET_NAME}/bronze"
        
        # 1. Events (Global or Partitioned)
        # For simplicity in this demo, we can query across all matches in the season
        events_bronze = f"{base_bronze}/events/competition_id={competition_id}/season_id={season_id}/*/*.parquet"
        self.transform_table("silver_events.sql", events_bronze, f"{config.SILVER_PREFIX}/events/events.parquet")
        
        # 2. Shots (Extracted from Events)
        self.transform_table("silver_shots.sql", events_bronze, f"{config.SILVER_PREFIX}/shots/shots.parquet")
        
        # 3. Pressures (Extracted from Events)
        self.transform_table("silver_pressures.sql", events_bronze, f"{config.SILVER_PREFIX}/pressures/pressures.parquet")
        
        # 4. Carries (Extracted from Events)
        self.transform_table("silver_carries.sql", events_bronze, f"{config.SILVER_PREFIX}/carries/carries.parquet")
        
        # 5. Lineups
        lineups_bronze = f"{base_bronze}/lineups/*/*.parquet"
        self.transform_table("silver_lineups.sql", lineups_bronze, f"{config.SILVER_PREFIX}/lineups/lineups.parquet")

if __name__ == "__main__":
    transformer = SilverTransformer()
    # Transform La Liga 2015/16 (Competition 11, Season 27)
    transformer.run_all_transforms(competition_id=11, season_id=27)
