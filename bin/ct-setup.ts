#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "@aws-cdk/core";
import { CtSetupStack } from "../lib/ct-setup-stack";

const app = new cdk.App();
new CtSetupStack(app, "CtSetupStack", {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: "ap-northeast-1" },
});