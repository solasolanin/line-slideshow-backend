#!/bin/bash

aws cloudformation deploy \
    --template-file ./apigw.yaml \
    --stack-name api-gateway-dev \
    --profile CryptoLineVSCode \
    --parameter-overrides \
        Env=dev