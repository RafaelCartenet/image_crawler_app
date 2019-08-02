from PIL import Image
import hashlib


def load_image(path):
    """
    Load image from path to PIL Image Object.
    :param path: string, path of image
    :return:
    """
    return Image.open(path)


def compute_md5(pil_img):
    """
    Compute md5 of a PIL Image Object
    :param pil_img: PIL Image Object
    :return:
    """
    return hashlib.md5(pil_img.tobytes()).hexdigest()


def get_image_metadata(pil_img):
    """
    Compute metadata from PIL Image object.
    Get shape and computes md5
    :param pil_img: PIL Image Object
    :return:
    """
    metadata = {
        'width': pil_img.width,
        'height': pil_img.height,
        'md5': compute_md5(pil_img)
    }
    return metadata


def gray_scale(pil_img):
    """
    Given a PIL Image Object, transform it to gray scale, using native conversion.
    :param pil_img: PIL Image Object
    :return:
    """
    pil_img = pil_img.convert('LA')
    return pil_img
