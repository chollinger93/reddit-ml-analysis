from __future__ import print_function
import praw, time, json, config, os, hashlib

__author__ = "Christian Hollinger (otter-in-a-suit)"
__version__ = "0.1.0"
__license__ = "GNU GPLv3"


class DictEncoder(json.JSONEncoder):
    def default(self, obj):
        return obj.__dict__


class Post:
    def __init__(self, title, subreddit, author, upvotes, date_iso, link, type, num_comments, content):
        self.id = hashlib.md5((title + str(date_iso)).encode('utf-8')).hexdigest()
        self.title = title
        self.subreddit = subreddit
        self.author = author
        self.upvotes = upvotes
        self.date_iso = int(date_iso)
        self.link = link
        # self.date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(date_iso))
        self.type = type
        self.num_comments = num_comments
        self.content = content

    def get_csv(self):
        return "{subreddit}|{type}|\"{title}\"|{upvotes}|{num_comments}|\"{content}\"|{author}|{date}".format(
            subreddit=self.subreddit.encode('utf8'),
            type=self.type.encode('utf8'),
            title=self.title.encode('utf8'),
            upvotes=self.upvotes,
            num_comments=self.num_comments,
            content=self.content.encode('utf8'),
            author=self.author.encode('utf8'),
            date=self.date_iso)

    def __str__(self):
        return "{title}, upvotes: {up}, date: {date}, link: {link}, content: {content}".format(
            title=self.title.encode('utf8'),
            up=self.upvotes,
            date=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.date_iso)).encode('utf8'),
            link=self.link.encode('utf8'),
            content=self.content.encode('utf-8'))


def get_top_posts(subreddit, reddit, limit):
    # Store posts
    posts = []

    for submission in reddit.subreddit(subreddit).top(limit=limit):
        if submission.pinned:
            continue

        if submission.is_self and submission.selftext is not None:
            # Self post - text
            content = submission.selftext
            _type = 'self'
        elif submission.is_self and submission.selftext is None:
            # Self post - no header - askreddit etc.
            content = submission.title
            _type = 'question'
        elif submission.url is not None and submission.preview is not None and submission.preview.__len__ > 0 \
                and 'images' in submission.preview and submission.preview['images'].__len__ > 0:
            # External media - store preview if available
            content = submission.preview['images'][0].get('source').get('url')
            _type = 'extMedia'
        elif submission.url is not None and submission.media is not None:
            # External media
            content = submission.url
            _type = 'extMedia'
        elif submission.url is not None and submission.media is None:
            # External link
            if 'imgur' in submission.url or '.jpg' in submission.url or '.png' in submission.url or '.gif' in submission.url:
                _type = 'extMedia'
            else:
                _type = 'link'
            content = submission.url
        else:
            # Empty post
            content = None
            _type = 'none'

        post = Post(submission.title, submission.subreddit_name_prefixed, submission.author.name, submission.ups,
                    submission.created, submission.permalink,
                    _type, submission.num_comments, content)
        posts.append(post)
        print("title: {post}".format(post=post))

        # https://github.com/reddit-archive/reddit/wiki/API
        # Honor fair use terms - 60 requests per minute
        time.sleep(1)

    return posts


def write_json_gcp(_input=config.creddit['file'], _output=config.cgcp['file'], bucket_name=config.cgcp['bucket']):
    from google.cloud import storage
    # Instantiates a client
    storage_client = storage.Client()

    # Gets bucket
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(_output)

    # Upload
    blob.upload_from_filename(_input)
    print('Uploaded {} to {} in bucket {}'.format(_input, _output, bucket_name))


def main():
    # Get reddit instance
    reddit = praw.Reddit(client_id=config.creddit['client_id'],
                         client_secret=config.creddit['client_secret'],
                         user_agent=config.creddit['user_agent'])
    # Set GCP path
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.cgcp['api_key']
    LIMIT = config.limit

    # Define top subreddits
    csv = 'subreddit|type|title|upvotes|num_comments|content|author|date\n'
    subreddits = ['announcements', 'funny', 'AskReddit', 'todayilearned', 'science', 'worldnews', 'pics', 'IAmA',
                  'gaming', 'videos', 'movies', 'aww', 'Music', 'blog', 'gifs', 'news', 'explainlikeimfive',
                  'askscience',
                  'EarthPorn', 'books', 'television', 'mildlyinteresting', 'LifeProTips', 'Showerthoughts', 'space',
                  'DIY', 'Jokes', 'gadgets', 'nottheonion', 'sports', 'tifu', 'food', 'photoshopbattles',
                  'Documentaries',
                  'Futurology', 'history', 'InternetIsBeautiful', 'dataisbeautiful', 'UpliftingNews', 'listentothis',
                  'GetMotivated', 'personalfinance', 'OldSchoolCool', 'philosophy', 'Art', 'nosleep', 'WritingPrompts',
                  'creepy', 'TwoXChromosomes', 'Fitness', 'technology', 'WTF', 'bestof', 'AdviceAnimals', 'politics',
                  'atheism', 'interestingasfuck', 'europe', 'woahdude', 'BlackPeopleTwitter', 'oddlysatisfying',
                  'gonewild', 'leagueoflegends', 'pcmasterrace', 'reactiongifs', 'gameofthrones', 'wholesomememes',
                  'Unexpected',
                  'Overwatch', 'facepalm', 'trees', 'Android', 'lifehacks', 'me_irl', 'relationships', 'Games', 'nba',
                  'programming', 'tattoos', 'NatureIsFuckingLit', 'Whatcouldgowrong', 'CrappyDesign', 'dankmemes',
                  'nsfw', 'cringepics', '4chan', 'soccer', 'comics', 'sex', 'pokemon', 'malefashionadvice', 'NSFW_GIF',
                  'StarWars', 'Frugal', 'HistoryPorn', 'AnimalsBeingJerks', 'RealGirls', 'travel', 'buildapc',
                  'OutOfTheLoop']
    posts = []
    flat_json = ''
    # Enable for debugging
    # subreddits = ['pics']

    for subreddit in subreddits:
        flat_json = ''
        try:
            top_posts = get_top_posts(subreddit, reddit, LIMIT)
            posts = posts + top_posts

            for post in top_posts:
                csv += post.get_csv() + '\n'
                flat_json += json.dumps(post.__dict__) + '\n'

            if config.use_json_array == 'true':
                # Write back Json as array
                with open(config.creddit['file'], 'a') as file:
                    file.write(json.dumps([ob.__dict__ for ob in posts]))
            else:
                # Write back JSON one line at a time for DataFlow
                with open(config.creddit['file'], 'a') as file:
                    file.write(flat_json)
        except Exception as e:
            print(e)
            print('Encountered error, skipping record')
            continue

    write_json_gcp()


if __name__ == "__main__":
    main()
