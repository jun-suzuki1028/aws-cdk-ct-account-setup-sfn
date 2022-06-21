#!/usr/bin/env node
import "source-map-support/register";
import {
  App,
} from 'aws-cdk-lib';
import { CtSetupStack } from "../lib/ct-setup-stack";

const app = new App();
new CtSetupStack(app, "CtSetupStack", {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: "ap-northeast-1" },
});