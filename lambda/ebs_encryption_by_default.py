import logging
from typing import List
from common.get_session import get_member_session
from constants import REGION_LIST

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def enable_ebs_encryption_by_default(member_session,regions: List[str]) -> None:
    for region_name in regions:
        ec2 = member_session.client("ec2", region_name=region_name)
        try: 
            ec2.enable_ebs_encryption_by_default()
            logger.info(f"Succeeded to enable ebs_encryption by default@{region_name}")
        except Exception as e:
            logger.info(f"Failed to enable ebs_encryption by default@{region_name}")
            logger.error(e)

def is_ebs_encryption_by_default(member_session,regions: List[str]) -> bool:
    check_regions = {}
    for region_name in regions:
        ec2 = member_session.client("ec2", region_name=region_name)
        try:
            res = ec2.get_ebs_encryption_by_default()
            check_regions[region_name] = res["EbsEncryptionByDefault"]
        except Exception as e:
            logger.error(f"{e}:{region_name}")
            check_regions[region_name] = False
    return all(check_regions.values())

def lambda_handler(event, context):

    member_account_id=event["detail"]["serviceEventDetails"]["createManagedAccountStatus"]["account"]["accountId"]
    # Get Client
    member_session = get_member_session(member_account_id)
    
    #EBSデフォルト暗号化の有効化
    enable_ebs_encryption_by_default(member_session,REGION_LIST)

    is_resources = {
        "ebs_encryption_by_default": False,
    }
    is_resources["ebs_encryption_by_default"] = is_ebs_encryption_by_default(member_session,REGION_LIST)

    if not all(is_resources.values()):
        logger.error("Failed to enable ebs_encryption by default")
        logger.error(
            f"is_resources: {is_resources}"
        )
        raise Exception('Fail to check resource')

    logger.info("Completed to enable ebs_encryption by default")
    logger.info(
        f"is_resources: {is_resources}"
    )
    return {
        "is_resources": is_resources
    }