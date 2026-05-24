import sys
import boto3
# print(f"DEBUG: sys.path: {sys.path}")
from settings import config
# print(f"DEBUG: settings file: {config.__file__ if hasattr(config, '__file__') else 'no __file__'}")

def check_imports():
    print("Checking imports...")
    modules = [
        "statsbombpy", "duckdb", "prefect", "streamlit", 
        "plotly", "mplsoccer", "pyarrow", "boto3", "pandas", "dotenv"
    ]
    all_passed = True
    for module in modules:
        try:
            __import__(module)
            print(f"  [PASS] {module}")
        except ImportError:
            print(f"  [FAIL] {module}")
            all_passed = False
    return all_passed

def check_s3():
    print("Checking S3 connection...")
    try:
        config.validate()
        s3 = boto3.client(
            "s3",
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION
        )
        s3.list_objects_v2(Bucket=config.S3_BUCKET_NAME, MaxKeys=1)
        print(f"  [PASS] Successfully connected to S3 bucket: {config.S3_BUCKET_NAME}")
        return True
    except Exception as e:
        print(f"  [FAIL] S3 connection failed: {e}")
        return False

if __name__ == "__main__":
    imports_ok = check_imports()
    s3_ok = check_s3()
    
    if imports_ok and s3_ok:
        print("\nAll checks passed! System is ready.")
        sys.exit(0)
    else:
        print("\nSome checks failed. Please verify your environment.")
        sys.exit(1)
    print("\nAll checks passed! System is ready.")
        sys.exit(0)
    else:
        print("\nSome checks failed. Please verify your environment.")
        sys.exit(1)
