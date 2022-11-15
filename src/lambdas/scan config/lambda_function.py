import os
import boto3
import botocore
import logging

def lambda_handler(event, context):
    sts = boto3.client("sts")
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.info(f"event: {event}")
    aws_service = "config"
    enabled_services = "enabledServices"
    account_num = sts.get_caller_identity()["Account"]
    
    role_arn = f"arn:aws:iam::{account_num}:role/config_lambda"
    sts_auth = sts.assume_role(RoleArn=role_arn, RoleSessionName="acquired_account_role")
    credentials = sts_auth["Credentials"]

        # ----------------------------- #
        # Place all service code below
        # ----------------------------- #

        # Section for boto3 connection with aws service
    sts_client = boto3.client(aws_service,
                                  region_name='us-east-2', 
                                  aws_access_key_id=credentials["AccessKeyId"],
                                  aws_secret_access_key=credentials["SecretAccessKey"],
                                  aws_session_token=credentials["SessionToken"], )
     # ----------------------------- #
        # Place all service code below
        # ----------------------------- #

      
        # Section for the "get" or "describe" boto3 code for AWS service                        
    response = sts_client.describe_delivery_channels(
        DeliveryChannelNames=[
]
)
    if len(response["DeliveryChannels"]) > 0:
       for cong in response["DeliveryChannels"]:
           conf= {'s3BucketName': cong['s3BucketName'],}
       
    else:
        logger.info(f"config is disabled. Account Num: account_num")
        response = {
                "enabledServices": enabled_services,
                "accountData": 'account_data',
                "scanData": {
                    "service": aws_service,
                    "status": "disabled"
                }
            }
        print(f"RESPONSE: {response}")
        return response

         #Get detailed info for config using recorder status
    response = sts_client.describe_configuration_recorder_status(
                   ConfigurationRecorderNames=[])
    if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
       if len(response["ConfigurationRecordersStatus"]) > 0:
          for con in response["ConfigurationRecordersStatus"]:
                    
              config = {
                            "name": con["name"],
                            "recording": con["recording"],
                            's3BucketName': cong['s3BucketName'],
                          }  
       
              status = "enabled" if con["recording"]== True else "disabled" 
           
          res= {
                
                "scanData": {
                    "service": aws_service,
                    's3BucketName':cong['s3BucketName'],
                    "status": status
                }}
          return ( res)      
       else:
           logger.info(f"config is disabled. Account Num: account_num")
           response = {
                "enabledServices": enabled_services,
                "accountData": 'account_data',
                "scanData": {
                    "service": aws_service,
                    "status": "disabled"
                }
            }
           print(f"RESPONSE: {response}")
           return response

    else:
        logger.info(f"config is disabled. Account Num: account_num")
        response = {
                "enabledServices": enabled_services,
                "accountData": 'account_data',
                "scanData": {
                    "service": aws_service,
                    "status": "disabled"
                }
            }
        print(f"RESPONSE: {response}")
        return response