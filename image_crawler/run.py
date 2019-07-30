import time
import logging
from image_processing import get_image_metadata, url_to_pil_image
from tools.mongo_handler import MongoAgent


def crawl_image(url):
    im = url_to_pil_image(url)
    metadata = get_image_metadata(im)
    metadata['source_url'] = url
    insert_id, _ = client.insert_image(im, metadata)
    logging.error('inserted image: %s' % insert_id)


def crawl_images(urls):
    """
    Crawl bunch of images given a list of url.
    Each url is crawled once.
    :param urls:
    :return:
    """
    for url in urls:
        crawl_image(url)
        return


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


if __name__ == '__main__':
    # Instantiate mongodb Agent
    client = MongoAgent('mongodb', 27017)

    # path = '../data/'
    url_path = '/usr/data/'

    urls_to_crawl = load_urls(url_path)

    while True:
        crawl_images(urls=urls_to_crawl)
        time.sleep(3)
