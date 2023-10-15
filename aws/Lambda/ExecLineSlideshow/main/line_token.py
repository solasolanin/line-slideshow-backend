import json
import boto3


class LineToken:

    def __init__(self, env):
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
        self.__access_token = json.loads(
            get_secret_value_response['SecretString'])["ACCESS_TOKEN"]
        self.__channel_token = json.loads(
            get_secret_value_response['SecretString'])["CHANNEL_TOKEN"]

    @property
    def access_token(self):
        return self.__access_token

    @property
    def channel_token(self):
        return self.__channel_token
