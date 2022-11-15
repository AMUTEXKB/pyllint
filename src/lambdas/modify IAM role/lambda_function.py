import os
import boto3
import botocore
import logging
import json


logger = logging.getLogger()
stack_name="role"
# stack parameters



def lambda_handler(event, context):
    sts = boto3.client("sts") 
    modify_service = "cloudformation"
    target_region="us-east-1"
    account_num = sts.get_caller_identity()["Account"]
    aws_service="iam"

    stack_name="role"
    # stack parameters
    deploy_version="2010-09-09"
    audit_account_role_arns=f"arn:aws:iam::{account_num}:user/<ENTER USERNAME>"
    audit_account_param_buckets=f"arn:aws:s3:::<ENTER BUCKETNAME>"
    audit_account_result_buckets=f"arn:aws:s3:::<ENTER BUCKETNAME>"
    

    client = boto3.client("organizations")
    
    response = client.describe_account(
    AccountId="<ENTER ACQUIRED ACCOUNT ID >"
    )
    email=response['Account']['Email']
     
  
    logger.info(f"Starting modify of new account: {account_num}")
    logger.info(f"account_num: {account_num}")
    role_arn = f"arn:aws:iam::{account_num}:role/KB_assumed_role" #create an assume role with the name KB_assumed_role
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

    logger.info("PRE LAUNCH STACK")
    
    stack_result = launch_stack(
        sts_client,
        stack_name,
        deploy_version,
        audit_account_role_arns,
        audit_account_param_buckets,
        audit_account_result_buckets,
        email
    )

    status = stack_result["status"]

    res = {
            "accountData": "account_data",
            "implementationData": {
                "service": aws_service,
                "status": status
            }
    }
    logger.info(f"RESPONSE: {res}")
    return res

def launch_stack(client,
                stack_name,
                deploy_version,
                audit_account_role_arns,
                audit_account_param_buckets,
                audit_account_result_buckets,
                email):


    try:

    
        logger.info(f"Creating {stack_name}")
        # read entire file as json
        template_file_location="role.json"
        with open(template_file_location, 'r') as content_file:
            content = json.load(content_file)
        
        # convert json to json string
        content = json.dumps(content)   
        client.create_stack(
            StackName=stack_name,
            TemplateBody=content,
            Parameters=[
                {
                    'ParameterKey': 'DeployVersion',
                    'ParameterValue': deploy_version
                },            {
                    'ParameterKey': 'AuditAccountRoleArns',
                    'ParameterValue': audit_account_role_arns
                },            {
                    'ParameterKey': 'AuditAccountParamBuckets',
                    'ParameterValue': audit_account_param_buckets
                },            {
                    'ParameterKey': 'AuditAccountResultsBuckets',
                    'ParameterValue': audit_account_result_buckets
                },            {
                    'ParameterKey': 'SecurityDL',
                    'ParameterValue': email
                }
            ],
            Capabilities=["CAPABILITY_NAMED_IAM"]
        )
        # ----------------------------- #
        # Place all service code below
        # ----------------------------- #
    
        # Section for boto3 connection with aws service
        wait_client = boto3.client("cloudformation") 

        waiter = wait_client.get_waiter('stack_create_complete')
        waiter.wait(
            StackName=stack_name,
            WaiterConfig={
                'Delay': 30,
                'MaxAttempts': 9
            }
)
        res = {
            "status": "successfully deployed",
            "deploy_started": True
        }
        return res

    except botocore.exceptions.ClientError as error:
        logger.error(f"Launch Stack Error: {error}")
        if error.response["Error"]["Code"] == "AlreadyExistsException":
            res = {
                    "status": "enabled",
                    "deploy_started": False
            }
            return res
        raise