#!/bin/bash

ENV=dev

aws cloudformation deploy \
    --template-file ./dynamodb.yaml \
    --stack-name dynamodb-$ENV \
    --parameter-overrides \
        Env=$ENV

# 初期値投入
aws dynamodb put-item \
    --table-name line-slideshow-dynamodb-contest-$ENV \
    --item '{
        "prize_id": {"N": "1"},
        "prize_name": {"S": "最優秀賞"},
        "photo_id": {"S": ""},
        "account_name": {"S":""}
      }'
aws dynamodb put-item \
    --table-name line-slideshow-dynamodb-contest-$ENV \
    --item '{
        "prize_id": {"N": "2"},
        "prize_name": {"S": "新婦賞"},
        "photo_id": {"S": ""},
        "account_name": {"S":""}
      }'
aws dynamodb put-item \
    --table-name line-slideshow-dynamodb-contest-$ENV \
    --item '{
        "prize_id": {"N": "3"},
        "prize_name": {"S": "新郎賞"},
        "photo_id": {"S": ""},
        "account_name": {"S":""}
      }'