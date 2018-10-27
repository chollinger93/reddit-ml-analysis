import sys

from google.cloud import automl_v1beta1
from google.cloud.automl_v1beta1.proto import service_pb2

"""
This code snippet requests a image classification from a custom AutoML Model
Usage: python2 automl_rest.py $img $project $model_id
"""

def get_prediction(_content, project_id, model_id):
    prediction_client = automl_v1beta1.PredictionServiceClient()

    name = 'projects/{}/locations/us-central1/models/{}'.format(project_id, model_id)
    payload = {'image': {'image_bytes': _content }}
    params = {}
    request = prediction_client.predict(name, payload, params)
    return request  # waits till request is returned


if __name__ == '__main__':
    file_path = sys.argv[1]
    project_id = sys.argv[2]
    model_id = sys.argv[3]

    with open(file_path, 'rb') as ff:
        _content = ff.read()

    print(get_prediction(_content, project_id,  model_id))