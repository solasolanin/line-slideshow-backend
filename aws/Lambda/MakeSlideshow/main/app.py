import boto3
import os
import logging
import datetime
import photo_info
from PIL import Image, ImageDraw, ImageFont
import moviepy.editor as mp


env = os.environ['ENV']
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 動画名のプレフィックス
VIDEO_NAME_PREFIX = "slideshow-"
VIDEO_SIZE = (1920, 1080)
SINGLE_TIME = 1.25  # 1枚あたりの表示時間(sec)
FRAME_RATE = 24.0  # フレームレート(fps)

# BGM名
BGM_NAME = "Boom.mp3"


def lambda_handler(event, context):
    # DynamoDBから画像情報を取得
    photos = photo_info.PhotoInfo(f"line-slideshow-dynamodb-{env}")
    photo_contents = photos.contents
    photo_name_list = photos.list

    # S3準備
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(f"line-slideshow-s3-{env}")

    # 動画名
    v_name = f'{VIDEO_NAME_PREFIX}{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.mp4'

    # フォントファイルダウンロード
    bucket.download_file("resources/NotoSansJP-Bold.ttf",
                         "/tmp/NotoSansJP-Bold.ttf")

    # 動画結合用ファイルダウンロード
    bucket.download_file("resources/list1.txt", "/tmp/list1.txt")
    bucket.download_file("resources/list2.txt", "/tmp/list2.txt")

    # BGMファイルダウンロード
    bucket.download_file(f"resources/{BGM_NAME}", f"/tmp/{BGM_NAME}")

    # 動画作成処理
    clips = []
    clips_name = []
    for contetns in photo_contents:
        # 投稿者名取得
        account_name = contetns['body']['account_name']

        # 画像取得
        file_name = contetns['body']['file_name']
        bucket.download_file(f"img/{file_name}", '/tmp/'+file_name)

        # 画像読み込み
        img = Image.open(f'/tmp/{file_name}')

        # 画像サイズ取得
        width, height = img.size

        if height >= width:
            # 画像のリサイズ
            is_wide = False
            nw = round(width*(VIDEO_SIZE[1]/height))
            resized_img = img.resize((nw, VIDEO_SIZE[1]), Image.BOX)
            # 余白の計算
            x = round((VIDEO_SIZE[0]-nw)/2)
            y = 0

        else:
            # 画像のリサイズ
            is_wide = True
            nh = round(height*(VIDEO_SIZE[0]/width))
            resized_img = img.resize((VIDEO_SIZE[0], nh), Image.BOX)
            # 余白の計算
            x = 0
            y = round((VIDEO_SIZE[1]-nh)/2)

        # 余白の黒塗り
        video_frame = Image.new(resized_img.mode, VIDEO_SIZE, (0, 0, 0))
        video_frame.paste(resized_img, (x, y))

        # 提供者名の追加
        video_frame = attach_sponsor(account_name, video_frame, is_wide)
        video_frame.save('/tmp/'+'new_'+file_name)

        # １枚あたりの表示時間で動画作成
        new_file_name = 'new_'+file_name
        clip = mp.ImageClip(f'/tmp/{new_file_name}').set_duration(SINGLE_TIME)
        clips.append(clip)
        clips_name.append(new_file_name)

        # tmpファイル削除
        os.remove('/tmp/'+file_name)

    # 動画の結合
    concat_clip = mp.concatenate_videoclips(clips, method="chain")

    # 一旦お掃除
    for clip_name in clips_name:
        os.remove('/tmp/'+clip_name)

    # イントロパートの追加
    # s3から取得
    video_files = ["endroll1.mp4", "endroll2.mp4"]
    bucket.download_file(
        f"resources/{video_files[0]}", '/tmp/' + video_files[0])
    bucket.download_file(
        f"resources/{video_files[1]}", '/tmp/' + video_files[1])

    # 音声ファイル結合
    intro1_clip = mp.VideoFileClip(f"/tmp/{video_files[0]}")
    intro2_clip = mp.VideoFileClip(f"/tmp/{video_files[1]}")
    # イントロ２からBGM開始なので先に結合
    audio_clip_tmp = mp.concatenate_videoclips([intro2_clip, concat_clip])
    audio_clip = audio_clip_tmp.set_audio(mp.AudioFileClip(f"/tmp/{BGM_NAME}"))
    video = mp.concatenate_videoclips([intro1_clip, audio_clip])

    video.write_videofile("/tmp/main.mp4", codec='libx264', audio_codec='aac',
                          temp_audiofile='/tmp/temp-audio.m4a', remove_temp=True)

    # 動画アップロード
    bucket.upload_file(f'/tmp/main.mp4', Key=f"video/main.mp4")


def attach_sponsor(account_name, base_img, is_wide):
    MARGIN = 10
    FONT_SIZE = 68
    INI_SIZE = (1920, 256)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    TITLE = f"提供：{account_name}様"

    # 貼り付ける画像が縦長なら白、横長なら黒の背景を作成
    b_x, b_y = base_img.size
    im = Image.new("RGB", INI_SIZE, BLACK if is_wide else WHITE)
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype("/tmp/NotoSansJP-Bold.ttf", FONT_SIZE)

    # 提供者名の描画
    ix, iy, ex, ey = draw.textbbox((20, 0), TITLE, font=font)
    coordinates = (ix-MARGIN, iy-MARGIN, ex+MARGIN, ey+MARGIN)
    draw.multiline_text(
        (20, 0), TITLE, fill=WHITE if is_wide else BLACK, font=font)
    im_crop = im.crop(coordinates)

    # 貼り付ける画像の上に貼り付け
    height = coordinates[3]-coordinates[1]
    base_img.paste(im_crop, (0, b_y-height))
    return base_img
