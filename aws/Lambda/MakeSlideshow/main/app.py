import boto3
import os
import logging
import datetime
import photo_info
import cv2
from PIL import Image
import numpy


# env = os.environ['ENV']
env = 'dev'
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 動画名のプレフィックス
VIDEO_NAME_PREFIX = "slideshow-"
VIDEO_SIZE = (1920, 1080)
SINGLE_TIME = 1.25  # 1枚あたりの表示時間(sec)
FRAME_RATE = 20.0  # フレームレート(fps)


def lambda_handler(event, context):
    # DynamoDBから画像情報を取得
    photos = photo_info.PhotoInfo(f"line-slideshow-dynamodb-{env}")
    photo_contents = photos.contents
    # print(photo_contents)
    photo_name_list = photos.list

    # S3準備
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(f"line-slideshow-s3-{env}")

    # 動画名
    v_name = f'{VIDEO_NAME_PREFIX}{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.mp4'

    # 動画設定
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(f'/tmp/{v_name}', fourcc, FRAME_RATE, VIDEO_SIZE)

    # 動画作成処理
    for contetns in photo_contents:

        # 画像取得
        file_name = contetns['body']['file_name']
        bucket.download_file(f"img/{file_name}", '/tmp/'+file_name)
        img = cv2.imread('/tmp/'+file_name)
        height, width = img.shape[:2]

        if height > width:
            nw = round(width*(VIDEO_SIZE[1]/height))
            resized_img = cv2.resize(img, dsize=(nw, VIDEO_SIZE[1]))
            # 余白の計算
            x = round((VIDEO_SIZE[0]-nw)/2)
            y = 0

        else:
            nh = round(height*(VIDEO_SIZE[0]/width))
            resized_img = cv2.resize(img, dsize=(VIDEO_SIZE[0], nh))
            # 余白の計算
            x = 0
            y = round((VIDEO_SIZE[1]-nh)/2)

        # 余白の黒塗り
        resized_img = Image.fromarray(resized_img)
        video_frame = Image.new(resized_img.mode, VIDEO_SIZE, (0, 0, 0))
        video_frame.paste(resized_img, (x, y))
        dst = numpy.asarray(video_frame)
        # print("size", dst.shape[:2])
        cv2.imwrite('/tmp/'+'new_'+file_name, dst)

        # フレームレートに拡張して動画作成
        for i in range(int(FRAME_RATE*SINGLE_TIME)):
            video.write(dst)

        # tmpファイル削除
        os.remove('/tmp/'+file_name)
        os.remove('/tmp/'+'new_'+file_name)

    video.release()

    # 動画アップロード
    bucket.upload_file(f'/tmp/{v_name}', Key=f"video/{v_name}")
