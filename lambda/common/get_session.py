import boto3
import logging
from boto3.session import Session

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_member_session(target_account_id):
    logger.info('[START] get_member_session')
    sts_connection = boto3.client('sts')
    try:
        # Assume Role
        role_arn = "arn:aws:iam::%s:role/AWSControlTowerExecution" % target_account_id
        role_session_name = "CROSS_ACCOUNT_ACCESS_FROM_CT_MANAGEMENT_ACCOUNT"
        logger.info("- RoleArn=%s" % role_arn)
        logger.info("- RoleSessionName=%s" % role_session_name)
        target = sts_connection.assume_role(
            RoleArn=role_arn,
            RoleSessionName=role_session_name,
        )
    except Exception as e:
        logger.error(e)
        exit()
    else:
        member_session = Session(
            aws_access_key_id=target['Credentials']['AccessKeyId'],
            aws_secret_access_key=target['Credentials']['SecretAccessKey'],
            aws_session_token=target['Credentials']['SessionToken']
        )
        logger.info('[END] get_member_session')
        return member_session
