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

# Some emoji.
EMOJI_THUMBS_UP = "\U0001f44d"
EMOJI_THUMBS_DOWN = "\U0001f44e"
EMOJI_SHRUG = "¯\\_(\u30c4)_/¯"

# The maximum number of characters in a tweet.
MAX_TWEET_SIZE = 140


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
            # if tweet.text:
                # print("Decoding short tweet.")

            return tweet.text
        except KeyError:
            print("Malformed tweet: %s" % tweet)
            return None

    def get_tweet_link(self, tweet):
        """Creates the link URL to a tweet."""

        if not tweet:
            # print("No tweet to get link.")
            return None

        try:
            screen_name = tweet.user.screen_name
            id_str = tweet.id_str
        except KeyError:
            # print("Malformed tweet for link: %s" % tweet)
            return None

        link = TWEET_URL % (screen_name, id_str)

        return link

    def compile_opinion_text(self, companies):
        """Generates the text for a tweet."""

        # Find all distinct company names.
        names = []
        for company in companies:
            name = company["name"]
            if name not in names:
                names.append(name)

        # Collect the ticker symbols and sentiment scores for each name.
        tickers = {}
        sentiments = {}
        for name in names:
            tickers[name] = []
            for company in companies:
                if company["name"] == name:
                    ticker = company["ticker"]
                    tickers[name].append(ticker)
                    sentiment = company["sentiment"]
                    # Assuming the same sentiment for each ticker.
                    sentiments[name] = sentiment

        # Create lines for each name with sentiment emoji and ticker symbols.
        lines = []
        for name in names:
            sentiment_str = self.get_sentiment_emoji(sentiments[name])
            tickers_str = " ".join(["$%s" % t for t in tickers[name]])
            line = "%s %s %s" % (name, sentiment_str, tickers_str)
            lines.append(line)

        return lines

    def make_tweet_text(self, companies, link):
        """Generates the text for a tweet."""

        # Find all distinct company names.
        names = []
        for company in companies:
            name = company["name"]
            if name not in names:
                names.append(name)

        # Collect the ticker symbols and sentiment scores for each name.
        tickers = {}
        sentiments = {}
        for name in names:
            tickers[name] = []
            for company in companies:
                if company["name"] == name:
                    ticker = company["ticker"]
                    tickers[name].append(ticker)
                    sentiment = company["sentiment"]
                    # Assuming the same sentiment for each ticker.
                    sentiments[name] = sentiment

        # Create lines for each name with sentiment emoji and ticker symbols.
        lines = []
        for name in names:
            sentiment_str = self.get_sentiment_emoji(sentiments[name])
            tickers_str = " ".join(["$%s" % t for t in tickers[name]])
            line = "%s %s %s" % (name, sentiment_str, tickers_str)
            lines.append(line)

        # Combine the lines and eclipsing if necessary.
        lines_str = "\n".join(lines)
        size = len(lines_str) + 1 + len(link)
        if size > MAX_TWEET_SIZE:
            print("Eclipsing lines: %s" % lines_str)
            lines_size = MAX_TWEET_SIZE - len(link) - 2
            lines_str = "%s\u2026" % lines_str[:lines_size]

        # Combine the lines with the link.
        text = "%s\n%s" % (lines_str, link)

        return text

    def get_sentiment_emoji(self, sentiment):
        """Returns the emoji matching the sentiment."""

        if not sentiment:
            return EMOJI_SHRUG

        if sentiment > 0:
            return EMOJI_THUMBS_UP

        if sentiment < 0:
            return EMOJI_THUMBS_DOWN

        # print("Unknown sentiment: %s" % sentiment)
        return EMOJI_SHRUG

    def get_tweet(self, tweet_id):
        """Looks up metadata for a single tweet."""

        # Use tweet_mode=extended so we get the full text.
        status = self.twitter_api.get_status(tweet_id, tweet_mode="extended")
        if not status:
            # print("Bad status response: %s" % status)
            return None

        # Use the raw JSON, just like the streaming API.
        return status._json
