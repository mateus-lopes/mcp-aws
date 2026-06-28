import boto3
from botocore.exceptions import ClientError
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


def list_vpcs(token: AWSToken) -> list[dict]:
    client = _ec2_client(token)
    try:
        response = client.describe_vpcs()
        result = []
        for vpc in response["Vpcs"]:
            name = next((t["Value"] for t in vpc.get("Tags", []) if t["Key"] == "Name"), None)
            result.append({
                "vpc_id": vpc["VpcId"],
                "name": name,
                "cidr_block": vpc["CidrBlock"],
                "state": vpc["State"],
                "is_default": vpc.get("IsDefault", False),
            })
        return result
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def list_subnets(token: AWSToken, vpc_id: str | None = None) -> list[dict]:
    client = _ec2_client(token)
    try:
        kwargs = {}
        if vpc_id:
            kwargs["Filters"] = [{"Name": "vpc-id", "Values": [vpc_id]}]
        response = client.describe_subnets(**kwargs)
        result = []
        for s in response["Subnets"]:
            name = next((t["Value"] for t in s.get("Tags", []) if t["Key"] == "Name"), None)
            result.append({
                "subnet_id": s["SubnetId"],
                "name": name,
                "vpc_id": s["VpcId"],
                "cidr_block": s["CidrBlock"],
                "availability_zone": s["AvailabilityZone"],
                "available_ips": s["AvailableIpAddressCount"],
                "public": s.get("MapPublicIpOnLaunch", False),
            })
        return result
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def list_security_groups(token: AWSToken, vpc_id: str | None = None) -> list[dict]:
    client = _ec2_client(token)
    try:
        kwargs = {}
        if vpc_id:
            kwargs["Filters"] = [{"Name": "vpc-id", "Values": [vpc_id]}]
        response = client.describe_security_groups(**kwargs)
        result = []
        for sg in response["SecurityGroups"]:
            result.append({
                "group_id": sg["GroupId"],
                "name": sg["GroupName"],
                "description": sg["Description"],
                "vpc_id": sg.get("VpcId"),
                "inbound_rules": len(sg.get("IpPermissions", [])),
                "outbound_rules": len(sg.get("IpPermissionsEgress", [])),
            })
        return result
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def list_internet_gateways(token: AWSToken, vpc_id: str | None = None) -> list[dict]:
    client = _ec2_client(token)
    try:
        kwargs = {}
        if vpc_id:
            kwargs["Filters"] = [{"Name": "attachment.vpc-id", "Values": [vpc_id]}]
        response = client.describe_internet_gateways(**kwargs)
        result = []
        for igw in response["InternetGateways"]:
            name = next((t["Value"] for t in igw.get("Tags", []) if t["Key"] == "Name"), None)
            attachments = [a["VpcId"] for a in igw.get("Attachments", []) if a["State"] == "available"]
            result.append({
                "igw_id": igw["InternetGatewayId"],
                "name": name,
                "attached_vpcs": attachments,
            })
        return result
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def list_route_tables(token: AWSToken, vpc_id: str | None = None) -> list[dict]:
    client = _ec2_client(token)
    try:
        kwargs = {}
        if vpc_id:
            kwargs["Filters"] = [{"Name": "vpc-id", "Values": [vpc_id]}]
        response = client.describe_route_tables(**kwargs)
        result = []
        for rt in response["RouteTables"]:
            name = next((t["Value"] for t in rt.get("Tags", []) if t["Key"] == "Name"), None)
            result.append({
                "route_table_id": rt["RouteTableId"],
                "name": name,
                "vpc_id": rt["VpcId"],
                "routes": len(rt.get("Routes", [])),
                "associated_subnets": [
                    a["SubnetId"] for a in rt.get("Associations", []) if a.get("SubnetId")
                ],
            })
        return result
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])
