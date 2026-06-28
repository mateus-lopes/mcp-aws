import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from app.models.aws_token import AWSToken


def _rds_client(token: AWSToken):
    try:
        return boto3.client(
            "rds",
            aws_access_key_id=token.access_key_id,
            aws_secret_access_key=token.secret_access_key,
            aws_session_token=token.session_token,
            region_name=token.region,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar no RDS: {str(e)}")


def list_instances(token: AWSToken) -> list[dict]:
    client = _rds_client(token)
    try:
        response = client.describe_db_instances()
        result = []
        for db in response["DBInstances"]:
            endpoint = db.get("Endpoint") or {}
            result.append({
                "db_instance_id": db["DBInstanceIdentifier"],
                "engine": db["Engine"],
                "engine_version": db.get("EngineVersion"),
                "instance_class": db["DBInstanceClass"],
                "status": db["DBInstanceStatus"],
                "endpoint": endpoint.get("Address"),
                "port": endpoint.get("Port"),
                "multi_az": db.get("MultiAZ", False),
                "storage_gb": db.get("AllocatedStorage"),
            })
        return result
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def create_instance(token: AWSToken, db_instance_id: str, engine: str, instance_class: str,
                    master_username: str, master_password: str, storage_gb: int) -> dict:
    client = _rds_client(token)
    try:
        response = client.create_db_instance(
            DBInstanceIdentifier=db_instance_id,
            Engine=engine,
            DBInstanceClass=instance_class,
            MasterUsername=master_username,
            MasterUserPassword=master_password,
            AllocatedStorage=storage_gb,
        )
        db = response["DBInstance"]
        return {
            "db_instance_id": db["DBInstanceIdentifier"],
            "engine": db["Engine"],
            "status": db["DBInstanceStatus"],
        }
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def stop_instance(token: AWSToken, db_instance_id: str) -> dict:
    client = _rds_client(token)
    try:
        response = client.stop_db_instance(DBInstanceIdentifier=db_instance_id)
        db = response["DBInstance"]
        return {"db_instance_id": db["DBInstanceIdentifier"], "status": db["DBInstanceStatus"]}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def start_instance(token: AWSToken, db_instance_id: str) -> dict:
    client = _rds_client(token)
    try:
        response = client.start_db_instance(DBInstanceIdentifier=db_instance_id)
        db = response["DBInstance"]
        return {"db_instance_id": db["DBInstanceIdentifier"], "status": db["DBInstanceStatus"]}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def delete_instance(token: AWSToken, db_instance_id: str, skip_final_snapshot: bool = True) -> dict:
    client = _rds_client(token)
    try:
        kwargs = {
            "DBInstanceIdentifier": db_instance_id,
            "SkipFinalSnapshot": skip_final_snapshot,
        }
        if not skip_final_snapshot:
            kwargs["FinalDBSnapshotIdentifier"] = f"{db_instance_id}-final"
        response = client.delete_db_instance(**kwargs)
        db = response["DBInstance"]
        return {"db_instance_id": db["DBInstanceIdentifier"], "status": db["DBInstanceStatus"]}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def create_snapshot(token: AWSToken, db_instance_id: str, snapshot_id: str) -> dict:
    client = _rds_client(token)
    try:
        response = client.create_db_snapshot(
            DBSnapshotIdentifier=snapshot_id,
            DBInstanceIdentifier=db_instance_id,
        )
        snap = response["DBSnapshot"]
        return {
            "snapshot_id": snap["DBSnapshotIdentifier"],
            "db_instance_id": snap["DBInstanceIdentifier"],
            "status": snap["Status"],
            "created_at": str(snap.get("SnapshotCreateTime", "")),
        }
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def list_snapshots(token: AWSToken, db_instance_id: str | None = None) -> list[dict]:
    client = _rds_client(token)
    try:
        kwargs = {}
        if db_instance_id:
            kwargs["DBInstanceIdentifier"] = db_instance_id
        response = client.describe_db_snapshots(**kwargs)
        return [
            {
                "snapshot_id": s["DBSnapshotIdentifier"],
                "db_instance_id": s["DBInstanceIdentifier"],
                "status": s["Status"],
                "engine": s["Engine"],
                "allocated_storage": s.get("AllocatedStorage"),
                "created_at": str(s.get("SnapshotCreateTime", "")),
            }
            for s in response["DBSnapshots"]
        ]
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])
