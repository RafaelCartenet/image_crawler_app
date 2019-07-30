from flask import Flask, Response, jsonify, make_response
from mongo_handler import MongoAgent
# import cv2
# import base64

app = Flask(__name__)
client = MongoAgent('mongodb', 27017)


def load_data():
    data_path = '/usr/data/test.txt'
    with open(data_path, 'r') as f:
        data = f.readlines()
    return jsonify(data)


def load_image(md5):
    return client.get_image_by_md5(md5)
    # return mongo.send_file(metadata['imageID'])
    # retval, buffer = cv2.imencode('.png', img)
    # png_as_text = base64.b64encode(buffer)
    # response = make_response(png_as_text)
    # response.headers['Content-Type'] = 'image/png'
    # return response


@app.route('/', methods=['GET'])
def index():
    return load_data()


@app.route('/image/<md5>')
def image(md5):
    img = client.get_image_by_md5(md5=md5)
    data = cv2.imencode('.png', img)[1].tobytes()
    return Response(data)
    # return load_image(md5)
    # response = load_image(md5)
    # response.content_type = 'image/jpeg'
    # return response


@app.route('/monitoring', methods=['GET'])
def monitoring():
    images = client.get_all_images()
    for im in images:
        im.pop('_id')
        im.pop('imageID')
    return jsonify(images)


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
