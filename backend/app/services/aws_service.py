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
            aws_session_token=token.session_token,
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


def list_images(token: AWSToken, os: str = "amazon-linux-2023", architecture: str = "x86_64", limit: int = 5) -> list[dict]:
    client = _ec2_client(token)
    image_filters = _image_filters(os, architecture)
    try:
        response = client.describe_images(
            Owners=image_filters["owners"],
            Filters=[
                {"Name": "name", "Values": [image_filters["name"]]},
                {"Name": "state", "Values": ["available"]},
                {"Name": "architecture", "Values": [architecture]},
                {"Name": "virtualization-type", "Values": ["hvm"]},
                {"Name": "root-device-type", "Values": ["ebs"]},
            ],
        )
        images = sorted(response.get("Images", []), key=lambda image: image.get("CreationDate", ""), reverse=True)
        return [
            {
                "ami_id": image["ImageId"],
                "name": image.get("Name"),
                "description": image.get("Description"),
                "architecture": image.get("Architecture"),
                "creation_date": image.get("CreationDate"),
                "owner_id": image.get("OwnerId"),
                "region": token.region,
            }
            for image in images[:max(1, min(limit, 20))]
        ]
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def _image_filters(os: str, architecture: str) -> dict:
    normalized_os = os.lower()
    if normalized_os in {"amazon-linux", "amazon-linux-2023", "al2023"}:
        return {"owners": ["amazon"], "name": f"al2023-ami-2023*-{architecture}"}
    if normalized_os in {"ubuntu", "ubuntu-24.04", "ubuntu-noble"}:
        arch = "amd64" if architecture == "x86_64" else architecture
        return {"owners": ["099720109477"], "name": f"ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-{arch}-server-*"}
    if normalized_os in {"ubuntu-22.04", "ubuntu-jammy"}:
        arch = "amd64" if architecture == "x86_64" else architecture
        return {"owners": ["099720109477"], "name": f"ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-{arch}-server-*"}
    raise HTTPException(status_code=400, detail="Sistema operacional inválido. Use amazon-linux-2023, ubuntu-24.04 ou ubuntu-22.04.")


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
