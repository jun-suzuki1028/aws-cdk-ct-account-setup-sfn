import { Construct } from 'constructs';
import {
  Stack,
  StackProps,
  Duration,
  aws_iam as iam,
  aws_lambda as lambda,
  aws_events as events,
  aws_events_targets as targets,
  aws_stepfunctions as sfn,
  aws_stepfunctions_tasks as tasks,
} from 'aws-cdk-lib';
import { Naming } from './naming';

export class CtSetupStack extends Stack {
  private LambdaDefaultRuntime = lambda.Runtime.PYTHON_3_8
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);
    const memorySize = this.node.tryGetContext("lambda").defaultMemorySize
    const timeoutSecond = this.node.tryGetContext("lambda").defaultTimeOut

    const policyName = Naming.of("lambda-role-policy");
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
    const roleName =  Naming.of("lambda-role");
    const lambdaRole = new iam.Role(this, roleName, {
      roleName: roleName,
      assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
      managedPolicies: [
        policy,
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole')
      ],
    });

    const DefaultVpcLambdaFunction = new lambda.Function(this, "DefaultVpcLambdaFunction", {
      code: new lambda.AssetCode("lambda"),
      runtime: this.LambdaDefaultRuntime,
      handler: "default_vpc.lambda_handler",
      memorySize: memorySize,
      role: lambdaRole,
      timeout: Duration.seconds(timeoutSecond),
      functionName: Naming.of("delete-default-vpc")
    });

    const EbsEncryptionByDefaultLambdaFunction = new lambda.Function(this, "EbsEncryptionByDefaultLambdaFunction", {
      code: new lambda.AssetCode("lambda"),
      runtime: this.LambdaDefaultRuntime,
      handler: "ebs_encryption_by_default.lambda_handler",
      memorySize: memorySize,
      role: lambdaRole,
      timeout: Duration.seconds(timeoutSecond),
      functionName: Naming.of("enable-ebs-encryption-by-default")
    });
    const PasswordPolicyLambdaFunction = new lambda.Function(this, "PasswordPolicyLambdaFunction", {
      code: new lambda.AssetCode("lambda"),
      runtime: this.LambdaDefaultRuntime,
      handler: "password_policy.lambda_handler",
      memorySize: memorySize,
      role: lambdaRole,
      timeout: Duration.seconds(timeoutSecond),
      functionName: Naming.of("change-password-policy")
    });
    const PublicAccessBlockLambdaFunction = new lambda.Function(this, "PublicAccessBlockLambdaFunction", {
      code: new lambda.AssetCode("lambda"),
      runtime: this.LambdaDefaultRuntime,
      handler: "public_access_block.lambda_handler",
      memorySize: memorySize,
      role: lambdaRole,
      timeout: Duration.seconds(timeoutSecond),
      functionName: Naming.of("enable-public-access-block")
    });
    const SecurityHubLambdaFunction = new lambda.Function(this, "SecurityHubLambdaFunction", {
      code: new lambda.AssetCode("lambda"),
      runtime: this.LambdaDefaultRuntime,
      handler: "security_hub.lambda_handler",
      memorySize: memorySize,
      role: lambdaRole,
      timeout: Duration.seconds(timeoutSecond),
      functionName: Naming.of("change-security-hub")
    });
    const end = new sfn.Pass(this, "End", {});
  
    const stateMachine = new sfn.StateMachine(this, "NewAccountSetupStateMachine", {
      stateMachineName: Naming.of("new-account-state-machine"),
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
      }))
  });
  const rule = new events.Rule(this, 'AccountCheckRule', {
    ruleName: Naming.of("create-account-check-rule"),
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

}