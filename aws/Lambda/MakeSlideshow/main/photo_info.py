import boto3


class PhotoInfo:

    def __init__(self, table_name):
        self.__dynamodb = boto3.resource('dynamodb')
        response = self.__dynamodb.Table(table_name).scan()
        print("response", response)
        self.__contents = response['Items']
        self.__size = len(self.__contents)
        self.__photo_list = []
        for content in self.__contents:
            self.__photo_list.append(content['body']['file_name'])

    @property
    def contents(self):
        return self.__contents

    @property
    def size(self):
        return self.__size

    @property
    def list(self):
        return self.__photo_list
