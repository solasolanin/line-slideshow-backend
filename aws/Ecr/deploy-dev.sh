#!/bin/bash

aws cloudformation deploy \
    --template-file ./ecr.yaml \
    --stack-name ecr-dev \
    --parameter-overrides \
        Env=dev 