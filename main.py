    import io
    import os

    import google.cloud.storage
    import google.cloud.vision

    # Create a storage client.
    storage_client = google.cloud.storage.Client()

    # TODO (Developer): Replace this with your Cloud Storage bucket name.
    bucket_name = 'Name of a bucket, for example my-bucket'
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
