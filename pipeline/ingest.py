import io
import pandas as pd
import boto3
from datetime import datetime, timezone
from statsbombpy import sb
from settings import config

class StatsBombIngestor:
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION
        )
        self.bucket = config.S3_BUCKET_NAME
        self.source = "statsbomb_open"

    def _upload_parquet(self, df: pd.DataFrame, key: str):
        """Uploads a DataFrame as a Parquet file to S3."""
        if df.empty:
            print(f"Warning: Attempting to upload empty DataFrame to {key}")
            return

        # Add metadata columns
        df = df.copy()
        df["_ingested_at"] = datetime.now(timezone.utc)
        df["_source"] = self.source

        # Handle problematic columns (e.g., mixed types or lists/dicts that should be strings in Bronze)
        # StatsBomb data often has nested objects or lists in columns
        for col in df.columns:
            if df[col].dtype == "object":
                # Convert list-like or mixed-type columns to string for Bronze layer
                # This ensures we don't lose data while keeping Parquet storage simple
                df[col] = df[col].astype(str)

        # Convert to Parquet in memory
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False, engine="pyarrow")
        buffer.seek(0)

        # Upload to S3
        self.s3.upload_fileobj(buffer, self.bucket, key)
        print(f"Successfully uploaded: s3://{self.bucket}/{key}")

    def ingest_competitions(self):
        print("Ingesting competitions...")
        df = sb.competitions()
        key = f"{config.BRONZE_PREFIX}/competitions/competitions.parquet"
        self._upload_parquet(df, key)

    def ingest_matches(self, competition_id: int, season_id: int):
        print(f"Ingesting matches for competition {competition_id}, season {season_id}...")
        df = sb.matches(competition_id=competition_id, season_id=season_id)
        key = f"{config.BRONZE_PREFIX}/matches/competition_id={competition_id}/season_id={season_id}/matches.parquet"
        self._upload_parquet(df, key)
        return df["match_id"].tolist()

    def ingest_events(self, competition_id: int, season_id: int, match_id: int):
        # Note: statsbombpy.sb.events returns flattened events by default
        df = sb.events(match_id=match_id)
        key = f"{config.BRONZE_PREFIX}/events/competition_id={competition_id}/season_id={season_id}/match_id={match_id}/events.parquet"
        self._upload_parquet(df, key)

    def ingest_lineups(self, match_id: int):
        # sb.lineups returns a dict of dataframes {team_name: df}
        lineups_dict = sb.lineups(match_id=match_id)
        all_lineups = []
        for team_name, df in lineups_dict.items():
            df = df.copy()
            df["team_name"] = team_name
            df["match_id"] = match_id
            all_lineups.append(df)
        
        if all_lineups:
            combined_df = pd.concat(all_lineups, ignore_index=True)
            key = f"{config.BRONZE_PREFIX}/lineups/match_id={match_id}/lineups.parquet"
            self._upload_parquet(combined_df, key)

    def ingest_frames(self, match_id: int):
        """Ingest freeze frames (360 data) if available."""
        try:
            # statsbombpy doesn't have a direct 'frames' method in the high-level API 
            # that is as simple as others, but let's check if we can get it.
            # Usually it's match_frames(match_id) or via events.
            # For simplicity in this step, we'll skip if it's not straightforward 
            # or not available for the specific match.
            pass
        except Exception as e:
            print(f"Skipping frames for match {match_id}: {e}")

    def run_full_ingestion(self, competition_id: int, season_id: int, limit_matches: int = None):
        self.ingest_competitions()
        match_ids = self.ingest_matches(competition_id, season_id)
        
        if limit_matches:
            match_ids = match_ids[:limit_matches]
            print(f"Limiting to first {limit_matches} matches for testing.")

        for mid in match_ids:
            print(f"Processing match {mid}...")
            self.ingest_events(competition_id, season_id, mid)
            self.ingest_lineups(mid)
        
        return competition_id, season_id

if __name__ == "__main__":
    ingestor = StatsBombIngestor()
    # La Liga 2015/16 is competition_id=11, season_id=27
    # Limiting to 5 matches for initial run to verify Step 2
    ingestor.run_full_ingestion(competition_id=11, season_id=27, limit_matches=5)
