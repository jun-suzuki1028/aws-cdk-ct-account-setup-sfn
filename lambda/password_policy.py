import json
import boto3
import logging
from common.get_session import get_member_session
from constants import PASSWORD_POLICY

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def update_password_policy(member_session):
    iam = member_session.client("iam")
    iam.update_account_password_policy(
        MinimumPasswordLength=PASSWORD_POLICY['MinimumPasswordLength'],
        RequireSymbols=PASSWORD_POLICY['RequireSymbols'],
        RequireNumbers=PASSWORD_POLICY['RequireNumbers'],
        RequireUppercaseCharacters=PASSWORD_POLICY['RequireUppercaseCharacters'],
        RequireLowercaseCharacters=PASSWORD_POLICY['RequireLowercaseCharacters'],
        AllowUsersToChangePassword=PASSWORD_POLICY['AllowUsersToChangePassword'],
    )

def check_password_policy(member_session):
    results = {
        'minimum_password_length': False,
        'require_symbols': False,
        'require_numbers': False,
        'require_uppercase_characters': False,
        'require_lowercase_characters': False,
        'allow_users_to_change_password': False,
    }

    iam = member_session.client("iam")
    res_password_policy = iam.get_account_password_policy()["PasswordPolicy"]

    results['minimum_password_length'] = res_password_policy['MinimumPasswordLength'] == PASSWORD_POLICY['MinimumPasswordLength']
    if not results['minimum_password_length']:
        logger.error(
            f'MinimumPasswordLength is not equal. {PASSWORD_POLICY["MinimumPasswordLength"]} expect but {res_password_policy["MinimumPasswordLength"]} ')

    results['require_symbols'] = res_password_policy['RequireSymbols'] == PASSWORD_POLICY['RequireSymbols']
    results['require_numbers'] = res_password_policy['RequireNumbers'] == PASSWORD_POLICY['RequireNumbers']
    results['require_uppercase_characters'] = res_password_policy['RequireUppercaseCharacters'] == PASSWORD_POLICY['RequireUppercaseCharacters']
    results['require_lowercase_characters'] = res_password_policy['RequireLowercaseCharacters'] == PASSWORD_POLICY['RequireLowercaseCharacters']
    results['allow_users_to_change_password'] = res_password_policy['AllowUsersToChangePassword'] == PASSWORD_POLICY['AllowUsersToChangePassword']

    return results

def lambda_handler(event, context):

    member_account_id=event["detail"]["serviceEventDetails"]["createManagedAccountStatus"]["account"]["accountId"]
    # Get Client
    member_session = get_member_session(member_account_id)

    update_password_policy(member_session)

    is_resources = {
        'password_policy': False
    }

    check_results = check_password_policy(member_session)

    is_resources['password_policy'] = all(check_results.values())

    if not all(is_resources.values()):
        logger.error("Failed to update password policy")
        logger.error(json.dumps(check_results))
        logger.error(
            f"is_resources: {is_resources}"
        )
        raise Exception('Fail to check reource')

    logger.info("Succeeded in updating IAM password policy")
    logger.info(
        f"is_resources: {is_resources}"
    )
    return {
        "is_resources": is_resources
    }