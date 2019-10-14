#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""wiki.py - obtain company data from Wikidata API using
a SPARQL query.

See README.md or https://github.com/nicholasadamou/stockflight
for more information.

Copyright (C) Nicholas Adamou 2019
stockflight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

from urllib.parse import quote_plus

from requests import get

from logs import *

# The URL for a GET request to the Wikidata API. The string parameter is the
# SPARQL query.
WIKIDATA_QUERY_URL = "https://query.wikidata.org/sparql?query=%s&format=JSON"

# A Wikidata SPARQL query to find stock ticker symbols and other information
# for a company. The string parameter is the Freebase ID of the company.
MID_TO_TICKER_QUERY = (
    'SELECT ?companyLabel ?rootLabel ?tickerLabel ?exchangeNameLabel'
    ' WHERE {'
    '  ?entity wdt:P646 "%s" .'  # Entity with specified Freebase ID.
    '  ?entity wdt:P176* ?manufacturer .'  # Entity may be product.
    '  ?manufacturer wdt:P1366* ?company .'  # Company may have restructured.
    '  { ?company p:P414 ?exchange } UNION'  # Company traded on exchange ...
    '  { ?company wdt:P127+ / wdt:P1366* ?root .'  # ... or company has owner.
    '    ?root p:P414 ?exchange } UNION'  # Owner traded on exchange or ...
    '  { ?company wdt:P749+ / wdt:P1366* ?root .'  # ... company has parent.
    '    ?root p:P414 ?exchange } .'  # Parent traded on exchange.
    '  VALUES ?exchanges { wd:Q13677 wd:Q82059 } .'  # Whitelist NYSE, NASDAQ.
    '  ?exchange ps:P414 ?exchanges .'  # Stock exchange is whitelisted.
    '  ?exchange pq:P249 ?ticker .'  # Get ticker symbol.
    '  ?exchange ps:P414 ?exchangeName .'  # Get name of exchange.
    '  FILTER NOT EXISTS { ?company wdt:P31 /'  # Exclude newspapers.
    '                               wdt:P279* wd:Q11032 } .'
    '  FILTER NOT EXISTS { ?company wdt:P31 /'  # Exclude news agencies.
    '                               wdt:P279* wd:Q192283 } .'
    '  FILTER NOT EXISTS { ?company wdt:P31 /'  # Exclude news magazines.
    '                               wdt:P279* wd:Q1684600 } .'
    '  FILTER NOT EXISTS { ?company wdt:P31 /'  # Exclude radio stations.
    '                               wdt:P279* wd:Q14350 } .'
    '  FILTER NOT EXISTS { ?company wdt:P31 /'  # Exclude TV stations.
    '                               wdt:P279* wd:Q1616075 } .'
    '  FILTER NOT EXISTS { ?company wdt:P31 /'  # Exclude TV channels.
    '                               wdt:P279* wd:Q2001305 } .'
    '  SERVICE wikibase:label {'
    '   bd:serviceParam wikibase:language "en" .'  # Use English labels.
    '  }'
    ' } GROUP BY ?companyLabel ?rootLabel ?tickerLabel ?exchangeNameLabel'
    ' ORDER BY ?companyLabel ?rootLabel ?tickerLabel ?exchangeNameLabel')


def make_wikidata_request(query):
    """Makes a request to the Wikidata SPARQL API."""

    query_url = WIKIDATA_QUERY_URL % quote_plus(query)
    print("%s Wikidata query: %s" % (OK, query_url))

    response = get(query_url)

    try:
        response_json = response.json()
    except ValueError:
        print("%s Failed to decode JSON response: %s" % (ERROR, response))
        return None

    print("%s Wikidata response: %s" % (OK, response_json))

    try:
        results = response_json["results"]
        bindings = results["bindings"]
    except KeyError:
        print("%s Malformed Wikidata response: %s" % (ERROR, response_json))
        return None

    return bindings


def get_company_data(mid):
    """Looks up stock ticker information for a company via its Freebase ID."""

    query = MID_TO_TICKER_QUERY % mid
    bindings = make_wikidata_request(query)

    if not bindings:
        if mid:
            print("%s No company data found for MID: %s" % (WARNING, mid))
        return None

    # Collect the data from the response.
    companies = []
    for binding in bindings:
        try:
            name = binding["companyLabel"]["value"]
        except KeyError:
            name = None

        try:
            root = binding["rootLabel"]["value"]
        except KeyError:
            root = None

        try:
            ticker = binding["tickerLabel"]["value"]
        except KeyError:
            ticker = None

        try:
            exchange = binding["exchangeNameLabel"]["value"]
        except KeyError:
            exchange = None

        company = {"name": name,
                   "ticker": ticker,
                   "exchange": exchange}

        # Add the root if there is one.
        if root and root != name:
            company["root"] = root

        # Add to the list unless we already have the same entry.
        if company not in companies:
            print("%s Adding company data: %s" % (OK, company))
            companies.append(company)
        else:
            print("%s Skipping duplicate company data: %s" % (WARNING, company))

    return companies
