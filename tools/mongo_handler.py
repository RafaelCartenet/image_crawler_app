from pymongo import MongoClient
import gridfs
import datetime
from PIL import Image


class MongoAgent(MongoClient):

    def __init__(self, host, port):
        super(MongoAgent, self).__init__(
            host=host,
            port=port
        )
        self.db = self.image_database
        self.fs = gridfs.GridFS(self.db)

    def image_exists(self, md5):
        """
        Check if an image exists with the associated md5, used as _id.
        :param md5:
        :return:
        """
        return self.db.images.find_one(
            {'_id': {'$eq': md5}}
        ) is not None

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
        insert_time = datetime.datetime.now()

        # Insert metadata into db.images, adding gridfs link
        metadata['image_id'] = image_id
        metadata['insert_time'] = insert_time
        metadata['_id'] = metadata.pop('md5')
        inserted_id = self.db.images.insert_one(metadata).inserted_id

        return inserted_id, image_id

    def get_image_by_md5(self, md5):
        image_metadata = self.get_image_metadata_by_md5(md5)
        return self.load_bytes_image(
            image_id=image_metadata['image_id']
        )

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

    def load_bytes_image(self, image_id):
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

    def get_image_object(self, md5):
        """
        Given an md5, loads the associated image back to a PIL Image object.
        :param md5:
        :return:
        """
        # Load metadata from md5
        metadata = self.get_image_metadata_by_md5(md5)

        # Load image as bytes
        bytes_img = self.load_bytes_image(metadata['image_id']).read()

        # Get image shape
        shape = (metadata['width'], metadata['height'])

        # Load image object from bytes to PIL object
        img = Image.frombytes('RGB', shape, bytes_img)
        return img
