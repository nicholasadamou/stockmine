import os
from os import getenv
from py_dotenv import read_dotenv

from tweepy import OAuthHandler
from tweepy import API

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
read_dotenv(dotenv_path)

# The keys for the Twitter account we're using for API requests and tweeting
# alerts (@Tweet2Stocks). Read from environment variables.
TWITTER_ACCESS_TOKEN = getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = getenv("TWITTER_ACCESS_TOKEN_SECRET")

# The keys for the Twitter app we're using for API requests
# (https://apps.twitter.com/app/13239588). Read from environment variables.
TWITTER_CONSUMER_KEY = getenv("TWITTER_CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = getenv("TWITTER_CONSUMER_SECRET")

# The URL pattern for links to tweets.
TWEET_URL = "https://twitter.com/%s/status/%s"


class Twitter:
    """A helper for talking to Twitter APIs."""

    def __init__(self):
        self.twitter_auth = OAuthHandler(TWITTER_CONSUMER_KEY,
                                         TWITTER_CONSUMER_SECRET)
        self.twitter_auth.set_access_token(TWITTER_ACCESS_TOKEN,
                                           TWITTER_ACCESS_TOKEN_SECRET)

        self.twitter_api = API(auth_handler=self.twitter_auth)

    def search(self, company, number):
        """Returns a list of tweets (tweet) containing a company's ticker-symbol"""

        tweets = []

        for tweet in self.twitter_api.search(q=company, lang="en", count=number, result_type="mixed"):
            tweets.append(tweet)

        return tweets

    def get_tweet_text(self, tweet):
        """Returns the full text of a tweet."""

        # The format for getting at the full text is different depending on
        # whether the tweet came through the REST API or the Streaming API:
        # https://dev.twitter.com/overview/api/upcoming-changes-to-tweets
        try:
            if tweet.text:
                print("Decoding short tweet.")

            return tweet.text
        except KeyError:
            print("Malformed tweet: %s" % tweet)
            return None

    def get_tweet_link(self, tweet):
        """Creates the link URL to a tweet."""

        if not tweet:
            print("No tweet to get link.")
            return None

        try:
            screen_name = tweet.user.screen_name
            id_str = tweet.id_str
        except KeyError:
            print("Malformed tweet for link: %s" % tweet)
            return None

        link = TWEET_URL % (screen_name, id_str)

        return link
