import base64
import hashlib
from typing import Any, Optional

import cv2
import numpy as np


class ImageTool:
    """Utility class for image processing, base64 conversion, and hashing."""

    @classmethod
    def from_64(cls, img_input: str) -> Optional[np.ndarray]:
        """Converts a base64 encoded image string to an OpenCV image (numpy array).

        Args:
            img_input (str): Base64 encoded image string.

        Returns:
            np.ndarray or None: OpenCV image if decoding is successful, otherwise None.
        """
        img_bytes = base64.b64decode(img_input)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return None
        return img

    @classmethod
    def to_64(cls, img: np.ndarray, content_type: str = 'png') -> str:
        """Converts an OpenCV image (numpy array) to a base64 encoded image string.

        Args:
            img (np.ndarray): OpenCV image to convert.
            content_type (str, optional): Target file format extension. Defaults to 'png'.

        Returns:
            str: Base64 encoded image string.
        """
        _, buffer = cv2.imencode(f'.{content_type}', img)
        img_bytes = buffer.tobytes()
        return base64.b64encode(img_bytes).decode('utf-8')

    @classmethod
    def gen_hash(cls, img_input: Any) -> str:
        """Generates an MD5 hash of raw image bytes or numpy array.

        Args:
            img_input (bytes or np.ndarray): Raw bytes or OpenCV image.

        Returns:
            str: MD5 hex digest string.
        """
        if isinstance(img_input, bytes):
            return hashlib.md5(img_input).hexdigest()
        else:
            return hashlib.md5(img_input.tobytes()).hexdigest()

    # Backward compatibility aliases
    _from_64 = from_64
    _to_64 = to_64
    _gen_hash = gen_hash
