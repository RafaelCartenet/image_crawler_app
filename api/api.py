from flask import Flask, jsonify, send_file
from tools.mongo_handler import MongoAgent
from io import BytesIO


app = Flask(__name__)
client = MongoAgent('mongodb', 27017)


@app.route('/', methods=['GET'])
def index():
    """
    Index, returns the links to all images in database
    :return:
    """
    images = client.get_all_images_metadata()
    available = []
    for metadata in images:
        available.append(
            'http://0.0.0.0:5000/image/' + metadata['_id']
        )
    return jsonify(available)


@app.route('/image/<md5>')
def image(md5):
    """
    Returns an image according to its md5.
    :param md5:
    :return:
    """
    # Get the image from the database
    img = client.get_image_object(md5=md5)

    # In case image does not exist
    if not img:
        return jsonify('md5: %s not found in database' % md5)

    # Transform image to bytes and render
    img_io = BytesIO()
    img.save(img_io, 'PNG', mode='LA')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


@app.route('/monitoring', methods=['GET'])
def monitoring():
    """
    Returns all the logs regarding insertion
    :return:
    """
    # Get all logs from database
    logs = client.get_all_insert_logs()

    # Remove _id field: not serializable
    for log in logs:
        log.pop('_id')

    # json render
    return jsonify(logs)


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
