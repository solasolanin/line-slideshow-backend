#!/bin/bash

aws cloudformation deploy \
    --template-file ./s3.yaml \
    --stack-name s3-dev \
    --profile CryptoLineVSCode \
    --parameter-overrides \
        Env=dev