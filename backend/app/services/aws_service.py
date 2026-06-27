import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import HTTPException
from app.models.aws_token import AWSToken


def _ec2_client(token: AWSToken):
    try:
        return boto3.client(
            "ec2",
            aws_access_key_id=token.access_key_id,
            aws_secret_access_key=token.secret_access_key,
            region_name=token.region,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar na AWS: {str(e)}")


def list_instances(token: AWSToken) -> list[dict]:
    client = _ec2_client(token)
    try:
        response = client.describe_instances()
        instances = []
        for reservation in response["Reservations"]:
            for inst in reservation["Instances"]:
                name = next(
                    (tag["Value"] for tag in inst.get("Tags", []) if tag["Key"] == "Name"),
                    "sem-nome",
                )
                instances.append({
                    "instance_id": inst["InstanceId"],
                    "name": name,
                    "state": inst["State"]["Name"],
                    "instance_type": inst["InstanceType"],
                    "public_ip": inst.get("PublicIpAddress"),
                    "launch_time": str(inst.get("LaunchTime")),
                })
        return instances
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def create_instance(token: AWSToken, instance_type: str, ami_id: str, name: str) -> dict:
    client = _ec2_client(token)
    try:
        response = client.run_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": [{"Key": "Name", "Value": name}],
            }],
        )
        inst = response["Instances"][0]
        return {
            "instance_id": inst["InstanceId"],
            "state": inst["State"]["Name"],
            "instance_type": inst["InstanceType"],
        }
    except (ClientError, NoCredentialsError) as e:
        raise HTTPException(status_code=400, detail=str(e))


def stop_instance(token: AWSToken, instance_id: str) -> dict:
    client = _ec2_client(token)
    try:
        response = client.stop_instances(InstanceIds=[instance_id])
        state = response["StoppingInstances"][0]["CurrentState"]["Name"]
        return {"instance_id": instance_id, "state": state}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def start_instance(token: AWSToken, instance_id: str) -> dict:
    client = _ec2_client(token)
    try:
        response = client.start_instances(InstanceIds=[instance_id])
        state = response["StartingInstances"][0]["CurrentState"]["Name"]
        return {"instance_id": instance_id, "state": state}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def terminate_instance(token: AWSToken, instance_id: str) -> dict:
    client = _ec2_client(token)
    try:
        response = client.terminate_instances(InstanceIds=[instance_id])
        state = response["TerminatingInstances"][0]["CurrentState"]["Name"]
        return {"instance_id": instance_id, "state": state}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])
