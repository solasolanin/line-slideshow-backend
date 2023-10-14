#!/bin/bash

aws cloudformation deploy \
    --template-file ./sqs.yaml \
    --stack-name sqs-dev \
    --parameter-overrides \
        Env=dev