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
import time
from os import getenv
from random import randint

from py_dotenv import read_dotenv

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse

import requests
from bs4 import BeautifulSoup
from tweepy import OAuthHandler, Stream, TweepError
from tweepy import API

from logs import *
from twitterlistener import API_RETRY_DELAY_S, API_RETRY_COUNT, API_RETRY_ERRORS, TwitterListener

# Read API keys
try:
    read_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
except FileNotFoundError:
    print("\n%s '.env' does not exist. Please create the file & add the necessary API keys to it." % ERROR)
    exit(1)

# The keys for the Twitter app we're using for API requests
# (https://apps.twitter.com/app/13239588). Read from environment variables.
TWITTER_CONSUMER_KEY = getenv('TWITTER_CONSUMER_KEY')
TWITTER_CONSUMER_SECRET = getenv('TWITTER_CONSUMER_SECRET')

# The keys for the Twitter account we're using for API requests.
# Read from environment variables.
TWITTER_ACCESS_TOKEN = getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = getenv('TWITTER_ACCESS_TOKEN_SECRET')

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


def get_twitter_users_from_file(file):
    """Returns a list of Twitter user ID's from a file."""

    # Get Twitter User IDs from file.
    users = []
    print("%s Grabbing any Twitter User IDs from file: %s" % (OK, file))

    try:
        f = open(file, "rt", encoding='utf-8')

        for user in f.readlines():
            users.append(user.rstrip())
        print("%s FOUND USERS: %s" % (OK, users))

        f.close()
    except (IOError, OSError) as e:
        print("%s Exception: Error opening file %s caused by: %s" % (ERROR, file, e))
        pass

    return users


def scrap_twitter_users_from_url(url):
    """Scraps a list of Twitter user ID's from a URL."""

    # Get Twitter User IDs from file.
    users = []
    print("%s Grabbing any Twitter User IDs from URL: %s" % (OK, url))

    try:
        urls = ("http://twitter.com/", "http://www.twitter.com/",
                "https://twitter.com/", "https://www.twitter.com/")

        request = requests.get(url)
        html = request.text
        soup = BeautifulSoup(html, 'html.parser')

        links = []
        for link in soup.findAll('a'):
            links.append(link.get('href'))

        if links:
            for link in links:

                # Check if twitter_url in link.
                parsed_uri = urlparse.urljoin(link, '/')

                # Get Twitter user name from link and add to list.
                if parsed_uri in urls and "=" not in link and "?" not in link:
                    user = link.split('/')[3]
                    users.append(u'@' + user)

            print("%s FOUND USERS: %s" % (OK, users))
    except requests.exceptions.RequestException as re:
        print("%s Requests Exception: can't crawl web-site (%s)" % re)
        pass

    return users


def stream_user_feeds(twitter, stream, target, users):
    """Stream a list of Twitter Users' FEEDs."""

    # Make sure we have Twitter User IDs
    if len(users) == 0:
        print("%s No Twitter User IDs found in %s" % (ERROR, target))
        sys.exit(1)

    # Build Twitter User ID list by accessing the Twitter API.
    print("%s Building Twitter User ID list from %s" % (WARNING, users))
    user_ids = []
    while True:
        for user in users:
            try:
                # Get user ID from screen_name using Twitter API.
                user = twitter.get_user(screen_name=user)
                screen_name = user.screen_name
                id = int(user.id)

                if id not in users:
                    print("%s Obtained [@%s:%s]" % (OK, screen_name, id))
                    user_ids.append(str(id))

                time.sleep(randint(0, 2))
            except TweepError as te:
                # Sleep a bit in case Twitter suspends us.
                print("%s Tweepy Exception: %s" % (ERROR, te))
                print("%s Sleeping for a random amount of time and retrying." % WARNING)
                time.sleep(randint(1, 10))
                continue
            except KeyboardInterrupt:
                print("\n%s Ctrl-c keyboard interrupt, exiting." % WARNING)
                stream.disconnect()
                sys.exit(0)
        break

    # Search for tweets containing a list of keywords.
    print("%s Following %s Twitter FEEDs" % (WARNING, users))
    stream.filter(follow=user_ids, languages=['en'])


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

                # Append list of required NLTK tokens to [keywords].
                if args.required_keywords:
                    required_keywords = args.required_keywords.split(',')
                    keywords.append(required_keywords)

                print("%s Searching for tweets containing %s" % (WARNING, keywords))
                twitter_stream.filter(track=keywords, languages=['en'])
            except TweepError:
                print("%s Twitter API error %s" % (ERROR, TweepError))
            except KeyboardInterrupt:
                print("\n%s Ctrl-c keyboard interrupt, exiting." % WARNING)
                twitter_stream.disconnect()
                sys.exit(0)
        elif args.file:
            try:
                # Obtain a list of Twitter User IDs from file.
                file = args.file
                users = get_twitter_users_from_file(file)

                # Stream a list of Twitter users' FEEDs.
                print("%s Searching for tweets from %s" % (WARNING, users))
                stream_user_feeds(twitter=self.twitter_api, stream=twitter_stream, target=file, users=users)
            except TweepError:
                print("%s Twitter API error %s" % (ERROR, TweepError))
            except KeyboardInterrupt:
                print("\n%s Ctrl-c keyboard interrupt, exiting." % WARNING)
                twitter_stream.disconnect()
                sys.exit(0)
        elif args.url:
            try:
                # Obtain a list of Twitter User IDs from URL.
                url = args.url
                users = scrap_twitter_users_from_url(url)

                # Stream a list of Twitter users' FEEDs.
                print("%s Searching for tweets from %s" % (WARNING, users))
                stream_user_feeds(twitter=self.twitter_api, stream=twitter_stream, target=url, users=users)
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
