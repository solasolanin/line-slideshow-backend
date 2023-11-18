#!/bin/bash

# aws cloudformation deploy \
#     --template-file ExecLineSlideshow/template.yaml \
#     --stack-name lambda-execlineslideshow-dev \
#     --parameter-overrides \
#         Env=dev \
#         LineSlideshowSqsArn=arn:aws:sqs:ap-northeast-1:935428647279:line-slideshow-sqs-dev.fifo

sam build

if [ $? -ne 0 ]; then
    echo "sam build failed"
    exit 1
fi

sam deploy --config-env dev --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND