import json
import boto3
import logging


def lambda_handler(event, context):
    
    target_region='us-east-1'
    sts = boto3.client("sts")
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.info(f"event: {event}")
    aws_service = "cloudtrail"
    account_num = sts.get_caller_identity()["Account"]
    
    logger.info("Starting delete of Account's Config")
    logger.info(f"account_num: {account_num}")
    role_arn = f"arn:aws:iam::{account_num}:role/KB_assumed_role" #create an assume role with the name KB_assumed_role
    sts_auth = sts.assume_role(RoleArn=role_arn, RoleSessionName="acquired_account_role")
    credentials = sts_auth["Credentials"]
    sts_client = boto3.client(aws_service,
                              region_name=target_region,
                              aws_access_key_id=credentials["AccessKeyId"],
                              aws_secret_access_key=credentials["SecretAccessKey"],
                              aws_session_token=credentials["SessionToken"], )

    # Section for the "get" or "describe" boto3 code for AWS service
    cloudtrails = sts_client.list_trails()
    logger.info(f"List of CloudTrails: {cloudtrails}")

    status = ""

    if len(cloudtrails) > 0:
        #build list of trail arns to use for describe_trails()
        cloudtrail_arn_list = []
        for cloudtrail in cloudtrails["Trails"]:
            cloudtrail_arn_list.append(cloudtrail["TrailARN"])

        #Get detailed info for trails using list of arns
        response = sts_client.describe_trails(
            trailNameList=cloudtrail_arn_list,
            includeShadowTrails=True
        )
        cloudtrail_list = []
        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            if len(response["trailList"]) > 0:
                for trail in response["trailList"]:
                    cloudtrail = {
                        "name": trail["Name"],
                        "s3BucketName": trail["S3BucketName"],
                        "isMultiRegionTrail": trail["IsMultiRegionTrail"],
                        "homeRegion": trail["HomeRegion"],
                        "isOrganizationTrail": trail["IsOrganizationTrail"]
                    }
                    cloudtrail_list.append(cloudtrail)
                    get_trail_status = sts_client.get_trail_status(
                        Name=trail["TrailARN"])
                    status = "enabled" if get_trail_status['IsLogging'] == True else "disabled"

                    res = {
                            "accountData": account_num,
                            "scanData": {
                                "service": aws_service,
                                "cloudTrailList": cloudtrail_list,
                                "status": status
                            }
                    }
                    return res
        else:
            error_message = "CloudTrail detail fetch failed!"
            logger.error(error_message)
            raise Exception(error_message)

      
    else:
        logger.info(f"CloudTrail is disabled. Account Num: {account_num}")
        status = "disabled"

    
