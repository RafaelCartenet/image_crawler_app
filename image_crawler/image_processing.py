from PIL import Image
import hashlib
import numpy as np
import urllib.request as urllib


def url_to_pil_image(url):
    """
    Load an image to a PIL Image object from an url.
    :param url:
    :return:
    """
    return Image.open(urllib.urlopen(url))


def get_image_metadata(pil_img):
    """
    Compute metadata from PIL Image object.
    Get shape and computes md5
    :param pil_img:
    :return: 
    """
    metadata = {
        'width': pil_img.width,
        'height': pil_img.height,
        'md5': hashlib.md5(pil_img.tobytes()).hexdigest()
    }
    return metadata


def rgb2gray(rgb):
    return np.dot(rgb[..., :3], [1/3, 1/3, 1/3])







