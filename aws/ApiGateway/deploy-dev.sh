#!/bin/bash

aws cloudformation deploy \
    --template-file ./apigw.yaml \
    --stack-name api-gateway-dev \
    --profile CryptoLineVSCode \
    --parameter-overrides \
        Env=dev \
        LineSlideshowSqsArn=arn:aws:sqs:ap-northeast-1:935428647279:line-slideshow-sqs-dev.fifo \
        ApigwCallingSqsRoleArn=arn:aws:iam::935428647279:role/apigw-calling-sqs-role-dev