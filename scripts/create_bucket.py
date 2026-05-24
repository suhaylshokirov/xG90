import boto3
from settings import config

def create_bucket():
    print(f"Attempting to create bucket: {config.S3_BUCKET_NAME} in region: {config.AWS_REGION}")
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION
        )
        if config.AWS_REGION == "us-east-1":
            s3.create_bucket(Bucket=config.S3_BUCKET_NAME)
        else:
            s3.create_bucket(
                Bucket=config.S3_BUCKET_NAME,
                CreateBucketConfiguration={'LocationConstraint': config.AWS_REGION}
            )
        print("Bucket created successfully!")
    except Exception as e:
        print(f"Failed to create bucket: {e}")

if __name__ == "__main__":
    create_bucket()
