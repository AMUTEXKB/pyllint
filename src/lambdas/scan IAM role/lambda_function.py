import os
import boto3
import botocore
import logging
import json

stack_name="amuda"

aws_service = "cloudformation"
target_region="us-east-1"
logger = logging.getLogger()

def lambda_handler(event, context):
    sts = boto3.client("sts")  
    account_num = sts.get_caller_identity()["Account"]
    logger.info(f"Starting scan of new account {account_num}")
    logger.info(f"account_num: {account_num}")
    role_arn = f"arn:aws:iam::{account_num}:role/KB_assumed_role" #create an assume role with the name KB_assumed_role
    sts_auth = sts.assume_role(RoleArn=role_arn, RoleSessionName="acquired_account_role")
    credentials = sts_auth["Credentials"]
    
    
    # ----------------------------- #
    # Place all service code below
    # ----------------------------- #

    # Section for boto3 connection with aws service
    sts_client = boto3.client(aws_service,
                              region_name=target_region,
                              aws_access_key_id=credentials["AccessKeyId"],
                              aws_secret_access_key=credentials["SecretAccessKey"],
                              aws_session_token=credentials["SessionToken"], )
     
    try:
    # TODO: write code...
        response = sts_client.describe_stacks(
        StackName=stack_name
        )
    except botocore.exceptions.ClientError as error:
        status = "disabled"
        logger.info(f" IAM role does not exist. Account Num: {account_num}")
        response = {
            "enabledServices": "enabled_services",
            "accountData": account_num,
            "scanData": {
                "service": aws_service,
                "status": status
            }
        }
        return response