from __future__ import absolute_import

import argparse
import json
import logging
import urllib
import sys
import apache_beam as beam
from apache_beam.io import ReadFromText
from apache_beam.io import WriteToText
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions
from apache_beam.options.pipeline_options import SetupOptions


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


class GetImage(beam.DoFn):
    def __init__(self, tmp, output, bucket):
        self.tmp_image_loc = tmp
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

    def process(self, record):
        print('Image: ' + record['image'])
        tmpuri = self.tmp_image_loc + record['post']['id'] + '.jpg'
        urllib.urlretrieve(record['image'], tmpuri)
        self.write_gcp(tmpuri, self.outputloc + record['post']['id'] + '.jpg', self.bucket)
        return [
            tmpuri
        ]


class GetPostBySubreddit(beam.DoFn):
    def process(self, record):
        print('Post: ' + record['post']['title'].encode('utf-8'))
        return [
            # (record['post']['subreddit'], record['post'])
            (record['post'])
        ]


class BuildSchema(beam.DoFn):
    def process(self, record):
        dict_ = {}
        _input = record['post']
        dict_['id'] = _input['id']
        dict_['date_iso'] = int(_input['date_iso'])
        dict_['author'] = _input['author']
        dict_['type'] = _input['type']
        dict_['title'] = _input['title']
        dict_['subreddit'] = _input['subreddit']
        dict_['content'] = _input['content']
        dict_['link'] = _input['link']
        dict_['num_comments'] = int(_input['num_comments'])
        dict_['upvotes'] = int(_input['upvotes'])
        dict_['date_str'] = _input['date_str']
        return [dict_]


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

        images = (
            records |
            'Filter images' >> beam.Filter(lambda record: record['image'] is not None) |
            'Get image' >> beam.ParDo(GetImage(known_args.tmp, 'images/', known_args.bucket))
        )

        posts = (
            records |
            'Group Subreddits' >> beam.ParDo(GetPostBySubreddit())
            # | 'GroupByKey' >> beam.GroupByKey()
        )

        # 'Build schema' >> beam.ParDo(BuildSchema()) |
        if known_args.use_bq:
            posts | 'Write to BQ' >> beam.io.WriteToBigQuery(
                known_args.output,
                schema='date_iso:INTEGER,author:STRING,type:STRING,title:STRING,subreddit:STRING,content:STRING,link:STRING,num_comments:INTEGER,upvotes:INTEGER,id:STRING',
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND)
        else:
            posts | 'Write to FS' >> WriteToText(known_args.output, coder=JsonCoder())


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
