import json

# import requests
import boto3
import os
import logging
import requests
from botocore.exceptions import ClientError
from enum import Enum

s3 = boto3.resource('s3')
env = os.environ['ENV']

class Returnable(Enum):
    SUCCESS=0
    NOT_MESSAGE=1,
    NOT_IMAGE=2
    MESSAGE_FORMAT_ERROR=3,
    INTERNAL_ERROR=99


def lambda_handler(event, context):
    print('event:',event)
    

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

    # 画像取得
    message_id = event_body['events'][0]['message']['id']
    line_token = getLineToken("ACCESS_TOKEN")
    headers = {
        'Authorization':'Bearer '+line_token,
    }
    contents = requests.get(f'https://api-data.line.me/v2/bot/message/{message_id}/content', headers=headers)
    print(contents)
    logging.info(f'status_code:{contents.status_code}')

    # event_body = json.loads(event['Records'][0]['body'])
    # url = event_body['events'][0]['message']['originalContentUrl']
    # url = contents['originalContentUrl']
    extension = contents.headers['Content-Type'].split('/')[-1]
    image_name=f'{message_id}.{extension}'
    print('extension:',extension)
    try:
        bucket = s3.Bucket(bucket_name)
        with open('/tmp/'+image_name, 'wb') as f:
            f.write(contents.content)
           
    except Exception as e:
        return response(Returnable.INTERNAL_ERROR, e)
    # 画像アップロード
    bucket.upload_file('/tmp/'+image_name, Key=image_name)
    # bucket.put_object(Body=image.content, Key=image_name)

    return response(Returnable.SUCCESS)


# トークン取得
def getLineToken(key=None):
    secret_name = f"line-slideshow-sm-{env}"
    region_name = "ap-northeast-1"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        return response(Returnable.INTERNAL_ERROR, e.response['Error']['Message'])

    print('get_secret_value_response:',get_secret_value_response)
    secret = json.loads(get_secret_value_response['SecretString'])
    print('secret:',secret[key])
    return secret[key] if key!=None else secret
    

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