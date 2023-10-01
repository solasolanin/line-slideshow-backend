#!/bin/bash

aws cloudformation deploy \
    --template-file ./secretsmanager.yaml \
    --stack-name secretsmanager-dev \
    --profile CryptoLineVSCode \
    --parameter-overrides \
        Env=dev