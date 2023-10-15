import requests


class Preview:
    """ 画像のプレビュー情報を保持するクラス

    Attributes:
        access_token (str): アクセストークン
        message_id (str): メッセージID
    """

    def __init__(self, access_token, message_id):
        self.__message_id = message_id
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        res = requests.get(
            f'https://api-data.line.me/v2/bot/message/{message_id}/content/preview', headers=headers)
        self.__content = res.content
        self.__code = res.status_code
        self.__extension = res.headers['Content-Type'].split('/')[-1]

    @property
    def content(self):
        return self.__content

    @property
    def code(self):
        return self.__code

    @property
    def extension(self):
        return self.__extension

    @property
    def filename(self):
        return f'{self.__message_id}_tmb.{self.__extension}'
