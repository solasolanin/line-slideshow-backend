import json
import boto3
import os
import logging
from botocore.exceptions import ClientError
from enum import Enum
from PIL import Image
from PIL.ExifTags import TAGS
import photo
import preview
import line_token
import account
import response


env = os.environ['ENV']


def lambda_handler(event, context):
    print('event:', event)

    bucket_name = f"line-slideshow-s3-{env}"

    try:
        # メッセージのパース
        event_body = json.loads(event['Records'][0]['body'])

        # メッセージ形式の確認
        if event_body['events'][0]['type'] != "message":
            return response.not_message()

        if event_body['events'][0]['message']['type'] != "image":
            return response.not_image()

        message = event_body['events'][0]['message']
    except Exception as e:
        return response.message_format_error(event)

    # トークンインスタンスの初期化
    line_token_info = line_token.LineToken(env)

    # 画像取得
    message_id = event_body['events'][0]['message']['id']
    photo_info = photo.Photo(line_token_info.access_token, message_id)
    if photo_info.code != 200:
        return response.internal_error(f'photo status code: {photo_info.code}')
    with open('/tmp/'+photo_info.filename, 'wb') as f:
        f.write(photo_info.content)

    # 画像のプレビュー情報取得
    preview_info = preview.Preview(line_token_info.access_token, message_id)
    if preview_info.code != 200:
        response.internal_error(f'preview status code: {preview_info.code}')
    with open('/tmp/'+preview_info.filename, 'wb') as f:
        f.write(preview_info.content)

    # 画像アップロード
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    bucket.upload_file('/tmp/' + photo_info.filename,
                       Key=f"img/{photo_info.filename}")
    bucket.upload_file('/tmp/'+preview_info.filename,
                       Key=f"tmb/{preview_info.filename}")

    # アカウント名取得
    account_info = account.Account(
        line_token_info.access_token, event_body['events'][0]['source']['userId'])
    account_name = account_info.account_name

    # メッセージ情報登録
    set_msg_info(message_id, account_name,
                 photo_info.filename, preview_info.filename, photo_info.extension)

    return response.success()


def set_msg_info(message_id, account_name, file_name, thumbnail=None, extension=None, date_time=None):
    values = {
        "account_name": account_name,
        "file_name": file_name,
        "thumbnail": thumbnail,
        "extension": extension,
        "date_time": date_time
    }

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(f'line-slideshow-dynamodb-{env}')
    table.put_item(
        Item={
            "id": message_id,
            "body": values
        })
    return
