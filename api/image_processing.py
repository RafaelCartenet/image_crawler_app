import requests
from PIL import Image
import cv2
from io import StringIO
import hashlib
import numpy as np
import urllib

# file_name = 'urls.txt'
#
# with open(file_name, 'r') as f:
#     urls = f.readlines()
#
# urls = map(
#     lambda k: k.split('\n')[0],
#     urls
# )


def url_to_image(url):
    # download the image, convert it to a NumPy array, and then read
    # it into OpenCV format
    resp = urllib.request.urlopen(url)
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)

    # return the image
    return image


def load_image(url):
    try:
        r = requests.get(url)
    except:
        print('could not load image from url: %s' % url)
        return None
    return r.content


def interpret_image(request_content):
    im = Image.open(StringIO(request_content))
    return im


def get_image_metadata(img):
    height, width, channels = img.shape
    metadata = {
        'width': width,
        'height': height,
        'md5': hashlib.md5(img).hexdigest()
    }
    return metadata


def rgb2gray(rgb):
    return np.dot(rgb[..., :3], [1/3, 1/3, 1/3])


# im = interpret_image(load_image(urls[0]))

# print(im)

# array = np.array(im)
#
# print(array.shape)
#
# gray_array = rgb2gray(array)
#
# print(gray_array.shape)
#
# print(get_image_metadata(im))
#
# new_im = Image.fromarray([gray_array])
#
# new_im.show()
#
#
# # for k, url in enumerate(urls):
# #     log_string = '#%s/%s\t' % (k, len(urls))
#     # print(log_string)
#     # load_image(url)






