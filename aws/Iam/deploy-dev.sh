#!/bin/bash

aws cloudformation deploy \
    --template-file ./iam.yaml \
    --stack-name iam-dev \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
        Env=dev

aws cloudformation describe-stacks \
    --stack-name iam-dev \
    --query 'Stacks[].Outputs[?OutputKey==`ApigwCallingSqsRoleArn`].OutputValue'
    # --output text > ./iam-secret-id.txt
    