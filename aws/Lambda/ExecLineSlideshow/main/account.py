import requests
import json


class Account:
    def __init__(self, access_token, account_id):
        self.__account_id = account_id
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        print("account_id: ", account_id)
        res = requests.get(
            f'https://api.line.me/v2/bot/profile/{account_id}', headers=headers)
        res = res.content.decode('utf-8')
        print("res: ", res)
        try:
            self.__account_name = json.loads(res)["displayName"]
        except:
            self.__account_name = "匿名"

    @property
    def account_id(self):
        return self.__account_id

    @property
    def account_name(self):
        return self.__account_name
