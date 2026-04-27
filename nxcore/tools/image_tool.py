import base64
import hashlib

import cv2
import numpy as np


class ImageTool:

    @classmethod
    def _from_64(cls, img_input):
        img_bytes = base64.b64decode(img_input)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return None

        return img

    @classmethod
    def _to_64(cls, img, content_type='png'):
        _, buffer = cv2.imencode(f'.{content_type}', img)
        img_bytes = buffer.tobytes()
        return base64.b64encode(img_bytes).decode('utf-8')

    @classmethod
    def _gen_hash(cls, img_input):
        if isinstance(img_input, bytes):
            return hashlib.md5(img_input).hexdigest()
        else:
            return hashlib.md5(img_input.tobytes()).hexdigest()
