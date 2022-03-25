import logging
from time import sleep
from common.get_session import get_member_session

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def put_public_access_block(member_session,account_id: str) -> None:
    try:
        s3 = member_session.client("s3control")
        s3.put_public_access_block(
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            },
            AccountId = account_id
        )
        logger.info(f'Succeeded to put s3 bucket public_access_block: {account_id}')
    except Exception as e:
        logger.info(f'Failed to put s3 bucket public_access_block: {account_id}')
        logger.error(e)

def is_public_access_block(member_session,account_id: str) -> bool:
    try:
        s3 = member_session.client("s3control")
        res = s3.get_public_access_block(
            AccountId = account_id,
        )
        return all(res["PublicAccessBlockConfiguration"].values())
    except Exception as e:
        logger.error(e)
        return False

def lambda_handler(event, context):
    
    member_account_id=event["detail"]["serviceEventDetails"]["createManagedAccountStatus"]["account"]["accountId"]
    # Get Client
    member_session = get_member_session(member_account_id)

    #アカウントレベルのS3のBPA有効化
    put_public_access_block(member_session,member_account_id)

    # 有効化直後だとgetできない場合があるため5秒待機
    sleep(5)

    is_resources = {
        "s3_account_level_bpa_enabled": False,
    }
    is_resources["s3_account_level_bpa_enabled"] = is_public_access_block(member_session,member_account_id)

    # is_resourcesにFalseがないか確認
    if not all(is_resources.values()):
        logger.error("Failed to enable s3 account level public_access_block")
        logger.error(
            f"is_resources: {is_resources}"
        )
        raise Exception('Fail to check resource')

    logger.info("Completed to enable s3 account level public_access_block")
    logger.info(
        f"is_resources: {is_resources}"
    )
    return {
        "is_resources": is_resources
    }