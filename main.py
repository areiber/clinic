import base64
import io
import os

import google.cloud.storage
import google.cloud.vision
from google.cloud.datastore
from flask import Flask, redirect, render_template, request

# Create a storage client.
storage_client = google.cloud.storage.Client()

# TODO (Developer): Replace this with your Cloud Storage bucket name.
bucket_name = 'hackclinic-192010.appspot.com'
bucket = storage_client.get_bucket(bucket_name)

# TODO (Developer): Replace this with the name of the local file to upload.
source_file_name = 'Local file to upload, for example ./file.txt'
blob = bucket.blob(os.path.basename(source_file_name))

# Upload the local file to Cloud Storage.
blob.upload_from_filename(source_file_name)

print('File {} uploaded to {}.'.format(
    source_file_name,
    bucket))

# Create a Vision client.
vision_client = google.cloud.vision.ImageAnnotatorClient()

# TODO (Developer): Replace this with the name of the local image
# file to analyze.
image_file_name = 'Local image to analyze, for example ./cat.jpg'
with io.open(image_file_name, 'rb') as image_file:
    content = image_file.read()

# Use Vision to label the image based on content.
image = google.cloud.vision.types.Image(content=content)
response = vision_client.label_detection(image=image)

print('Labels:')
for label in response.label_annotations:
    print(label.description)


app = Flask(__name__)


@app.route('/')
def homepage():
    # Create a Cloud Datastore client.
    datastore_client = datastore.Client()

    # Use the Cloud Datastore client to fetch information from Datastore about
    # each photo.
    query = datastore_client.query(kind='Photos')
    image_entities = list(query.fetch())    

    # Return a Jinja2 HTML template.
    return render_template('homepage.html', image_entities=image_entities)


@app.route('/upload_photo', methods=['GET', 'POST'])
def upload_photo():
    # Create a Cloud Storage client.
    storage_client = storage.Client()

    # Get the Cloud Storage bucket that the file will be uploaded to.
    bucket = storage_client.get_bucket(os.environ.get('CLOUD_STORAGE_BUCKET'))

    # Create a new blob and upload the file's content to Cloud Storage.
    photo = request.files['file']
    blob = bucket.blob(photo.filename)
    blob.upload_from_string(
            photo.read(), content_type=photo.content_type)

    # Make the blob publicly viewable.
    blob.make_public()
    image_public_url = blob.public_url
    
    # Create a Cloud Vision client.
    vision_client = vision.ImageAnnotatorClient()

    # Retrieve a Vision API response for the photo stored in Cloud Storage
    source_uri = 'gs://{}/{}'.format(os.environ.get('CLOUD_STORAGE_BUCKET'), blob.name)
    response = vision_client.annotate_image({
        'image': {'source': {'image_uri': source_uri}},
    })
    labels = response.label_annotations
    faces = response.face_annotations
    web_entities = response.web_detection.web_entities

    # Create a Cloud Datastore client
    datastore_client = datastore.Client()

    # The kind for the new entity
    kind = 'Photos'

    # The name/ID for the new entity
    name = blob.name

    # Create the Cloud Datastore key for the new entity
    key = datastore_client.key(kind, name)

    # Construct the new entity using the key. Set dictionary values for entity
    # keys image_public_url and label. If we are using python version 2, we need to convert
    # our image URL to unicode to save it to Datastore properly.
    entity = datastore.Entity(key)
    if sys.version_info >= (3, 0):
        entity['image_public_url'] = image_public_url
    else:
        entity['image_public_url'] = unicode(image_public_url, "utf-8")
    entity['label'] = labels[0].description

    # Save the new entity to Datastore
    datastore_client.put(entity)

    # Redirect to the home page.
    return render_template('homepage.html', labels=labels, faces=faces, web_entities=web_entities, public_url=image_public_url)


@app.errorhandler(500)
def server_error(e):
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)

