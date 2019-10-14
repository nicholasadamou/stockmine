#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""stockflight.py - main driver program of stockflight.

See README.md or https://github.com/nicholasadamou/stockflight
for more information.

Copyright (C) Nicholas Adamou 2019
stockflight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""
import argparse
import os
import sys

import inquirer
import re

from py_dotenv import read_dotenv
from pyfiglet import Figlet

from logs import *
from anaylsis import Analysis, write2csv

STOCKFLIGHT_VERSION = '0.1a'
__version__ = STOCKFLIGHT_VERSION

IS_PY3 = sys.version_info >= (3, 0)

if IS_PY3:
    unicode = str

if __name__ == "__main__":
    # Print banner and app description
    custom_fig = Figlet(font='shadow')
    print(custom_fig.renderText('StockFlight'))
    print("Crowd-sourced stock analyzer and stock predictor using\n"
          "Google Natural Language Processing API, Twitter, and\n"
          "Wikidata API in order to determine, if at all, how much\n"
          "emotions can effect a stock price?")

    # Read API keys
    try:
        read_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
    except FileNotFoundError:
        print("\n%s .env does not exist. Please create the file & add the necessary API keys to it." % ERROR)
        exit(1)

    # parse CLI arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--keywords", metavar="KEYWORDS",
                        help="Use keywords to search for in Tweets instead of feeds. "
                             "Separated by comma, case insensitive, spaces are ANDs commas are ORs. "
                             "Example: TSLA,'Elon Musk',Musk,Tesla,SpaceX")
    parser.add_argument("--count", metavar="COUNT", default=120, type=int,
                        help="How many tweets to analyze (default: 120)")
    parser.add_argument("-V", "--version", action="version",
                        version="stockflight v%s" % STOCKFLIGHT_VERSION,
                        help="Prints version and exits")
    args = parser.parse_args()

    analysis = Analysis()

    if args.keywords and args.count:
        print("%s Analyzing %s tweet(s) for mentions of %s\n" % (WARNING, args.count, args.keywords))

        # Get tweets pertaining to a given company.
        tweets = analysis.twitter.search(args.keywords, args.count)

        data = []
        for tweet in tweets:
            # Find any mention of companies in tweet.
            companies = analysis.find_companies(tweet)

            if not companies:
                print("%s Didn't find any mention to any known publicly traded companies." % ERROR)
                continue

            # Analyze a tweet & obtain its sentiment.
            results = analysis.analyze(companies)

            print("%s %s" % (OK, results))

            # Add to results.
            data += results

            # Prettify output.
            if len(tweets) > 1:
                print()

        if data:
            # Write results to csv.
            write2csv(data)

    print("\n%s Done" % SUCCESS)
