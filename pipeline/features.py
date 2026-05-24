from models.tactical import TacticalModel
from settings import config
import duckdb

def run_feature_engineering():
    model = TacticalModel()
    
    # Process La Liga 2015/16
    comp_id = 11
    season_id = 27
    
    gold_df = model.compute_fingerprints(comp_id, season_id)
    
    if gold_df.empty:
        print("Error: No features generated.")
        return

    # Write to S3 Gold layer
    con = duckdb.connect(database=':memory:')
    output_path = f"s3://{config.S3_BUCKET_NAME}/{config.GOLD_PREFIX}/team_fingerprints/fingerprints.parquet"
    
    # Configure S3 for DuckDB write
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"SET s3_region='{config.AWS_REGION}';")
    con.execute(f"SET s3_access_key_id='{config.AWS_ACCESS_KEY_ID}';")
    con.execute(f"SET s3_secret_access_key='{config.AWS_SECRET_ACCESS_KEY}';")
    
    con.execute(f"COPY gold_df TO '{output_path}' (FORMAT PARQUET);")
    print(f"Successfully wrote Gold layer: {output_path} (Rows: {len(gold_df)})")

if __name__ == "__main__":
    run_feature_engineering()
