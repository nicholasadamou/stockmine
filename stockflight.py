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
import inquirer
import re

from py_dotenv import read_dotenv
from pyfiglet import Figlet

from logs import *
from anaylsis import Analysis, write2csv

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

    analysis = Analysis()

    # Ask the user to enter a target Ticker Symbol (e.g. $AAPL)
    questions = [
        inquirer.Text('ticker', message="Enter a Ticker Symbol (e.g. $AAPL)",
                      validate=lambda _, x: re.match(r'\$[A-Z]{1,4}', x),
                      ),
        inquirer.Text('numberOfTweets', message="Enter a number of tweets to analyze"),
    ]

    # Obtain user's response to questions
    answers = inquirer.prompt(questions)

    ticker = answers['ticker']
    numberOfTweets = answers['numberOfTweets']

    print()

    print("%s Analyzing %s tweet(s) for mentions of %s" % (WARNING, numberOfTweets, ticker))
    print()

    # Get tweets pertaining to a given company.
    tweets = analysis.twitter.search(ticker, numberOfTweets)

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

        if len(tweets) > 1:
            print()

    if data:
        # Write results to csv.
        write2csv(data)

    print("\n%s Done" % SUCCESS)
