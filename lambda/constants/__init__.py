## 実行対象のリージョン
REGION_LIST = ["us-east-1","ap-northeast-1"]
## Security Hub AFSBで無効化したいコントロール
SECURITY_HUB_AFSBP_DISABLE_CONTROL_LIST = ["IAM.6","EC2.8","CloudTrail.5"]
SECURITY_HUB_AFSBP_STANDARD_NAME = "aws-foundational-security-best-practices/v/1.0.0"
SECURITY_HUB_CIS_STANDARD_NAME = "cis-aws-foundations-benchmark/v/1.2.0"

PASSWORD_POLICY = {
    "MinimumPasswordLength": 8,
    "RequireSymbols": True,
    "RequireNumbers": True,
    "RequireUppercaseCharacters": True,
    "RequireLowercaseCharacters": True,
    "AllowUsersToChangePassword": True,
}