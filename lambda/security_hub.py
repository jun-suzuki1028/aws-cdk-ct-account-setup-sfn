import logging
from common.get_session import get_member_session
import time

from typing import List
from constants import (
    SECURITY_HUB_AFSBP_STANDARD_NAME,
    SECURITY_HUB_AFSBP_DISABLE_CONTROL_LIST,
    SECURITY_HUB_CIS_STANDARD_NAME,
    REGION_LIST
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def batch_disable_standards (session,region_name: str,member_account_id) -> None:
    sh = session.client("securityhub", region_name=region_name)
    cis_std_arn = f"arn:aws:securityhub:{region_name}:{member_account_id}:subscription/{SECURITY_HUB_CIS_STANDARD_NAME}"
    sh.batch_disable_standards(StandardsSubscriptionArns=[cis_std_arn])
    logger.info(f"Succeeded to disable securityhub standard {SECURITY_HUB_CIS_STANDARD_NAME}@{region_name}")
    
    
def batch_enable_standards (session,region_name: str) -> None:
    sh = session.client("securityhub", region_name=region_name)
    std_arn = f"arn:aws:securityhub:{region_name}::standards/{SECURITY_HUB_AFSBP_STANDARD_NAME}"
    sh.batch_enable_standards(StandardsSubscriptionRequests= [{'StandardsArn': std_arn}])
    logger.info(f"Succeeded to enable securityhub standard {SECURITY_HUB_AFSBP_STANDARD_NAME}@{region_name}")

def update_standards_control (session,
                              region_name: str,
                              account_id: str,) -> None:
    sh = session.client("securityhub", region_name=region_name)
    is_standard_status=is_get_standard_status(session,region_name,account_id)

    while not is_standard_status:
        logger.info(f"is_standard_status {is_standard_status}")
        logger.info("Waiting for standard enabled...")
        time.sleep(1)
        is_standard_status=is_get_standard_status(session,region_name,account_id)
        
    for control in SECURITY_HUB_AFSBP_DISABLE_CONTROL_LIST:
        ctl_arn = f"arn:aws:securityhub:{region_name}:{account_id}:control/{SECURITY_HUB_AFSBP_STANDARD_NAME}/{control}"
        sh.update_standards_control(StandardsControlArn=ctl_arn,
                                    ControlStatus='DISABLED',
                                    DisabledReason='init disable control')
        logger.info(f"Succeeded to disable securityhub standards control {control}@{region_name}")   
        
def is_get_standard_status(session,region_name: str,account_id: str):
    sh = session.client("securityhub", region_name=region_name)
    std_arn = f"arn:aws:securityhub:{region_name}:{account_id}:standards/{SECURITY_HUB_AFSBP_STANDARD_NAME}"
    res = sh.get_enabled_standards(StandardsSubscriptionArns=[std_arn])
    standard_status = res["StandardsSubscriptions"][0]["StandardsStatus"]
    if standard_status in ('INCOMPLETE','READY'):
        logger.info(f"Succeeded to check securityhub standard status@{region_name}:{standard_status}")
        is_standard_status = True
    else:
        logger.error(f"Failed to check securityhub standard status@{region_name}:{standard_status}")
        is_standard_status = False
    return is_standard_status

def is_describe_hub (session,regions: List[str]) -> bool:
    check_regions = {}
    for region_name in regions:
        sh = session.client("securityhub", region_name=region_name)
        try:
            sh.describe_hub()
            check_regions[region_name] = True
        except Exception as e:
            logger.error(f"{e}:{region_name}")
            check_regions[region_name] = False
    return all(check_regions.values())

def is_get_enabled_standards (session,regions: List[str],account_id: str) -> bool:
    check_regions = {}
    for region_name in regions:
        sh = session.client("securityhub", region_name=region_name)
        try:
            std_arn = f"arn:aws:securityhub:{region_name}:{account_id}:standards/{SECURITY_HUB_AFSBP_STANDARD_NAME}"
            res = sh.get_enabled_standards(StandardsSubscriptionArns=[std_arn])
            standard_status = res["StandardsSubscriptions"][0]["StandardsStatus"]
            if standard_status in ('INCOMPLETE','READY'):
                logger.info(f"Succeeded to check securityhub standard status@{region_name}:{standard_status}")
                check_regions[region_name] = True
            else:
                logger.error(f"Failed to check securityhub standard status@{region_name}:{standard_status}")
                check_regions[region_name] = False
        except Exception as e:
            logger.error(f"Failed to check securityhub standard status@{region_name}:{standard_status}")
            logger.error(e)
            check_regions[region_name] = False
    return all(check_regions.values())
    
def is_control_status(disable_list: List[str],region_name: str,control_list: List[str]):
    check_control_status={}
    for control in disable_list:
        control_status = [x['ControlStatus'] for x
                            in control_list if 'ControlId'
                            in x and 'ControlStatus'
                            in x and x['ControlId'] == control][0]
        if control_status == "DISABLED":
            check_control_status[control] = True
        else:
            check_control_status[control] = False
    return check_control_status

def is_describe_standards_controls (session,
                                    regions: List[str],
                                    account_id: str) -> None:
    
    check_regions = {}
    for region_name in regions:
        sh = session.client("securityhub", region_name=region_name)
        try:
            std_sub_arn = f"arn:aws:securityhub:{region_name}:{account_id}:subscription/{SECURITY_HUB_AFSBP_STANDARD_NAME}"
            control_list = sh.describe_standards_controls(
            StandardsSubscriptionArn=std_sub_arn,)["Controls"]
            check_control_status = is_control_status(SECURITY_HUB_AFSBP_DISABLE_CONTROL_LIST,region_name,control_list)
            if all(check_control_status.values()):
                check_regions[region_name] = True
            else:
                check_regions[region_name] = False
            logger.info(
                    f"check_control_status@{region_name}: {check_control_status}"
            )
        except Exception as e:
            logger.error(f"check_control_status@{region_name}:{check_control_status}")
            logger.error(e)
            check_regions[region_name] = False
    logger.info(
            f"is_describe_standards_controls:{check_regions}"
    )
    return all(check_regions.values())

def lambda_handler(event, context):

    member_account_id=event["detail"]["serviceEventDetails"]["createManagedAccountStatus"]["account"]["accountId"]
    # Get Client
    member_session = get_member_session(member_account_id)

    # for raise error lazy
    errs = []

    for region_name in REGION_LIST:
        try:
            batch_enable_standards(member_session,region_name)
        except Exception as e:
            logger.error(f'Failed to enable standard@{region_name}:{SECURITY_HUB_AFSBP_STANDARD_NAME}')
            logger.error(e)
            errs.append(e)
        try:
            batch_disable_standards(member_session,region_name,member_account_id)
        except Exception as e:
            logger.error(f'Failed to disable standard@{region_name}:{SECURITY_HUB_CIS_STANDARD_NAME}')
            logger.error(e)
            errs.append(e)
        try:
            update_standards_control(
                member_session,
                region_name,
                member_account_id,
                )
        except Exception as e:
            logger.error(f"Failed to disable securityhub standards control@{region_name}")
            logger.error(e)
            errs.append(e)
    if errs:
        raise Exception('Failed to update securityhub')
    
    is_resources = {
        "cm_securityhub": False,
        "cm_securityhub_std": False,
        "cm_securityhub_control": False
    }
    
    is_resources["cm_securityhub"] = is_describe_hub(member_session,REGION_LIST)
    is_resources["cm_securityhub_std"] = is_get_enabled_standards(
        member_session,
        REGION_LIST,
        member_account_id
        )
    is_resources["cm_securityhub_control"] = is_describe_standards_controls(
        member_session,
        REGION_LIST,
        member_account_id
        )

    if not all(is_resources.values()):
        logger.error("Failed to enable securityhub")
        logger.error(
            f"is_resources: {is_resources}"
        )
        raise Exception('Fail to check reource')

    logger.info("Completed to enable securityhub")
    logger.info(
        f"is_resources: {is_resources}"
    )
    return {
        "is_resources": is_resources
    }