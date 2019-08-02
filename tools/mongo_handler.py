from pymongo import MongoClient
from PIL import Image
import gridfs
import datetime


class MongoAgent(MongoClient):

    def __init__(self, host, port):
        super(MongoAgent, self).__init__(
            host=host,
            port=port
        )
        self.db = self.image_database
        self.fs = gridfs.GridFS(self.db)

    # GET METHODS
    def get_image_metadata_by_md5(self, md5):
        """
        Get image metadata object based on an md5.
        :param md5:
        :return:
        """
        image_metadata = self.db.images.find_one(
            {'_id': {'$eq': md5}}
        )
        return image_metadata

    def get_bytes_image(self, image_id):
        """
        Loads bytes image from gridfs based on its _id in the gridfs
        :param image_id:
        :return:
        """
        return self.fs.get(file_id=image_id)

    def get_one_image_metadata(self):
        """
        Gets one random image metadata object
        :return:
        """
        return self.db.images.find_one()

    def get_all_images_metadata(self):
        """
        Gets all images metadata objects
        :return:
        """
        return list(
            self.db.images.find({})
        )

    def get_all_insert_logs(self):
        return list(
            self.db.insert_logs.find({})
        )

    def get_image_object(self, md5):
        """
        Given an md5, loads the associated image back to a PIL Image object.
        Returns None if no image is found.
        :param md5:
        :return:
        """
        # Load metadata from md5
        metadata = self.get_image_metadata_by_md5(md5)

        # Return None if no image was found
        if not metadata:
            return None

        # Load image as bytes
        bytes_img = self.get_bytes_image(metadata['image_id']).read()

        # Get image shape
        shape = (metadata['width'], metadata['height'])

        # Load image object from bytes to PIL object
        img = Image.frombytes('LA', shape, bytes_img)
        return img

    # CHECK METHODS
    def image_exists(self, md5):
        """
        Check if an image exists with the associated md5, used as _id.
        :param md5:
        :return:
        """
        return self.db.images.find_one(
            {'_id': {'$eq': md5}}
        ) is not None

    def interval_exists(self, log_datetime):
        """
        Check if an interval exists in the database.
        :param log_datetime: datetime.datetime
        :return:
        """
        return self.db.insert_logs.find_one(
            {'interval': {'$eq': log_datetime}}
        )

    # INSERT METHODS
    def insert_image(self, image, metadata):
        """
        Inserts a PIL Image object as bytes into the mongodb.
        Using Gridfs.
        :param image: PIL image
        :param metadata: image metadata
        :return:
        """
        # Transform PIL image to bytes
        image_as_bytes = image.tobytes()

        if self.image_exists(metadata['md5']):
            raise ValueError("image already exists")

        # Insert bytes image into gridfs, keep inserted reference
        image_id = self.fs.put(
            image_as_bytes,
            filename=metadata['md5']
        )
        inserted_datetime = datetime.datetime.now()

        # Insert metadata into db.images, adding gridfs link
        metadata['image_id'] = image_id
        metadata['insert_time'] = inserted_datetime
        metadata['_id'] = metadata.pop('md5')
        inserted_id = self.db.images.insert_one(metadata).inserted_id

        return inserted_id, inserted_datetime, image_id

    def insert_log(self, result, inserted_datetime):
        """
        Main method to insert log in database.
        :param result: string, "fail" or "success"
        :param inserted_datetime: datetime.datetime of the log
        :return:
        """
        # Round inserted datetime to minute.
        interval = inserted_datetime.replace(
            second=0,
            microsecond=0
        )

        # Adding collection for specific interval if does not exist
        if not self.interval_exists(interval):
            self.create_interval(interval)
            return

        # Update collection
        query = {'interval': interval}
        new_values = {'$inc': {result: 1}}
        self.db.insert_logs.update(
            query,
            new_values
        )

    def create_interval(self, interval):
        """
        Create a blank interval object inside database.
        :param interval:
        :return:
        """
        document = {
            'success': 0,
            'fail': 0,
            'interval': interval,

        }
        self.db.insert_logs.insert_one(document)
