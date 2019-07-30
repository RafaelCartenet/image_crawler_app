from pymongo import MongoClient
import gridfs
import datetime
from pprint import pprint

from bson.binary import Binary
from bson import ObjectId

import pickle


class MongoAgent(MongoClient):

    def __init__(self, host, port):
        super(MongoAgent, self).__init__(
            host=host,
            port=port
        )
        self.db = self.image_database
        self.fs = gridfs.GridFS(self.db)

    def insert_image(self, image, metadata):
        binary = Binary(pickle.dumps(image, protocol=2), subtype=128)

        image_id = self.fs.put(
            binary,
            filename=metadata['md5']
        )

        metadata['image_id'] = image_id
        inserted_id = self.db.images.insert_one(metadata).inserted_id
        return inserted_id, image_id

    def get_image_by_md5(self, md5):
        image_metadata = self.db.images.find_one(
            {'md5': {'$eq': md5}}
        )
        return self.fs.get(file_id=image_metadata['image_id'])

    def load_image(self, image_id):
        binary = self.fs.get(image_id).read()
        return pickle.loads(binary, encoding='bytes')

    def get_one_image(self):
        return self.db.images.find_one()

    def get_all_images(self):
        return list(
            self.db.images.find({})
        )


if __name__ == '__main__':
    client = MongoAgent('localhost', 27017)


    post = {
        "author": "Bob",
        "text": "My first bob post!",
        "tags": ["mongodb", "pymongo"],
        "date": datetime.datetime.utcnow()
    }
    from image_processing import load_image, interpret_image, get_image_metadata, url_to_image


    # DOWNLOADING IMAGE
    url = 'https://picsum.photos/441/442'
    im = url_to_image(url)
    metadata = get_image_metadata(im)
    md5 = metadata['md5']
    #
    # # INSERTING IMAGE
    # binary_before = Binary(pickle.dumps(im)) #, subtype=128)  #, protocol=2
    insert_id, image_id = client.insert_image(im, metadata)
    out=pickle.loads(client.get_image_by_md5(md5).read(), encoding='bytes')

    import cv2
    out = cv2.imencode('.png', out)
    out.show()
    print(type(out))
    cv2.imencode('.png', img)[1].tobytes()


    assert()

    # LOADING IMAGE
    # print(image_id, type(image_id))
    # im_back = client.get_image(image_id=image_id)
    # im1 = client.get_image_by__id("5d3f4e26b7643f5bbd18b979")
    im2 = client.get_image_by_md5("1851b54ab313c103175d5d32dfdec22f")
    img = client.load_image(im2['imageID'])
    print(img)

    print(im2)
    # assert()
    # import cv2
    # cv2.imshow("Color Image", im1)
    # cv2.imshow("Color Image", im2)
    # cv2.imshow("Color Image", im3)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # im_from_md5 = client.get_image_md5(md5)
    # print(binary_before == im_from_md5)

    # print(im)
    # print(im_back)
    print(im == im_back)
    print(im == im_from_md5)

