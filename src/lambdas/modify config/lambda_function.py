import os
import boto3
import botocore
import logging

logger = logging.getLogger()

def lambda_handler(event, context):
    sts = boto3.client("sts")
    log_level = os.environ.get("log_level", "INFO")
    logger.setLevel(level=log_level)
    logger.info(f"REQUEST: {event}")
    aws_service = "config"
    config_name = "" #input the parameters yourself
    kb_config_arn = ""
    s3_key_Prefix = ""
    delivery_channel = ""

    try:
        account_num = sts.get_caller_identity()["Account"]
        target_region = ""
        kb_central_logging_bucket = ""

        logger.info(f"Starting scan of new account {account_num}")
        logger.info(f"account_num: {account_num}")
        role_arn = f"arn:aws:iam::{account_num}:role/GoDaddy_assumed_role"
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
        # Section for the "get" or "describe" boto3 code for AWS service
             # ----------------------------- #
        # Place all service code below
        # ----------------------------- #

        # Section for boto3 connection with aws service

        create_recorder = sts_client.put_configuration_recorder(
         ConfigurationRecorder={
               "name": config_name,
               "roleARN": kb_config_arn,
               "recordingGroup": {
                   "allSupported": True,
                   "includeGlobalResourceTypes": False,

        }
    })
         # section for creating config delivery channel
        delivery_channel = sts_client.put_delivery_channel(
        DeliveryChannel={
                    "name": delivery_channel,
                    "s3KeyPrefix": s3_key_Prefix,
                    "s3BucketName":kb_central_logging_bucket,

        }
)

         # section for starting config recorder
        response = sts_client.start_configuration_recorder(
        ConfigurationRecorderName=config_name,
)

        response = {
                        "enabledServices": 'enabled_services',
                        "accountData": account_num,
                        "implementationData": {
                            "service": aws_service,
                            "status":'enabled'
                        }
                    }

        return response


    except botocore.exceptions.ClientError as error:
        logger.error(f"Error: {error}")
        error_message = error.response["Error"]["Message"]
        sns_client = boto3.client("sns")
        sns_client.publish (
            TopicArn = "arn:aws:sns:us-east-1:{account_num}:kb_Send_Failure_Notification_Topic",
            Message = f"An error has occured during the scanning process of account {account_num}. The error is: {error_message}",
            Subject = f"Error occured in running scan of {aws_service} on account {account_num}."
        )
        raise
