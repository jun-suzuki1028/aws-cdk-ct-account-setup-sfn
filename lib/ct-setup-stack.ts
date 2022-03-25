import * as cdk from "@aws-cdk/core";
import * as lambda from "@aws-cdk/aws-lambda";
import * as sfn from "@aws-cdk/aws-stepfunctions";
import * as iam from '@aws-cdk/aws-iam';
import * as tasks from "@aws-cdk/aws-stepfunctions-tasks";
import * as events from "@aws-cdk/aws-events";
import * as targets from '@aws-cdk/aws-events-targets';

export class CtSetupStack extends cdk.Stack {
  private LambdaDefaultRuntime = lambda.Runtime.PYTHON_3_8
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    const createLambdaRole = this.createLambdaRole()

    const DefaultVpcLambdaFunction = new lambda.Function(this, "DefaultVpcLambdaFunction", {
      code: new lambda.AssetCode("lambda"),
      runtime: this.LambdaDefaultRuntime,
      handler: "default_vpc.lambda_handler",
      memorySize: this.node.tryGetContext("lambda").defaultMemorySize,
      role: createLambdaRole,
      timeout: cdk.Duration.seconds(this.node.tryGetContext("lambda").defaultTimeOut),
    });

    const EbsEncryptionByDefaultLambdaFunction = new lambda.Function(this, "EbsEncryptionByDefaultLambdaFunction", {
      code: new lambda.AssetCode("lambda"),
      runtime: this.LambdaDefaultRuntime,
      handler: "ebs_encryption_by_default.lambda_handler",
      memorySize: this.node.tryGetContext("lambda").defaultMemorySize,
      role: createLambdaRole,
      timeout: cdk.Duration.seconds(this.node.tryGetContext("lambda").defaultTimeOut),
    });
    const PasswordPolicyLambdaFunction = new lambda.Function(this, "PasswordPolicyLambdaFunction", {
      code: new lambda.AssetCode("lambda"),
      runtime: this.LambdaDefaultRuntime,
      handler: "password_policy.lambda_handler",
      memorySize: this.node.tryGetContext("lambda").defaultMemorySize,
      role: createLambdaRole,
      timeout: cdk.Duration.seconds(this.node.tryGetContext("lambda").defaultTimeOut),
    });
    const PublicAccessBlockLambdaFunction = new lambda.Function(this, "PublicAccessBlockLambdaFunction", {
      code: new lambda.AssetCode("lambda"),
      runtime: this.LambdaDefaultRuntime,
      handler: "public_access_block.lambda_handler",
      memorySize: this.node.tryGetContext("lambda").defaultMemorySize,
      role: createLambdaRole,
      timeout: cdk.Duration.seconds(this.node.tryGetContext("lambda").defaultTimeOut),
    });
    const SecurityHubLambdaFunction = new lambda.Function(this, "SecurityHubLambdaFunction", {
      code: new lambda.AssetCode("lambda"),
      runtime: this.LambdaDefaultRuntime,
      handler: "security_hub.lambda_handler",
      memorySize: this.node.tryGetContext("lambda").defaultMemorySize,
      role: createLambdaRole,
      timeout: cdk.Duration.seconds(this.node.tryGetContext("lambda").defaultTimeOut),
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

  /**
   * リソースを展開するLambdaのRoleを作成する。
   */
   private createLambdaRole() {
    const policyName = "NewAccountSetupLambdaRolePolicy";
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
    const roleName = "NewAccountSetupLambdaRole";
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