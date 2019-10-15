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
import os
import sys
from os import getenv

from py_dotenv import read_dotenv
from tweepy import OAuthHandler, Stream, TweepError
from tweepy import API

from logs import *
from twitterlistener import API_RETRY_DELAY_S, API_RETRY_COUNT, API_RETRY_ERRORS, TwitterListener

# Read API keys
try:
    read_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
except FileNotFoundError:
    print("\n%s .env does not exist. Please create the file & add the necessary API keys to it." % ERROR)
    exit(1)

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
        screen_name = tweet['user']['screen_name']
        id_str = tweet['id_str']
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
        return tweet['text']
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

        self.twitter_api = API(auth_handler=self.twitter_auth,
                               retry_count=API_RETRY_COUNT,
                               retry_delay=API_RETRY_DELAY_S,
                               retry_errors=API_RETRY_ERRORS,
                               wait_on_rate_limit=True,
                               wait_on_rate_limit_notify=True)

    def start_streaming(self, args, callback):
        """Starts streaming tweets and returning data to the callback."""

        self.twitter_listener = TwitterListener(callback=callback)

        twitter_stream = Stream(self.twitter_auth, self.twitter_listener)

        if args.keywords:
            try:
                # Search for tweets containing a list of keywords.
                keywords = args.keywords.split(',')
                print("%s Searching for tweets containing %s" % (WARNING, keywords))
                twitter_stream.filter(track=keywords, languages=['en'])
            except TweepError:
                print("%s Twitter API error %s" % (ERROR, TweepError))
            except KeyboardInterrupt:
                print("\n%s Ctrl-c keyboard interrupt, exiting." % WARNING)
                twitter_stream.disconnect()
                sys.exit(0)

        # If we got here because of an API error, raise it.
        if self.twitter_listener and self.twitter_listener.get_error_status():
            raise Exception("Twitter API error: %s" %
                            self.twitter_listener.get_error_status())

        return twitter_stream

    def stop_streaming(self):
        """Stops the current stream."""

        if not self.twitter_listener:
            print("%s No stream to stop." % WARNING)
            return

        self.twitter_listener.stop_queue()
        self.twitter_listener = None

    def get_tweet(self, tweet_id):
        """Looks up metadata for a single tweet."""

        # Use tweet_mode=extended so we get the full text.
        status = self.twitter_api.get_status(tweet_id, tweet_mode="extended")
        if not status:
            print("%s Bad status response: %s" % (ERROR, status))
            return None

        # Use the raw JSON, just like the streaming API.
        return status._json
