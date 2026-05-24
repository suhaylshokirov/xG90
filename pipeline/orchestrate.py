import argparse
from prefect import flow, task
from pipeline.ingest import StatsBombIngestor
from pipeline.transform import SilverTransformer
from pipeline.features import TacticalModel
from settings import config
import duckdb

@task(retries=2, retry_delay_seconds=30)
def ingest_task(competition_id: int, season_id: int, limit: int = None):
    print(f"--- Starting Ingest Task for Comp {competition_id} Season {season_id} ---")
    ingestor = StatsBombIngestor()
    return ingestor.run_full_ingestion(competition_id, season_id, limit_matches=limit)

@task
def transform_task(ids):
    comp_id, season_id = ids
    print(f"--- Starting Transform Task for Comp {comp_id} Season {season_id} ---")
    transformer = SilverTransformer()
    transformer.run_all_transforms(comp_id, season_id)
    return comp_id, season_id

@task
def features_task(ids):
    comp_id, season_id = ids
    print(f"--- Starting Feature Engineering Task for Comp {comp_id} Season {season_id} ---")
    model = TacticalModel()
    gold_df = model.compute_fingerprints(comp_id, season_id)
    
    # Write to Gold
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"SET s3_region='{config.AWS_REGION}';")
    con.execute(f"SET s3_access_key_id='{config.AWS_ACCESS_KEY_ID}';")
    con.execute(f"SET s3_secret_access_key='{config.AWS_SECRET_ACCESS_KEY}';")
    
    output_path = f"s3://{config.S3_BUCKET_NAME}/{config.GOLD_PREFIX}/team_fingerprints/fingerprints.parquet"
    con.execute(f"COPY gold_df TO '{output_path}' (FORMAT PARQUET);")
    print(f"Successfully wrote Gold layer: {output_path}")

@flow(name="90xG Data Pipeline")
def pipeline_90xg(competition_id: int, season_id: int, limit: int = None):
    ingest_result = ingest_task(competition_id, season_id, limit)
    transform_result = transform_task(ingest_result)
    features_task(transform_result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the 90xG Data Pipeline")
    parser.add_argument("--competition", type=int, required=True, help="StatsBomb Competition ID")
    parser.add_argument("--season", type=int, required=True, help="StatsBomb Season ID")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of matches (for testing)")
    
    args = parser.parse_args()
    
    pipeline_90xg(competition_id=args.competition, season_id=args.season, limit=args.limit)
