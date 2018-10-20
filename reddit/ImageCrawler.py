# encoding=utf8
from __future__ import print_function

import config
import os
import praw
import urllib
import re

from reddit.Main import get_top_posts
from reddit.Main import Post

__author__ = "Christian Hollinger (otter-in-a-suit)"
__version__ = "0.1.0"
__license__ = "GNU GPLv3"


def unixify(path):
    return re.sub('[^\w\-_\. ]', '_', path)


def get_image(post, img_path):
    filename = unixify(post.title)
    tmp_uri = '{}{}'.format(img_path, filename)
    print('Saving {url} as {tmp}'.format(url=post.content, tmp=tmp_uri))
    urllib.urlretrieve(post.content, tmp_uri)
    return tmp_uri, filename


def write_gcp(_input, _output, bucket_name):
    from google.cloud import storage
    # Instantiates a client
    storage_client = storage.Client()

    # Gets bucket
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(_output)

    # Upload
    blob.upload_from_filename(_input)

    print('Uploading {} to bucket {}'.format(_output, bucket_name))


def csv_prep(gcs_loc):
    return '{gcs_loc}|\n'.format(gcs_loc=gcs_loc).encode('utf-8')


def main():
    import sys
    reload(sys)
    sys.setdefaultencoding('utf8')

    # Get reddit instance
    reddit = praw.Reddit(client_id=config.creddit['client_id'],
                         client_secret=config.creddit['client_secret'],
                         user_agent=config.creddit['user_agent'])
    # Set GCP path
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.cgcp['api_key']
    LIMIT = config.limit
    bucket_name = config.cgcp['images']

    # Settings
    subreddit=config.crawler['subreddit']
    img_path=config.crawler['path']+subreddits

    # Get top posts
    top_posts = get_top_posts(subreddit, reddit, LIMIT)

    # Filter images
    images = filter(lambda p: p.type == 'extMedia', top_posts)

    csv = ''
    # Download images
    for post in images:
        tmp, filename = get_image(post, img_path)
        write_gcp(tmp, subreddit + '/' + filename, bucket_name)
        csv += csv_prep('gs://{bucket_name}/{subreddit}/{filename}'
                        .format(bucket_name=bucket_name, subreddit=subreddit, filename=filename))

    # Dump pre-classifier CSV
    with open(img_path+'images.csv', 'a') as file:
        file.write(csv)


if __name__ == "__main__":
    main()
