#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""analysis.py - analyze tweets on Twitter mentioning any publicly traded companies.

See README.md or https://github.com/nicholasadamou/stockmine
for more information.

Copyright (C) Nicholas Adamou 2019
stockmine is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import csv

from google.cloud import language

from twitter import get_tweet_link

from logs import *
from wiki import get_company_data

# Some emoji.
EMOJI_THUMBS_UP = "\U0001f44d"
EMOJI_THUMBS_DOWN = "\U0001f44e"
EMOJI_SHRUG = "¯\\_(\u30c4)_/¯"


def entity_tostring(entity):
    """Converts one GNL (Google Natural Language) entity to a readable string."""

    metadata = ", ".join(['"%s": "%s"' % (key, value) for
                          key, value in entity.metadata.items()])

    mentions = ", ".join(['"%s"' % mention for mention in entity.mentions])

    return ('{name: "%s",'
            ' type: "%s",'
            ' metadata: {%s},'
            ' salience: %s,'
            ' mentions: [%s]}') % (
               entity.name,
               entity.type,
               metadata,
               entity.salience,
               mentions)


def entities_tostring(entities):
    """Converts a list of GNL (Google Natural Language) entities to a readable string."""

    return f'[{", ".join([entity_tostring(entity) for entity in entities])}]'


def get_sentiment_emoji(sentiment):
    """Returns the emoji matching the sentiment."""

    if not sentiment:
        return EMOJI_SHRUG

    if sentiment > 0:
        return EMOJI_THUMBS_UP

    if sentiment < 0:
        return EMOJI_THUMBS_DOWN

    print(f"{ERROR} Unknown sentiment: {sentiment}")
    return EMOJI_SHRUG


def compile_opinion_text(name, symbol, sentiment):
    """Generates an opinion on a tweet."""

    return f"{name} {get_sentiment_emoji(sentiment)} {symbol}"


def write2csv(file_name, results, targets):
    """Writes results to [.csv] file."""

    print('\n%s Writing results to %s' % (WARNING, file_name))

    f = csv.writer(open(file_name, "w"))

    # Write headers
    if ",".join(targets) not in open(file_name).read():
        f.writerow(targets)

    # Write individual values
    f.writerow([",".join([str(e) for e in results.values()])])


class Analysis:
    """A helper for analyzing company data in text."""

    def __init__(self):
        self.language_client = language.LanguageServiceClient()

    def find_companies(self, tweet):
        """Finds any mention of companies in a tweet."""

        if not tweet:
            print(f"{WARNING} No tweet to find companies.")
            return None

        text = tweet['text']
        if not text:
            print(f"{WARNING} Failed to get text from tweet: {tweet}")
            return None

        # Run entity detection.
        document = language.types.Document(
            content=text,
            type=language.enums.Document.Type.PLAIN_TEXT,
            language="en")
        entities = self.language_client.analyze_entities(document).entities
        print(f"{OK} Found entities: {entities_tostring(entities)}")

        # Collect all entities which are publicly traded companies, i.e.
        # entities which have a known stock ticker symbol.
        companies = []

        for entity in entities:
            # Use the Freebase ID of the entity to find company data. Skip any
            # entity which doesn't have a Freebase ID (unless we find one via
            # the Twitter handle).
            name = entity.name
            metadata = entity.metadata
            try:
                mid = metadata["mid"]
            except KeyError:
                if name:
                    print(f"No MID found for entity: {name}")
                continue

            company_data = get_company_data(mid)

            # Skip any entity for which we can't find any company data.
            if not company_data:
                if name and mid:
                    print(f"{WARNING} No company data found for entity: {name} ({mid})")
                continue
            print(f"{OK} Found company data: {company_data}")

            for company in company_data:
                # Append & attach metadata associated with a company.
                company["tweet"] = text
                company["url"] = get_tweet_link(tweet)

                # Add to the list unless we already have the same entry.
                names = [existing["name"] for existing in companies]
                if company["name"] not in names:
                    companies.append(company)
                else:
                    print(f"{WARNING} Skipping company with duplicate name: {company}")

                break

        return companies

    def extract_sentiment(self, text):
        """Extracts a sentiment score [-1, 1] from text
        using Google Natural Language API."""

        if not text:
            print(f"{WARNING} No sentiment for empty text.")
            return 0

        document = language.types.Document(
            content=text,
            type=language.enums.Document.Type.PLAIN_TEXT,
            language="en")
        sentiment = self.language_client.analyze_sentiment(
            document).document_sentiment

        print("%s Sentiment score and magnitude for text: %s %s \"%s\"" % (
            OK, sentiment.score, sentiment.magnitude, text))

        return sentiment.score

    def analyze(self, companies):
        """Attach a sentiment score & opinion to each company found."""

        results = {}

        for company in companies:
            # Extract and add a sentiment score.
            sentiment = self.extract_sentiment(company['tweet'])
            print(f"{WARNING} Using sentiment for company: {sentiment} {company}")
            results[company['symbol']] = {'sentiment': sentiment}

            # Should we invest in $TICKER?
            opinion = compile_opinion_text(company['name'], company['symbol'], sentiment)
            print(f'{WARNING} {opinion}')
            results[company['symbol']].update({'opinion': opinion})

        return results
