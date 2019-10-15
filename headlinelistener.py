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

    def __init__(self, symbol=None, frequency=120, follow_links=False):
        self.symbol = symbol
        self.follow_links = follow_links
        self.headlines = []
        self.frequency = frequency

        analysis = Analysis()

        while True:
            news_headlines = scrap_yahoo_finance(symbol, follow_links)

            for headline, url in news_headlines:
                if headline not in self.headlines:
                    self.headlines.append(headline)

                    # Output current headline
                    date = datetime.utcnow().isoformat()
                    print("%s %s %s %s" % (OK, date, headline, url))

                    # Tokenize words for use with NLTK
                    text_for_tokens = re.sub(
                        r"[%|$.,!:@]|\(|\)|#|\+|(``)|('')|\?|-", "", headline)
                    tokens = nltk.word_tokenize(text_for_tokens)
                    print("%s NLTK Tokens: %s" % (OK, str(tokens)))

                    # Obtain sentiment
                    sentiment = analysis.extract_sentiment(headline)
                    print("%s Using sentiment %s for %s" % (OK, sentiment, headline))

            print("%s Waiting %s seconds" % (WARNING, self.frequency))
            time.sleep(self.frequency)
