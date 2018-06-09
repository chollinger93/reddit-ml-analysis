from __future__ import absolute_import

import argparse
import json
import logging
import urllib
import sys
import apache_beam as beam
import os
import io
from apache_beam.io import ReadFromText
from apache_beam.io import WriteToText
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions
from apache_beam.options.pipeline_options import SetupOptions
from google.cloud import vision
from google.cloud.vision import types


class JsonCoder(object):
    def encode(self, x):
        return json.dumps(x, ensure_ascii=False).encode('utf8')

    def decode(self, x):
        return json.loads(x)


class Split(beam.DoFn):
    def process(self, record):

        _type = record['type']
        if _type == 'self' or _type == 'link':
            return [{
                'post': record,
                'image': None
            }]
        elif _type == 'extMedia':
            return [{
                'post': record,
                'image': record['content']
            }]
        else:
            return None


class img():
    def __init__(self, id, description, score, topicality):
        self.id = id
        if description is not None:
            self.description = description
        else:
            self.description = ''
        self.score = score
        self.topicality = topicality


class GetImage(beam.DoFn):
    def __init__(self, tmp, output, bucket):
        self.tmp_image_loc = tmp
        self.outputloc = output
        self.bucket = bucket

    def process(self, record):
        print('Image: ' + record['image'])
        tmpuri = self.tmp_image_loc + record['post']['id'] + '.jpg'
        # Download the image, upload to GCS
        urllib.urlretrieve(record['image'], tmpuri)
        return [{
            'uri': tmpuri,
            'post': record['post']
        }]


class StoreGcp(beam.DoFn):
    def __init__(self, output, bucket):
        self.outputloc = output
        self.bucket = bucket

    def write_gcp(self, _input, _output, bucket_name):
        from google.cloud import storage
        # Instantiates a client
        storage_client = storage.Client()
        # Gets bucket
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(_output)

        # Upload
        blob.upload_from_filename(_input)
        print('Uploaded {} to {} in bucket {}'.format(_input, _output, bucket_name))

    def read_gcs(self, filename, bucket_name):
        from google.cloud import storage
        # Instantiates a client
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)
        return bucket.get_blob(filename).download_as_string()

    def process(self, record):
        print(record['uri'])
        self.write_gcp(record['uri'], self.outputloc + record['post']['id'] + '.jpg', self.bucket)
        return record['uri']


class GetVisionApi(beam.DoFn):
    def read_image(self, filename):
        # The name of the image file to annotate
        file_name = os.path.join(
            os.path.dirname(__file__),
            filename)

        # Loads the image into memory
        with io.open(file_name, 'rb') as image_file:
            return image_file.read()

    def get_vision(self, filename, id):
        # c_image = self.read_gcs(filename, self.bucket)
        c_image = self.read_image(filename)
        client = vision.ImageAnnotatorClient()
        image = types.Image(content=c_image)
        # Performs label detection on the image file
        response = client.label_detection(image=image)
        labels = response.label_annotations

        # Transform the labels to a custom class we can parse as JSON
        label_dict = []
        for label in labels:
            label_dict.append(img(id, label.description, label.score, label.topicality))

        return label_dict

    def process(self, record):
        labels = self.get_vision(record['uri'], record['post']['id'])

        for label in labels:
            yield {
                'id': label.id,
                'description': label.description,
                'score': label.score,
                'topicality': label.topicality
            }


class GetPostBySubreddit(beam.DoFn):
    def process(self, record):
        print('Post: ' + record['post']['title'].encode('utf-8'))
        post = record['post']
        print(post)
        return [
            # (record['post']['subreddit'], record['post'])
            post
        ]


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input',
                        dest='input',
                        required=True,
                        help='Input file to process.')
    parser.add_argument('--output',
                        dest='output',
                        required=True,
                        help='Output to write results to.')
    parser.add_argument('--imgOutput',
                        dest='img_output',
                        required=True,
                        help='Image output to write results to.')
    parser.add_argument('--tmp',
                        dest='tmp',
                        required=False,
                        default='/tmp/',
                        help='Temporary location for images')
    parser.add_argument('--useBigQuery',
                        dest='use_bq',
                        required=False,
                        default=False,
                        help='Use BigQuery or local FS?')
    parser.add_argument('--bucket',
                        dest='bucket',
                        required=True,
                        help='Bucket name for images.')
    known_args, pipeline_args = parser.parse_known_args(argv)

    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = True

    if known_args.use_bq and pipeline_options.view_as(GoogleCloudOptions).project is None:
        parser.print_usage()
        print(sys.argv[0] + ': Error: argument --project is required')
        sys.exit(1)

    with beam.Pipeline(options=pipeline_options) as p:
        records = (
            p |
            ReadFromText(known_args.input, coder=JsonCoder()) |
            'Splitting records' >> beam.ParDo(Split())
        )

        image_uris = (
            records |
            'Filter images' >> beam.Filter(lambda record: record['image'] is not None) |
            'Get image' >> beam.ParDo(GetImage(known_args.tmp, 'images/', known_args.bucket))
        )

        images = (
            image_uris |
            'Get VisionAPI' >> beam.ParDo(GetVisionApi())
        )

        posts = (
            records |
            'Group Subreddits' >> beam.ParDo(GetPostBySubreddit())
            # | 'GroupByKey' >> beam.GroupByKey()
        )

        if known_args.use_bq:
            posts | 'Write to BQ' >> beam.io.WriteToBigQuery(
                known_args.output,
                schema='date_iso:INTEGER,author:STRING,type:STRING,title:STRING,subreddit:STRING,content:STRING,link:STRING,num_comments:INTEGER,upvotes:INTEGER,id:STRING',
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND)
        else:
            posts | 'Write to FS' >> WriteToText(known_args.output, coder=JsonCoder())

        if known_args.use_bq:
            images | 'Write images to BQ' >> beam.io.WriteToBigQuery(
                known_args.img_output,
                schema='id:STRING,description:STRING,score:FLOAT,topicality:FLOAT',
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND)
        else:
            images | 'Write images to FS' >> WriteToText(known_args.img_output, coder=JsonCoder())

        image_gcp = (
            image_uris |
            'Store images to GCP' >> beam.ParDo(StoreGcp('images/', known_args.bucket))
        )


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
