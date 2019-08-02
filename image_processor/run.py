import time
from tools.mongo_handler import MongoAgent
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from image_processing import get_image_metadata, gray_scale, load_image
import logging
import os
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class ImagesHandler(FileSystemEventHandler):

    @staticmethod
    def delete_temp_image(path):
        """
        Delete file from path.
        :param path:
        :return:
        """
        os.remove(path)

    @staticmethod
    def insert_image(img, metadata):
        """
        Insert PIL Image object according to its metadata.
        :param img: PIL Image object
        :param metadata: dict, image's metadata
        :return:
        """
        try:
            insert_id, insert_datetime, _ = client.insert_image(img, metadata)
            logger.error('Inserted image: %s' % insert_id)
            client.insert_log(
                result='success',
                inserted_datetime=insert_datetime
            )

        except ValueError:
            logger.error('Image already exists.')
            client.insert_log(
                result='fail',
                inserted_datetime=datetime.now()
            )

    def process_temp_image(self, img):
        """
        Process a PIL Image object:
        - get metadata (including md5)
        - switch mode to gray scale
        - insert it to database
        :param img:
        :return:
        """
        # Get raw image metadata
        metadata = get_image_metadata(img)

        # Transform to gray scale
        img = gray_scale(img)

        # Insert image
        self.insert_image(img, metadata)

    def on_created(self, event):
        """
        Event triggered when a new file is created inside the watched directory.
        Loads the image, delets it from the temp directory, process it and insert it
        in the database.
        :param event: information regarding newly created file
        :return:
        """
        # Found file's path
        path = event.src_path

        # If the image is something else than an image, we stop here
        extension = path.split('.')[-1]
        if extension != 'png':
            return

        logger.info('found file: %s' % path)

        # Load image from path as a PIL Image object
        img = load_image(path)

        self.delete_temp_image(path)

        self.process_temp_image(img)

        # Delete object
        del img


if __name__ == '__main__':
    # Instantiate mongodb Agent
    client = MongoAgent('mongodb', 27017)

    # Instantiate watchdog event handler
    observer = Observer()
    event_handler = ImagesHandler()
    observer.schedule(event_handler, path='/usr/data/temp_images/')
    observer.start()

    # Main loop
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
