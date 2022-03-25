import * as cdk from "@aws-cdk/core";
import * as lambda from "@aws-cdk/aws-lambda";
import * as sfn from "@aws-cdk/aws-stepfunctions";
import * as iam from '@aws-cdk/aws-iam';
import * as tasks from "@aws-cdk/aws-stepfunctions-tasks";
import * as events from "@aws-cdk/aws-events";
import * as targets from '@aws-cdk/aws-events-targets';

export class CtAccountSetupStack extends cdk.Stack {
  private LambdaDefaultRuntime = lambda.Runtime.PYTHON_3_8
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    const createLambdaRole = this.createLambdaRole()
    const systemName = this.node.tryGetContext('systemName');
    const envType = this.node.tryGetContext('envType');
    const memorySize = this.node.tryGetContext("lambda").defaultMemorySize
    const timeoutSecond = this.node.tryGetContext("lambda").defaultTimeOut

    const DefaultVpcLambdaFunction = new lambda.Function(this, "DefaultVpcLambdaFunction", {
      code: new lambda.AssetCode("lambda"),
      runtime: this.LambdaDefaultRuntime,
      handler: "default_vpc.lambda_handler",
      memorySize: memorySize,
      role: createLambdaRole,
      timeout: cdk.Duration.seconds(timeoutSecond),
      functionName: systemName+envType+"delete-default-vpc"
    });

    const EbsEncryptionByDefaultLambdaFunction = new lambda.Function(this, "EbsEncryptionByDefaultLambdaFunction", {
      code: new lambda.AssetCode("lambda"),
      runtime: this.LambdaDefaultRuntime,
      handler: "ebs_encryption_by_default.lambda_handler",
      memorySize: memorySize,
      role: createLambdaRole,
      timeout: cdk.Duration.seconds(timeoutSecond),
      functionName: systemName+envType+"enable-ebs-encryption-by-default"
    });
    const PasswordPolicyLambdaFunction = new lambda.Function(this, "PasswordPolicyLambdaFunction", {
      code: new lambda.AssetCode("lambda"),
      runtime: this.LambdaDefaultRuntime,
      handler: "password_policy.lambda_handler",
      memorySize: memorySize,
      role: createLambdaRole,
      timeout: cdk.Duration.seconds(timeoutSecond),
      functionName: systemName+envType+"change-password-policy"
    });
    const PublicAccessBlockLambdaFunction = new lambda.Function(this, "PublicAccessBlockLambdaFunction", {
      code: new lambda.AssetCode("lambda"),
      runtime: this.LambdaDefaultRuntime,
      handler: "public_access_block.lambda_handler",
      memorySize: memorySize,
      role: createLambdaRole,
      timeout: cdk.Duration.seconds(timeoutSecond),
      functionName: systemName+envType+"enable-public-access-block"
    });
    const SecurityHubLambdaFunction = new lambda.Function(this, "SecurityHubLambdaFunction", {
      code: new lambda.AssetCode("lambda"),
      runtime: this.LambdaDefaultRuntime,
      handler: "security_hub.lambda_handler",
      memorySize: memorySize,
      role: createLambdaRole,
      timeout: cdk.Duration.seconds(timeoutSecond),
      functionName: systemName+envType+"change-security-hub"
    });
    const end = new sfn.Pass(this, "End", {});
  
    const stateMachine = new sfn.StateMachine(this, "NewAccountSetupStateMachine", {
      definition: new tasks.LambdaInvoke(this, "DefaultVpc", {
        lambdaFunction: DefaultVpcLambdaFunction,
        resultPath: '$.DeleteDefaultVpc',
      }).next(new tasks.LambdaInvoke(this, "EbsEncryptionByDefault",{
        lambdaFunction: EbsEncryptionByDefaultLambdaFunction,
        resultPath: '$.EbsEncryptionByDefault',
      })).next(new tasks.LambdaInvoke(this, "PasswordPolicy",{
        lambdaFunction: PasswordPolicyLambdaFunction,
        resultPath: '$.PasswordPolicy',
      })).next(new tasks.LambdaInvoke(this, "PublicAccessBlock",{
        lambdaFunction: PublicAccessBlockLambdaFunction,
        resultPath: '$.PublicAccessBlock',
      })).next(new tasks.LambdaInvoke(this, "SecurityHub",{
        lambdaFunction: SecurityHubLambdaFunction,
        resultPath: '$.SecurityHub',
      })).next(end)
  });
  const rule = new events.Rule(this, 'NewAccountCheckRule', {
    eventPattern:{
      "source": ["aws.controltower"],
      "detailType":["AWS Service Event via CloudTrail"],
      "detail": {
        "eventName": ["CreateManagedAccount"]
      }
    },
    targets: [new targets.SfnStateMachine(stateMachine)],
  });
  }

   private createLambdaRole() {
    const systemName = this.node.tryGetContext('systemName');
    const envType = this.node.tryGetContext('envType');
    const policyName = systemName+envType+"lambda-role-policy";
    const policy = new iam.ManagedPolicy(this, policyName, {
      managedPolicyName: policyName,
      statements: [

        new iam.PolicyStatement({
          actions: [
            "sts:AssumeRole",
          ],
          resources: ["*"]
        }),

      ],
    });
    const roleName = systemName+envType+"lambda-role";
    const senderLambdaRole = new iam.Role(this, roleName, {
      roleName: roleName,
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
      managedPolicies: [
        policy,
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole')
      ],
    });
    return senderLambdaRole
  }

}