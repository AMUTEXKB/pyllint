import os
import boto3
import botocore
import logging
import json
aws_service="custom insight" 
modify_service='securityhub'
account_num="672432851135"
target_region="us-east-1"
logger = logging.getLogger()

def lambda_handler(event, context):
    insight_name="CIRRUSSCAN_INSIGHT_NAME"
    aws_service="custom insight" 
    modify_service='securityhub'
    sts = boto3.client("sts")
    log_level = os.environ.get("log_level", "INFO")
    logger.setLevel(level=log_level)
    logger.info(f"REQUEST: {event}")
    aws_service = "securityhub"
 
    try:
        logger.info(f"Starting scan of new account {account_num}")
        logger.info(f"account_num: {account_num}")
        role_arn = f"arn:aws:iam::{account_num}:role/KB_assumed_role"
        sts_auth = sts.assume_role(RoleArn=role_arn, RoleSessionName="acquired_account_role")
        credentials = sts_auth["Credentials"]
    
        # ----------------------------- #
        # Place all service code below
        # ----------------------------- #
    
        # Section for boto3 connection with aws service
        sts_client = boto3.client(modify_service,
                                  region_name=target_region,
                                  aws_access_key_id=credentials["AccessKeyId"],
                                  aws_secret_access_key=credentials["SecretAccessKey"],
                                  aws_session_token=credentials["SessionToken"], )
        
        #checking for already existing custom insight with same name
        
        response = sts_client.get_insights()
        if  len(response["Insights"]) > 0:
            for insight in response["Insights"]:
                if  insight["Name"] == insight_name:
                    existing_arn= insight["InsightArn"]
                #updating existing custom insight
                    res= {
                                "enabledServices": "enabled_services",
                                "accountData": "account_data",
                                "scanData": {
                                    "service": aws_service,
                                    "status": "enabled"
                                }
                            }
                    return res
                else:
                    res= {
                            "enabledServices": "enabled_services",
                            "accountData": "account_data",
                            "scanData": {
                                "service": aws_service,
                                "status": "disabled"
                            }
                        }
                    return res
                    
        else:
            res= {
                "enabledServices": "enabled_services",
                "accountData": "account_data",
                "scanData": {
                    "service": aws_service,
                    "status": "disabled"
                }
                    }
            return res 
    except botocore.exceptions.ClientError as error:
        logger.error(f"Error: {error}")
        error_message = error.response["Error"]["Message"]
        sns_client = boto3.client("sns")
        sns_client.publish (
            TopicArn = f"arn:aws:sns:us-east-1:{account_num}:KB_Send_Failure_Notification_Topic",
            Message = f"An error has occured during the scanning process of account {account_num}. The error is: {error_message}",
            Subject = f"Error occured in running scan of {aws_service} on account {account_num}."
        )
        raise