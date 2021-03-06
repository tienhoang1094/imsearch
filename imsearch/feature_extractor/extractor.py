import os
import sys
import time
import json
import base64
import numpy as np
import redis
import tensorflow as tf

import keras
from keras.applications.inception_resnet_v2 import preprocess_input

from object_detector import get_model, preprocess_image, resize_image, label_to_name, labels_to_names_dict


def get_session():
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    return tf.Session(config=config)


keras.backend.tensorflow_backend.set_session(get_session())

REDIS_DB = redis.StrictRedis.from_url(os.environ.get('REDIS_URI', 'redis://localhost:6379/0'))
REDIS_QUEUE = 'image_queue'
BATCH_SIZE = 32

inception_model = keras.applications.inception_resnet_v2.InceptionResNetV2(
    include_top=False, weights='imagenet', pooling='avg')


def get_inception_features(x):
    x = preprocess_input(x)
    x = inception_model.predict(np.expand_dims(x, axis=0))
    return base64.b64encode(x[0]).decode("utf-8")


def decode_image(_q, dtype=np.uint8):
    if sys.version_info.major == 3:
        img = bytes(_q['image'], encoding="utf-8")

    img = np.frombuffer(base64.decodestring(img), dtype=dtype)
    img = img.reshape(_q['shape'])
    return img


def main():
    primary_model = get_model()
    while True:
        time.sleep(0.01)
        _queue = REDIS_DB.lrange(REDIS_QUEUE, 0, BATCH_SIZE - 1)
        for _q in _queue:
            all_features = {
                'primary': [],
                'object_bitmap': [0 for _ in range(len(labels_to_names_dict))]
            }
            _q = json.loads(_q.decode("utf-8"))
            img = decode_image(_q)

            all_features['secondary'] = get_inception_features(img.copy())

            img = preprocess_image(img)
            img, scale = resize_image(img)
            boxes, scores, labels = primary_model.predict_on_batch(
                np.expand_dims(img, axis=0))

            for box, score, label in zip(boxes[0], scores[0], labels[0]):
                if score < 0.5:
                    break
                box /= scale
                box = box.astype(int)
                x1, y1, x2, y2 = box[0], box[1], box[2], box[3]
                if(x2-x1 >= 75 and y2-y1 >= 75):
                    features = get_inception_features(img[x1:x2, y1:y2])
                    all_features['primary'].append({
                        'features': features,
                        'label': int(label),
                        'name': label_to_name(label)
                    })
                    all_features['object_bitmap'][label] = 1

            REDIS_DB.set(_q['id'], json.dumps(all_features))
        REDIS_DB.ltrim(REDIS_QUEUE, len(_queue), -1)


if __name__ == "__main__":
    print("Running extractor")
    main()
