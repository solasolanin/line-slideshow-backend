#!/bin/bash

cd main
docker build -t make-lideshow .
docker tag make-lideshow:latest 935428647279.dkr.ecr.ap-northeast-1.amazonaws.com/make-lideshow:latest
docker push 935428647279.dkr.ecr.ap-northeast-1.amazonaws.com/make-lideshow:latest
cd ../

aws cloudformation deploy \
    --template-file ./template.yaml \
    --stack-name make-slideshow-lambda \
    --parameter-overrides \
        Env=dev

# sam build

# if [ $? -ne 0 ]; then
#     echo "sam build failed"
#     exit 1
# fi

# sam deploy --config-env dev
# aws cloudformation deploy \
#     --template-file ./template.yaml \
#     --stack-name make-slideshow-lambda \
#     --parameter-overrides \
#         Env=dev \
#         MakeSlideshowRoleArn=arn:aws:iam::935428647279:role/make-slideshow-role-dev 