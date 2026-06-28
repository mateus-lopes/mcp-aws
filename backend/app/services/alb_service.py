import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from app.models.aws_token import AWSToken


def _elb_client(token: AWSToken):
    try:
        return boto3.client(
            "elbv2",
            aws_access_key_id=token.access_key_id,
            aws_secret_access_key=token.secret_access_key,
            aws_session_token=token.session_token,
            region_name=token.region,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar no ELB: {str(e)}")


def list_load_balancers(token: AWSToken) -> list[dict]:
    client = _elb_client(token)
    try:
        response = client.describe_load_balancers()
        result = []
        for lb in response["LoadBalancers"]:
            result.append({
                "arn": lb["LoadBalancerArn"],
                "name": lb["LoadBalancerName"],
                "dns_name": lb["DNSName"],
                "state": lb["State"]["Code"],
                "type": lb["Type"],
                "scheme": lb["Scheme"],
                "vpc_id": lb.get("VpcId"),
                "created_at": str(lb.get("CreatedTime", "")),
            })
        return result
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def list_listeners(token: AWSToken, load_balancer_arn: str) -> list[dict]:
    client = _elb_client(token)
    try:
        response = client.describe_listeners(LoadBalancerArn=load_balancer_arn)
        result = []
        for l in response["Listeners"]:
            result.append({
                "arn": l["ListenerArn"],
                "port": l.get("Port"),
                "protocol": l.get("Protocol"),
                "default_actions": [
                    {"type": a["Type"], "target_group_arn": a.get("TargetGroupArn")}
                    for a in l.get("DefaultActions", [])
                ],
            })
        return result
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def list_target_groups(token: AWSToken, load_balancer_arn: str | None = None) -> list[dict]:
    client = _elb_client(token)
    try:
        kwargs = {}
        if load_balancer_arn:
            kwargs["LoadBalancerArn"] = load_balancer_arn
        response = client.describe_target_groups(**kwargs)
        result = []
        for tg in response["TargetGroups"]:
            result.append({
                "arn": tg["TargetGroupArn"],
                "name": tg["TargetGroupName"],
                "protocol": tg.get("Protocol"),
                "port": tg.get("Port"),
                "vpc_id": tg.get("VpcId"),
                "target_type": tg.get("TargetType"),
                "health_check_path": tg.get("HealthCheckPath"),
            })
        return result
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def describe_target_health(token: AWSToken, target_group_arn: str) -> list[dict]:
    client = _elb_client(token)
    try:
        response = client.describe_target_health(TargetGroupArn=target_group_arn)
        return [
            {
                "target_id": d["Target"]["Id"],
                "port": d["Target"].get("Port"),
                "health_state": d["TargetHealth"]["State"],
                "reason": d["TargetHealth"].get("Reason"),
                "description": d["TargetHealth"].get("Description"),
            }
            for d in response["TargetHealthDescriptions"]
        ]
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def register_target(token: AWSToken, target_group_arn: str, target_id: str, port: int | None = None) -> dict:
    client = _elb_client(token)
    try:
        target = {"Id": target_id}
        if port:
            target["Port"] = port
        client.register_targets(TargetGroupArn=target_group_arn, Targets=[target])
        return {"registered": target_id, "target_group_arn": target_group_arn}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])


def deregister_target(token: AWSToken, target_group_arn: str, target_id: str) -> dict:
    client = _elb_client(token)
    try:
        client.deregister_targets(TargetGroupArn=target_group_arn, Targets=[{"Id": target_id}])
        return {"deregistered": target_id, "target_group_arn": target_group_arn}
    except ClientError as e:
        raise HTTPException(status_code=400, detail=e.response["Error"]["Message"])
