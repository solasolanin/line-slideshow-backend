#!/bin/bash

aws cloudformation deploy \
    --template-file ./sqs.yaml \
    --stack-name sqs-dev \
    --profile CryptoLineVSCode \
    --parameter-overrides \
        Env=dev