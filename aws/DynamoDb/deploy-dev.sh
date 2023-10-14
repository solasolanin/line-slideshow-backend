#!/bin/bash

aws cloudformation deploy \
    --template-file ./dynamodb.yaml \
    --stack-name dynamodb-dev \
    --parameter-overrides \
        Env=dev