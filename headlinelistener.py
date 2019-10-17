#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""headlinelistener.py - listens for relevant headlines on Yahoo Finance about a company with a given frequency.

See README.md or https://github.com/nicholasadamou/stockflight
for more information.

Copyright (C) Nicholas Adamou 2019
stockflight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import re
import time
from datetime import datetime

import nltk

from analysis import Analysis
from logs import OK, WARNING
from yahoo import scrap_yahoo_finance

# Download the 'punkt' package for NLTK
# for tokenizing tweet text.
nltk.download('punkt')


class HeadlineListener:
    """Listens for relevant headlines on Yahoo Finance about a company with a given frequency."""

    def __init__(self, args, symbol=None, frequency=120, follow_links=False):
        self.args = args
        self.symbol = symbol
        self.follow_links = follow_links
        self.headlines = []
        self.frequency = frequency

        analysis = Analysis()

        if args.ignored_keywords:
            ignored_keywords = args.ignored_keywords.split(',')

        if args.required_keywords:
            required_keywords = args.required_keywords.split(',')

        while True:
            news_headlines = scrap_yahoo_finance(symbol, follow_links)

            for headline, url in news_headlines:
                if headline not in self.headlines:
                    self.headlines.append(headline)

                    # Output current headline.
                    date = datetime.utcnow().isoformat()
                    print("%s %s %s %s" % (OK, date, headline, url))

                    # Tokenize words for use with NLTK.
                    text_for_tokens = re.sub(
                        r"[%|$.,!:@]|\(|\)|#|\+|(``)|('')|\?|-", "", headline)
                    tokens = nltk.word_tokenize(text_for_tokens)
                    print("%s NLTK Tokens: %s" % (OK, str(tokens)))

                    if len(ignored_keywords) > 0:
                        # Make sure [tokens] does not contain any of the ignored NLTK tokens.
                        for token in ignored_keywords:
                            if token in tokens:
                                print("%s Token %s is IGNORED" % (WARNING, token))
                                continue

                    if len(required_keywords) > 0:
                        # Make sure [tokens] does contains all required NLTK tokens.
                        contains_token = False
                        for token in required_keywords:
                            if token in tokens:
                                contains_token = True
                                break

                        if not contains_token:
                            print("%s Text does not contain %s', skipping." %
                                  (WARNING, required_keywords))
                            continue

                    # Obtain sentiment.
                    sentiment = analysis.extract_sentiment(headline)
                    print("%s Using sentiment %s for %s" % (OK, sentiment, headline))

            print("%s Waiting %s seconds" % (WARNING, self.frequency))
            time.sleep(self.frequency)
