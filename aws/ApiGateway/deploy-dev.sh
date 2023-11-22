#!/bin/bash

aws cloudformation deploy \
    --template-file ./apigw.yaml \
    --stack-name api-gateway-dev \
    --parameter-overrides \
        Env=dev \
        LineSlideshowSqsArn=arn:aws:sqs:ap-northeast-1:935428647279:line-slideshow-sqs-dev \
        ApigwCallingSqsRoleArn=arn:aws:iam::935428647279:role/apigw-calling-sqs-role-dev