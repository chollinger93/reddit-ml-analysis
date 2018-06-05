# Reddit Analysis
Simple Python scripts that reads the top posts from popular subreddits and stores them as JSON. JSONs will be uploaded to Google Cloud storage.

This is a work-in progress project for my [blog](https://otter-in-a-suit.com/blog).

### Prerequisites
* Python 2.7.3

## Install
Install dependencies:

```
pip install --upgrade google-cloud-storage
pip install --upgrade praw
```

## Configuration

```
cp config_example.py config.py
vim config.py
```

Set your reddit API and GCP keys here. Create the GCS bucket before via the Cloud Console.

## Run
Simply run `python Main.py` from your Cloud Shell or local machine.


## License
This project is licensed under the GNU GPLv3 License - see the [LICENSE](LICENSE) file for details.