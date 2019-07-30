from flask import Flask, jsonify, send_file
from tools.mongo_handler import MongoAgent
from io import BytesIO


app = Flask(__name__)
client = MongoAgent('mongodb', 27017)


@app.route('/', methods=['GET'])
def index():
    images = client.get_all_images_metadata()
    available = []
    for metadata in images:
        available.append(
            'http://0.0.0.0:5000/image/' + metadata['_id']
        )
    return jsonify(available)


@app.route('/image/<md5>')
def image(md5):
    img = client.get_image_object(md5=md5)
    img_io = BytesIO()
    img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')


@app.route('/monitoring', methods=['GET'])
def monitoring():
    images = client.get_all_images_metadata()
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
