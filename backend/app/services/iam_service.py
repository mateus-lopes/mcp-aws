import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from app.models.aws_token import AWSToken


def _iam_client(token: AWSToken):
    try:
        return boto3.client(
            "iam",
            aws_access_key_id=token.access_key_id,
            aws_secret_access_key=token.secret_access_key,
            aws_session_token=token.session_token,
            region_name=token.region,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar no IAM: {str(e)}")


def _sts_client(token: AWSToken):
    try:
        return boto3.client(
            "sts",
            aws_access_key_id=token.access_key_id,
            aws_secret_access_key=token.secret_access_key,
            aws_session_token=token.session_token,
            region_name=token.region,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar no STS: {str(e)}")


def whoami(token: AWSToken) -> dict:
    client = _sts_client(token)
    try:
        response = client.get_caller_identity()
        return {
            "account_id": response["Account"],
            "user_id": response["UserId"],
            "arn": response["Arn"],
        }
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def list_users(token: AWSToken) -> list[dict]:
    client = _iam_client(token)
    try:
        response = client.list_users()
        return [
            {
                "username": u["UserName"],
                "user_id": u["UserId"],
                "arn": u["Arn"],
                "created_at": str(u["CreateDate"]),
                "last_used": str(u.get("PasswordLastUsed", "")),
            }
            for u in response["Users"]
        ]
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def list_roles(token: AWSToken) -> list[dict]:
    client = _iam_client(token)
    try:
        response = client.list_roles()
        return [
            {
                "role_name": r["RoleName"],
                "role_id": r["RoleId"],
                "arn": r["Arn"],
                "description": r.get("Description", ""),
                "created_at": str(r["CreateDate"]),
            }
            for r in response["Roles"]
        ]
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def list_policies(token: AWSToken, scope: str = "Local") -> list[dict]:
    client = _iam_client(token)
    try:
        response = client.list_policies(Scope=scope)
        return [
            {
                "policy_name": p["PolicyName"],
                "policy_id": p["PolicyId"],
                "arn": p["Arn"],
                "description": p.get("Description", ""),
                "attachment_count": p.get("AttachmentCount", 0),
                "created_at": str(p["CreateDate"]),
            }
            for p in response["Policies"]
        ]
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def list_groups(token: AWSToken) -> list[dict]:
    client = _iam_client(token)
    try:
        response = client.list_groups()
        return [
            {
                "group_name": g["GroupName"],
                "group_id": g["GroupId"],
                "arn": g["Arn"],
                "created_at": str(g["CreateDate"]),
            }
            for g in response["Groups"]
        ]
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def list_access_keys(token: AWSToken, username: str) -> list[dict]:
    client = _iam_client(token)
    try:
        response = client.list_access_keys(UserName=username)
        return [
            {
                "access_key_id": k["AccessKeyId"],
                "username": k["UserName"],
                "status": k["Status"],
                "created_at": str(k["CreateDate"]),
            }
            for k in response["AccessKeyMetadata"]
        ]
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def create_access_key(token: AWSToken, username: str) -> dict:
    client = _iam_client(token)
    try:
        response = client.create_access_key(UserName=username)
        k = response["AccessKey"]
        return {
            "access_key_id": k["AccessKeyId"],
            "secret_access_key": k["SecretAccessKey"],
            "username": k["UserName"],
            "status": k["Status"],
        }
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def delete_access_key(token: AWSToken, username: str, access_key_id: str) -> dict:
    client = _iam_client(token)
    try:
        client.delete_access_key(UserName=username, AccessKeyId=access_key_id)
        return {"deleted": access_key_id, "username": username}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])
