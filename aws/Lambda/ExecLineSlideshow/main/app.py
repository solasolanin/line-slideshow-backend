import json
import boto3
import os
import logging
import requests
from botocore.exceptions import ClientError
from enum import Enum
from PIL import Image
from PIL.ExifTags import TAGS


env = os.environ['ENV']


class Returnable(Enum):
    SUCCESS = 0
    NOT_MESSAGE = 1,
    NOT_IMAGE = 2
    MESSAGE_FORMAT_ERROR = 3,
    INTERNAL_ERROR = 99


def lambda_handler(event, context):
    print('event:', event)

    bucket_name = f"line-slideshow-s3-{env}"

    try:
        # メッセージのパース
        event_body = json.loads(event['Records'][0]['body'])

        # メッセージ形式の確認
        if event_body['events'][0]['type'] != "message":
            return response(Returnable.NOT_MESSAGE)

        if event_body['events'][0]['message']['type'] != "image":
            return response(Returnable.NOT_IMAGE)

        message = event_body['events'][0]['message']
    except Exception as e:
        return response(Returnable.MESSAGE_FORMAT_ERROR, e)

    # トークンインスタンスの初期化
    lt = LineToken()

    # 画像取得
    message_id = event_body['events'][0]['message']['id']
    headers = {
        'Authorization': 'Bearer '+lt.get_access_token(),
    }
    contents = requests.get(
        f'https://api-data.line.me/v2/bot/message/{message_id}/content', headers=headers)
    logging.info(f'status_code:{contents.status_code}')

    extension = contents.headers['Content-Type'].split('/')[-1]
    image_name = f'{message_id}.{extension}'
    print('extension:', extension)
    try:
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        with open('/tmp/'+image_name, 'wb') as f:
            f.write(contents.content)

    except Exception as e:
        return response(Returnable.INTERNAL_ERROR, e)
    # 画像アップロード
    bucket.upload_file('/tmp/'+image_name, Key=image_name)

    # アカウント名取得
    account_name = get_account_name(
        event_body['events'][0]['source']['userId'], lt.get_access_token())

    # メッセージ情報登録
    set_msg_info(message_id, account_name, image_name, extension)

    return response(Returnable.SUCCESS)


# トークン取得
class LineToken:
    __access_token = None
    __channel_token = None

    def __init__(self):
        secret_name = f"line-slideshow-sm-{env}"
        region_name = "ap-northeast-1"

        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        LineToken.__access_token = json.loads(
            get_secret_value_response['SecretString'])["ACCESS_TOKEN"]
        LineToken.__channel_token = json.loads(
            get_secret_value_response['SecretString'])["CHANNEL_TOKEN"]

    def get_access_token(self):
        return LineToken.__access_token

    def get_channel_token(self):
        return LineToken.__channel_token


def response(returnable, err_message=None):
    match returnable:
        case Returnable.SUCCESS:
            logging.info("Success")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Image uploaded",
                }),
            }
        case Returnable.NOT_MESSAGE:
            logging.warning("Not message")
            return {
                "statusCode": 204,
                "body": json.dumps({
                    "message": "No message",
                }),
            }
        case Returnable.NOT_IMAGE:
            logging.warning("Not image")
            return {
                "statusCode": 204,
                "body": json.dumps({
                    "message": "No image",
                }),
            }
        case Returnable.MESSAGE_FORMAT_ERROR:
            logging.error(err_message)
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "message": "Message format error",
                }),
            }
        case Returnable.INTERNAL_ERROR:
            logging.error(err_message)
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "message": f"Internal error.\n {err_message}",
                }),
            }


def get_account_name(account_id, line_token):
    headers = {
        'Authorization': 'Bearer '+line_token,
    }
    contents = requests.get(
        f'https://api.line.me/v2/bot/profile/{account_id}', headers=headers)
    res = contents.content.decode('utf-8')
    return json.loads(res)["displayName"]


def set_msg_info(message_id, account_name, file_name, extension, date_time=None):
    values = {
        "account_name": account_name,
        "file_name": file_name,
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
