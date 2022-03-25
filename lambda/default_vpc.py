import logging
from typing import List
from common.get_session import get_member_session
from constants import REGION_LIST

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def delete_sub(ec2, vpc_id: str):
    response = ec2.describe_subnets( \
        Filters=[ { 'Name': 'vpc-id', 'Values':[ vpc_id ], } ] )
    subs = map(lambda x:x['SubnetId'], response['Subnets'])
    for sub in subs:
        ec2.delete_subnet(SubnetId=sub)
    logger.info(f" Succeeded to delete Subnet")

def delete_igw(ec2, vpc_id: str):
    response = ec2.describe_internet_gateways( \
        Filters=[ { 'Name': 'attachment.vpc-id', 'Values':[ vpc_id ], } ] )

    for igw in response['InternetGateways']:
        for attach in igw['Attachments']:
            if attach['State'] == 'available':
                ec2.detach_internet_gateway(
                    InternetGatewayId = igw['InternetGatewayId'],
                    VpcId = vpc_id)
        ec2.delete_internet_gateway(InternetGatewayId=igw['InternetGatewayId'])
    logger.info(f" Succeeded to delete InternetGateway")

def delete_vpc(ec2, vpc_id: str):
    ec2.delete_vpc(VpcId=vpc_id)
    logger.info(f" Succeeded to delete VPC")

def get_default_vpc_id(ec2) -> str:
    attributes = ec2.describe_account_attributes(AttributeNames = ['default-vpc'] )
    vpc_id=attributes['AccountAttributes'][0]['AttributeValues'][0]['AttributeValue']
    return vpc_id

def is_get_default_vpc (member_session,regions: List[str]) -> bool:
    check_regions = {}
    for region_name in regions:
        ec2 = member_session.client('ec2',region_name=region_name)
        try:
            vpc_id=get_default_vpc_id(ec2)
            if vpc_id == "none":
                check_regions[region_name] = True
            else:
                check_regions[region_name] = False
        except Exception as e:
            logger.error(f"{e}:{region_name}")
            check_regions[region_name] = False
    return all(check_regions.values())
    
def lambda_handler(event, context):

    member_account_id=event["detail"]["serviceEventDetails"]["createManagedAccountStatus"]["account"]["accountId"]
    # Get Client
    member_session = get_member_session(member_account_id)
    #実行対象のリージョン取得
    regions=REGION_LIST

    errs = []
    for region_name in regions:
        try:
            ec2 = member_session.client('ec2',region_name=region_name)
            vpc_id=get_default_vpc_id(ec2)
            
            if vpc_id != "none":
                delete_sub(ec2, vpc_id)
                delete_igw(ec2, vpc_id)
                delete_vpc(ec2, vpc_id)
                logger.info(f"Succeeded to delete default VPC@{region_name}:{vpc_id}")
            else:
                logger.info(f"default VPC is already been deleted@{region_name}")
        except Exception as e:
            logger.error(f'Failed to delete default VPC@{region_name}')
            logger.error(e)
            errs.append(e)

    if errs:
        raise Exception('Failed to delete default VPC')
    
    is_resources = {
        "default_vpc": False,
    }
    is_resources["default_vpc"] = is_get_default_vpc(member_session,regions)

    # is_resourcesにFalseがないか確認
    if not all(is_resources.values()):
        logger.error("Failed to delete default vpc")
        logger.error(
            f"is_resources: {is_resources}"
        )
        raise Exception('Fail to check reource')

    logger.info("Completed to delete default vpc")
    logger.info(f"is_resources: {is_resources}")
    return {"is_resources": is_resources}