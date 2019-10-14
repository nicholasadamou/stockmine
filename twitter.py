#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""twitter.py - authenticate and retrieve tweets from Twitter using
Tweepy.

See README.md or https://github.com/nicholasadamou/stockflight
for more information.

Copyright (C) Nicholas Adamou 2019
stockflight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

from os import getenv

from re import findall

from tweepy import OAuthHandler
from tweepy import API

from logs import *

# The keys for the Twitter app we're using for API requests
# (https://apps.twitter.com/app/13239588). Read from environment variables.
TWITTER_CONSUMER_KEY = getenv("TWITTER_CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = getenv("TWITTER_CONSUMER_SECRET")

# The keys for the Twitter account we're using for API requests.
# Read from environment variables.
TWITTER_ACCESS_TOKEN = getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = getenv("TWITTER_ACCESS_TOKEN_SECRET")

# The URL pattern for links to tweets.
TWEET_URL = "https://twitter.com/%s/status/%s"


def get_tweet_link(tweet):
    """Creates the link URL to a tweet."""

    if not tweet:
        print("%s No tweet to get link." % WARNING)
        return None

    try:
        screen_name = tweet.user.screen_name
        id_str = tweet.id_str
    except KeyError:
        print("%s Malformed tweet for link: %s" % (ERROR, tweet))
        return None

    link = TWEET_URL % (screen_name, id_str)

    return link


def get_tweet_text(tweet):
    """Returns the full text of a tweet."""

    # The format for getting at the full text is different depending on
    # whether the tweet came through the REST API or the Streaming API:
    # https://dev.twitter.com/overview/api/upcoming-changes-to-tweets
    try:
        return tweet.text
    except KeyError:
        print("%s Malformed tweet: %s" % (ERROR, tweet))
        return None


class Twitter:
    """A helper for talking to Twitter APIs."""

    def __init__(self):
        self.twitter_auth = OAuthHandler(TWITTER_CONSUMER_KEY,
                                         TWITTER_CONSUMER_SECRET)
        self.twitter_auth.set_access_token(TWITTER_ACCESS_TOKEN,
                                           TWITTER_ACCESS_TOKEN_SECRET)

        self.twitter_api = API(auth_handler=self.twitter_auth)

    def search(self, query, count):
        """Returns a list of tweets (tweet) matching the query"""

        tweets = []

        # query (q=) of '*' returns all tweets
        for tweet in self.twitter_api.search(q=query, lang="en", count=count, result_type="mixed"):
            print("%s %s" % (OK, tweet.text))
            tweets.append(tweet)

        return tweets

    def get_tweet(self, tweet_id):
        """Looks up metadata for a single tweet."""

        # Use tweet_mode=extended so we get the full text.
        status = self.twitter_api.get_status(tweet_id, tweet_mode="extended")
        if not status:
            print("%s Bad status response: %s" % (ERROR, status))
            return None

        # Use the raw JSON, just like the streaming API.
        return status._json
