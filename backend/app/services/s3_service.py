import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from app.models.aws_token import AWSToken


def _s3_client(token: AWSToken):
    try:
        return boto3.client(
            "s3",
            aws_access_key_id=token.access_key_id,
            aws_secret_access_key=token.secret_access_key,
            aws_session_token=token.session_token,
            region_name=token.region,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar no S3: {str(e)}")


def list_buckets(token: AWSToken) -> list[dict]:
    client = _s3_client(token)
    try:
        response = client.list_buckets()
        return [
            {"name": b["Name"], "creation_date": str(b["CreationDate"])}
            for b in response.get("Buckets", [])
        ]
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def create_bucket(token: AWSToken, bucket_name: str) -> dict:
    client = _s3_client(token)
    try:
        kwargs = {"Bucket": bucket_name}
        if token.region != "us-east-1":
            kwargs["CreateBucketConfiguration"] = {"LocationConstraint": token.region}
        client.create_bucket(**kwargs)
        return {"bucket_name": bucket_name, "region": token.region}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def delete_bucket(token: AWSToken, bucket_name: str) -> None:
    client = _s3_client(token)
    try:
        client.delete_bucket(Bucket=bucket_name)
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def list_objects(token: AWSToken, bucket_name: str, prefix: str = "") -> list[dict]:
    client = _s3_client(token)
    try:
        response = client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        return [
            {
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": str(obj["LastModified"]),
            }
            for obj in response.get("Contents", [])
        ]
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def put_object(token: AWSToken, bucket_name: str, key: str, content: str, content_type: str) -> dict:
    client = _s3_client(token)
    try:
        response = client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=content.encode("utf-8"),
            ContentType=content_type,
        )
        return {"key": key, "etag": response.get("ETag", "").strip('"')}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def delete_object(token: AWSToken, bucket_name: str, key: str) -> None:
    client = _s3_client(token)
    try:
        client.delete_object(Bucket=bucket_name, Key=key)
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])
