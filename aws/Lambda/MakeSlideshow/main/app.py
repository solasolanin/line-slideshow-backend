import boto3
import os
import logging
import datetime
import photo_info
from PIL import Image, ImageDraw, ImageFont
import moviepy.editor as mp
from datetime import datetime


env = os.environ['ENV']
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 動画名のプレフィックス
VIDEO_NAME_PREFIX = "20231217_浅岡家野牧家_エンドロールムービー_作成日"
VIDEO_SIZE = (1920, 1080)
SINGLE_TIME = 1.25  # 1枚あたりの表示時間(sec)
FRAME_RATE = 24.0  # フレームレート(fps)

# BGM名
BGM_NAME = "Boom.mp3"

# 写真枚数
PHOTO_NUM = 139


def lambda_handler(event, context):
    print("event", event)

    # 動画ファイル名作成
    now = datetime.now()

    # DynamoDBから画像情報を取得
    photos = photo_info.PhotoInfo(f"line-slideshow-dynamodb-{env}")
    photo_contents = photos.contents
    photo_name_list = photos.list

    # S3準備
    s3 = boto3.resource('s3')
    private_bucket = s3.Bucket(f"line-slideshow-s3-{env}")
    public_bucket = s3.Bucket(f"line-slideshow-open-s3-{env}")

    # S3から画像リストを取得
    photo_list = public_bucket.objects.filter(
        Prefix="img/")
    print("photo_list", [k.key for k in photo_list])

    # 動画名
    v_name = f'{VIDEO_NAME_PREFIX}{datetime.now().strftime("%Y%m%d%H%M%S")}.mp4'

    # フォントファイルダウンロード
    private_bucket.download_file("resources/NotoSansJP-Bold.ttf",
                                 "/tmp/NotoSansJP-Bold.ttf")

    # 動画結合用ファイルダウンロード
    private_bucket.download_file("resources/list1.txt", "/tmp/list1.txt")
    private_bucket.download_file("resources/list2.txt", "/tmp/list2.txt")

    # BGMファイルダウンロード
    private_bucket.download_file(f"resources/{BGM_NAME}", f"/tmp/{BGM_NAME}")

    # 動画作成処理
    clips = []
    clips_name = []
    photo_count = 1
    for contetns in photo_contents:
        try:
            # 投稿者名取得
            account_name = contetns['body']['account_name']

            # 画像取得
            file_name = contetns['body']['file_name']
            public_bucket.download_file(f"img/{file_name}", '/tmp/'+file_name)

            # 画像読み込み
            img = Image.open(f'/tmp/{file_name}')

            # 画像サイズ取得
            width, height = img.size

            # アスペクト比によって処理を分ける
            if VIDEO_SIZE[0]/VIDEO_SIZE[1] > width/height:
                # 画像のリサイズ
                is_wide_margin = False
                nw = round(width*(VIDEO_SIZE[1]/height))
                resized_img = img.resize((nw, VIDEO_SIZE[1]))
                # 余白の計算
                x = round((VIDEO_SIZE[0]-nw)/2)
                y = 0

            else:
                # 画像のリサイズ
                is_wide_margin = True
                nh = round(height*(VIDEO_SIZE[0]/width))
                resized_img = img.resize((VIDEO_SIZE[0], nh))
                # 余白の計算
                x = 0
                y = round((VIDEO_SIZE[1]-nh)/2)

            # 余白の黒塗り
            video_frame = Image.new(resized_img.mode, VIDEO_SIZE, (0, 0, 0))
            video_frame.paste(resized_img, (x, y))

            # 提供者名の追加
            video_frame = attach_sponsor(
                account_name, video_frame, is_wide_margin)
            video_frame.save('/tmp/'+'new_'+file_name)

            # １枚あたりの表示時間で動画作成
            new_file_name = 'new_'+file_name
            clip = mp.ImageClip(
                f'/tmp/{new_file_name}').set_duration(SINGLE_TIME)
            clips.append(clip)
            clips_name.append(new_file_name)

            # tmpファイル削除
            os.remove('/tmp/'+file_name)

            # 140枚以上は処理しない
            photo_count += 1
            if photo_count >= PHOTO_NUM:
                print("photo_count", photo_count)
                break

        except Exception as e:
            print(e)
            continue

    # 動画の結合
    concat_clip = mp.concatenate_videoclips(clips, method="chain")

    # 一旦お掃除
    for clip_name in clips_name:
        os.remove('/tmp/'+clip_name)

    # イントロパートの追加
    # s3から取得
    video_files = ["endroll1.mp4", "endroll2.mp4", "endroll3.mp4"]
    private_bucket.download_file(
        f"resources/{video_files[0]}", '/tmp/' + video_files[0])
    private_bucket.download_file(
        f"resources/{video_files[1]}", '/tmp/' + video_files[1])
    private_bucket.download_file(
        f"resources/{video_files[2]}", '/tmp/' + video_files[2])

    # 音声ファイル結合
    intro1_clip = mp.VideoFileClip(f"/tmp/{video_files[0]}")
    intro2_clip = mp.VideoFileClip(f"/tmp/{video_files[1]}")
    final_clip = mp.VideoFileClip(f"/tmp/{video_files[2]}")
    # イントロ２からBGM開始なので先に結合
    audio_clip_tmp = mp.concatenate_videoclips(
        [intro2_clip, concat_clip, final_clip])
    audio_clip = audio_clip_tmp.set_audio(mp.AudioFileClip(f"/tmp/{BGM_NAME}"))
    video = mp.concatenate_videoclips([intro1_clip, audio_clip])

    video.write_videofile(f"/tmp/{v_name}", codec='libx264', audio_codec='aac',
                          temp_audiofile='/tmp/temp-audio.m4a', remove_temp=True)

    # 動画アップロード
    public_bucket.upload_file(f'/tmp/{v_name}', Key=f"video/{v_name}")

    return {
        'statusCode': 200,
        'body': {
            'video_url': f"https://line-slideshow-open-s3-{env}.s3-ap-northeast-1.amazonaws.com/video/{v_name}",
            'video_name': f'{v_name}',
        }
    }


def attach_sponsor(account_name, base_img, is_wide_margin):
    MARGIN = 10
    FONT_SIZE = 68
    INI_SIZE = (1920, 256)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    TITLE = f"提供：{account_name}様"

    # 貼り付ける画像が縦長なら白、横長なら黒の背景を作成
    b_x, b_y = base_img.size
    im = Image.new("RGB", INI_SIZE, BLACK if is_wide_margin else WHITE)
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype("/tmp/NotoSansJP-Bold.ttf", FONT_SIZE)

    # 提供者名の描画
    ix, iy, ex, ey = draw.textbbox((20, 0), TITLE, font=font)
    coordinates = (ix-MARGIN, iy-MARGIN, ex+MARGIN, ey+MARGIN)
    draw.multiline_text(
        (20, 0), TITLE, fill=WHITE if is_wide_margin else BLACK, font=font)
    im_crop = im.crop(coordinates)

    # 貼り付ける画像の上に貼り付け
    height = coordinates[3]-coordinates[1]
    base_img.paste(im_crop, (0, b_y-height))
    return base_img
