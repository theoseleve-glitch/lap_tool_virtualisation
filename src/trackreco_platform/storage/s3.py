import boto3

from trackreco_platform.config import settings


class S3Storage:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )

    def put_bytes(self, key: str, payload: bytes, content_type: str = "application/octet-stream") -> str:
        self.client.put_object(Bucket=settings.s3_bucket, Key=key, Body=payload, ContentType=content_type)
        return f"s3://{settings.s3_bucket}/{key}"
