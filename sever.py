import web
import imageio
import math
import os
import cv2
import json
import math
import requests
import numpy as np
from PIL import Image
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf
urls = (
    '/', 'upload_file'
)
app = web.application(urls, globals())

class upload_file():
    def POST(self):
        data = web.input()
        totalFrame = data.get('totalFrame')
        group = math.floor(int(totalFrame) / 16)
        video = data.get('video')
        path = 'video.mp4'
        with open(path, 'wb+') as fp:
            fp.write(video)
        cap = None
        vid = None
        try:
            cap = cv2.VideoCapture(path)
            vid = imageio.get_reader(path, "ffmpeg")
        except:
            os.remove(path)
            return '文件解码错误'
        # total = 0
        # for num, im in enumerate(vid):
        #     total = total + 1  # 计算总帧数
        # print('total:', total)

        datas = np.zeros((group, 16, 112, 112, 3), dtype=float)
        now_group = 0
        picture_num = 0
        num = 0
        while cap.isOpened():
            success, frame = cap.read()
            if success:
                image = tf.image.resize(frame, [112, 112])
                image.set_shape([112, 112, 3])
                tmp_data = np.array(image)
                datas[now_group][picture_num] = tmp_data
                picture_num += 1
                if picture_num == 16:
                    picture_num = 0
                    now_group += 1
            else:
                break
        print(datas.shape)
        datas = json.dumps({"signature_name": "predict_video", "instances": datas.tolist()})
        headers = {"content-type": "application/json"}
        r = requests.post('http://localhost:8501/v1/models/concentration:predict', data=datas, headers=headers)
        print("type(r):",type(r))
        predictions = json.loads(r.text)['predictions']
        # os.remove(path)
        print(predictions)
        print("type(trans):",type(predictions))
        return predictions




if __name__ == '__main__':
    app.run()