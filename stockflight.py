#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""stockflight.py - main driver program of stockflight.

See README.md or https://github.com/nicholasadamou/stockflight
for more information.

Copyright (C) Nicholas Adamou 2019
stockflight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import os
import argparse
import re
import sys
from time import sleep
from datetime import datetime
from os import getenv

import nltk as nltk

from py_dotenv import read_dotenv
from pyfiglet import Figlet

from headlinelistener import HeadlineListener
from logs import *
from analysis import Analysis
from monitor import Monitor
from twitter import Twitter
from yahoo import scrap_company_data

STOCKFLIGHT_VERSION = '0.1a'
__version__ = STOCKFLIGHT_VERSION

if sys.version_info >= (3, 0):
    unicode = str

# Download the 'punkt' package for NLTK
# for tokenizing tweet text.
nltk.download('punkt')

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

# The duration of the smallest backoff step in seconds.
BACKOFF_STEP_S = 0.1

# The maximum number of retry steps, equivalent to 0.1 * (2^12 - 1) = 409.5
# seconds of total delay. This is the largest interval that one backoff
# sequence may take.
MAX_TRIES = 12

# The time in seconds after which to reset a backoff sequence. This is the
# smallest interval at which backoff sequences may repeat normally.
BACKOFF_RESET_S = 30 * 60


class Main:
    """A wrapper for the main application logic and retry loop."""

    def __init__(self):
        self.twitter = Twitter()

    def twitter_callback(self, tweet):
        """Analyzes tweets"""

        # Start analysis.
        analysis = Analysis()

        # create tokens of words in text using NLTK.
        text_for_tokens = re.sub(r"[%|$.,!:@]|\(|\)|#|\+|(``)|('')|\?|-", "", tweet['text'])
        tokens = nltk.word_tokenize(text_for_tokens)
        print("%s NLTK Tokens: %s" % (OK, str(tokens)))

        # strip out hash-tags for language processing.
        text = re.sub(r"[#|@$]\S+", "", tweet['text']).strip()
        tweet['text'] = text
        print('%s Strip Hash-tags from text: %s' % (OK, tweet['text']))

        # Find any mention of companies in tweet.
        companies = analysis.find_companies(tweet)

        if not companies:
            print("%s Didn't find any mention to any known publicly traded companies." % ERROR)
            return

        # Analyze a tweet & obtain its sentiment.
        results = analysis.analyze(companies)

        print("%s %s" % (OK, results))

    def run_session(self, args):
        """Runs a single streaming session. Logs and cleans up after
        exceptions.
        """

        print("%s Starting new session." % WARNING)
        self.twitter.start_streaming(args, self.twitter_callback)

    def backoff(self, tries):
        """Sleeps an exponential number of seconds based on the number of
        tries.
        """

        delay = BACKOFF_STEP_S * pow(2, tries)
        print("%s Waiting for %.1f seconds." % (WARNING, delay))
        sleep(delay)

    def run(self, args):
        """Runs the main retry loop with exponential backoff."""

        tries = 0
        while True:

            # The session blocks until an error occurs.
            self.run_session(args)

            # Remember the first time a backoff sequence starts.
            now = datetime.now()
            if tries == 0:
                print("%s Starting first backoff sequence." % WARNING)
                backoff_start = now

            # Reset the backoff sequence if the last error was long ago.
            if (now - backoff_start).total_seconds() > BACKOFF_RESET_S:
                print("%s Starting new backoff sequence." % OK)
                tries = 0
                backoff_start = now

            # Give up after the maximum number of tries.
            if tries >= MAX_TRIES:
                print("%s Exceeded maximum retry count." % WARNING)
                break

            # Wait according to the progression of the backoff sequence.
            self.backoff(tries)

            # Increment the number of tries for the next error.
            tries += 1


if __name__ == "__main__":
    # Print banner and app description
    custom_fig = Figlet(font='shadow')
    print(custom_fig.renderText('StockFlight'))
    print("Crowd-sourced stock analyzer and stock predictor using\n"
          "Google Natural Language Processing API, Twitter, and\n"
          "Wikidata API in order to determine, if at all, how much\n"
          "emotions can effect a stock price?\n")

    print("%s TWITTER_CONSUMER_KEY = %s" % (OK, TWITTER_CONSUMER_KEY))
    print("%s TWITTER_CONSUMER_SECRET = %s" % (OK, TWITTER_CONSUMER_SECRET))
    print("%s TWITTER_ACCESS_TOKEN = %s" % (OK, TWITTER_ACCESS_TOKEN))
    print("%s TWITTER_ACCESS_TOKEN_SECRET = %s" % (OK, TWITTER_ACCESS_TOKEN_SECRET))
    print()

    # parse CLI arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--keywords", metavar="KEYWORDS",
                        help="Use keywords to search for in Tweets instead of feeds. "
                             "Separated by comma, case insensitive, spaces are ANDs commas are ORs. "
                             "Example: TSLA,'Elon Musk',Musk,Tesla,SpaceX")
    parser.add_argument("-s", "--symbol", metavar="SYMBOL",
                        help="Stock symbol to use when fetching stock data., example: TSLA")
    parser.add_argument("-n", "--news-headlines", action="store_true",
                        help="Get news headlines instead of Twitter using stock symbol, example: TSLA")
    parser.add_argument("-f", "--frequency", metavar="FREQUENCY", default=120, type=int,
                        help="How often in seconds to retrieve news headlines (default: 120 sec)")
    parser.add_argument("--follow-links", action="store_true",
                        help="Follow links on news headlines and scrape relevant text from landing page")
    parser.add_argument("-V", "--version", action="version",
                        version="stockflight v%s" % STOCKFLIGHT_VERSION,
                        help="Prints version and exits")
    args = parser.parse_args()

    # Print help if no arguments are given.
    if len(sys.argv) == 1:
        parser.print_help()

    # Handle CLI arguments

    # python3 stockflight.py -k TSLA,'Elon Musk',Musk,Tesla,SpaceX
    if args.keywords:
        monitor = Monitor()
        monitor.start()

        try:
            Main().run(args)
        finally:
            monitor.stop()
    else:
        # python3 stockflight.py --symbol TSLA
        if args.symbol and not args.news_headlines:
            symbol = args.symbol

            results = scrap_company_data(symbol)
            print("%s FOUND DATA for %s: %s" % (OK, symbol, results))

        # python3 stockflight.py --news-headlines --follow-links --symbol TSLA --frequency 120
        elif args.symbol and args.news_headlines and args.follow_links:
            symbol = args.symbol
            frequency = args.frequency

            try:
                news_listener = HeadlineListener(symbol=symbol, frequency=frequency, follow_links=args.follow_links)
            except KeyboardInterrupt:
                print("%s Ctrl-c keyboard interrupt, exiting." % WARNING)
                sys.exit(0)

        # python3 stockflight.py --news-headlines --symbol TSLA --frequency 120
        elif args.symbol and args.news_headlines and not args.follow_links:
            symbol = args.symbol
            frequency = args.frequency

            try:
                news_listener = HeadlineListener(symbol=symbol, frequency=frequency)
            except KeyboardInterrupt:
                print("%s Ctrl-c keyboard interrupt, exiting." % WARNING)
                sys.exit(0)
