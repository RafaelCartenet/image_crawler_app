import logging
from tools.mongo_handler import MongoAgent
import os
from datetime import datetime
import uuid
from urllib.request import urlretrieve


TEMP_IMAGES_PATH = '/usr/data/temp_images'
URL_PATH = '/usr/data/'

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def crawl_image(url):
    """
    Given an url, download the image and insert it in a temporary directory
    :param url: url to crawl image from
    :return:
    """
    try:
        # Generate unique id for filename
        unique_id = uuid.uuid1()

        # Define output path
        output_path = '%s/%s.png' % (TEMP_IMAGES_PATH, unique_id)

        # Download image
        urlretrieve(url, output_path)

    except:
        # Log error in insert_logs table
        logger.error('Could not process request: %s' % url)
        client.insert_log(
            result='fail',
            inserted_datetime=datetime.now()
        )


def crawl_images(urls):
    """
    Crawl bunch of images given a list of url.
    Each url is crawled once.
    :param urls:
    :return:
    """
    for url in urls:
        logger.error('Crawling url: %s' % url)
        crawl_image(url)


def load_urls(path):
    """
    Load urls file from a given path.
    :param path:
    :return:
    """
    # Loading urls from path
    data_path = path + 'urls.txt'
    with open(data_path, 'r') as f:
        raw_urls = f.readlines()

    # Cleaning
    urls = list(map(
        lambda k: k.split('\n')[0],
        raw_urls,
    ))

    return urls


def init_temp_dir(directory):
    """
    Create directory if does not exist
    :param directory:
    :return:
    """
    if not os.path.exists(directory):
        os.mkdir(directory)


if __name__ == '__main__':
    # Instantiate mongodb Agent
    client = MongoAgent('mongodb', 27017)

    # Create temp directory if does not exist
    init_temp_dir(TEMP_IMAGES_PATH)

    urls_to_crawl = load_urls(URL_PATH)

    # Main loop
    while True:
        crawl_images(urls=urls_to_crawl)
