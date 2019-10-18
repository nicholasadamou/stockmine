#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""yahoo.py - obtain company headlines from Yahoo Finance using Beautiful-Soup.

See REAdataME.md or https://github.com/nicholasadamou/stockflight
for more information.

Copyright (C) Nicholas Adamou 2019
stockflight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import re
import time

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse

import requests
from bs4 import BeautifulSoup

from logs import OK, ERROR, WARNING

# The URL for a GET request to Yahoo Finance. The string parameter is the ticker symbol of a given company.
YAHOO_FINANCE_QUERY_URL = "https://finance.yahoo.com/quote/%s/?p=%s"

# The URL to fetch stock price from, SYMBOL will be replaced with ticker symbol from CLI arguments.
YAHOO_FINANCE_STOCK_QUERY_URL = "https://query1.finance.yahoo.com/v8/finance/chart/SYMBOL?region=US&lang=en-US" \
                                "&includePrePost=false&interval=2m&range=5d&corsdataomain=finance.yahoo.com&.tsrc" \
                                "=finance"

# The URL to fetch a company's stock name from, SYMBOL will be replaced with ticker symbol from CLI arguments.
YAHOO_FINANCE_STOCK_NAME_QUERY_URL = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query=SYMBOL&region=1&lang=en"

# Maximum number of paragraphs to crawl on a Companies Yahoo Finance page.
MAX_PARAGRAPHS = 10


def scrap_yahoo_finance(ticker, follow_links=False):
    """Scrap Yahoo Finance for relevant company headlines using a given ticker symbol."""

    # add stock symbol to URL
    query_url = YAHOO_FINANCE_QUERY_URL % (ticker, ticker)
    print("%s Yahoo Finance query: %s" % (OK, query_url))

    latest_headlines = []
    headline_links = []
    parsed_uri = urlparse.urljoin(query_url, '/')

    try:
        request = requests.get(query_url)
        html = request.text
        soup = BeautifulSoup(html, 'html.parser')

        headlines = soup.findAll('h3')
        print('%s Scrapped Headlines: %s' % (OK, headlines))

        links = soup.findAll('a')
        print('%s Scrapped Links: %s' % (OK, links))

        if headlines:
            for element in headlines:
                latest_headlines.append((element.next.next.next.next, query_url))
            print('%s Latest Headlines: %s' % (OK, latest_headlines))

        if follow_links:
            print("%s Following any link and scrapping its contents" % WARNING)
            if links:
                for element in links:
                    if '/news/' in element['href']:
                        link = parsed_uri.rstrip('/') + element['href']
                        headline_links.append(link)
                print('%s Links: %s' % (OK, headline_links))

        for link in headline_links:
            for p in crawl_page_text(link):
                latest_headlines.append((p, link))
        print("%s Latest Headlines: %s" % (OK, latest_headlines))
    except requests.exceptions.RequestException as request_exception:
        print("%s Exception: can't crawl web-site (%s)" % (ERROR, request_exception))
        pass

    return latest_headlines


def crawl_page_text(url):
    """Crawl a Yahoo Finance page for relevant text."""

    try:
        print("%s Using URL: %s" % (OK, url))

        request = requests.get(url)

        html = request.text
        soup = BeautifulSoup(html, 'html.parser')

        paragraphs = soup.findAll('p')
        print("%s Scrapped paragraphs: %s" % (OK, paragraphs))

        if paragraphs:
            n = 1

            for p in paragraphs:
                if n <= MAX_PARAGRAPHS:
                    if p.string is not None:
                        print("%s Crawling %s" % (OK, p.string))
                        yield p.string
                n += 1
    except requests.exceptions.RequestException as re:
        print("%s Exception: can't crawl web-site (%s)" % (ERROR, re))
        pass


def scrap_company_data(symbol):
    """Scraps Yahoo Finance for stock price data pertaining to a given ticker symbol."""

    # Add stock symbol to URL.
    query_url = re.sub("SYMBOL", symbol, YAHOO_FINANCE_STOCK_QUERY_URL)
    print("%s Yahoo Finance query: %s" % (OK, query_url))

    try:
        response = requests.get(query_url).json()
    except (requests.HTTPError, requests.ConnectionError, requests.ConnectTimeout) as request_execption:
        print("%s Exception: Failed to retrieve data from %s because: %s" % (ERROR, query_url, request_execption))
        raise

    # Build dictionary containing results.
    data = {
        'symbol': response['chart']['result'][0]['meta']['symbol'],
        'date': time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()),  # time now in GMT (UTC)
        'last price': response['chart']['result'][0]['indicators']['quote'][0]['close'][-1],
        'low': response['chart']['result'][0]['indicators']['quote'][0]['low'][-1],
        'high': response['chart']['result'][0]['indicators']['quote'][0]['high'][-1],
        'volume': response['chart']['result'][0]['indicators']['quote'][0]['volume'][-1]
    }

    return {
        'symbol': data['symbol'],
        'date': data['date'],
        'last price': data['last price'],
        'low': data['low'],
        'high': data['high'],
        'volume': data['volume']
    }


def scrap_company_name(symbol):
    """Scraps Yahoo Finance for a company's name pertaining to a given ticker symbol."""

    # The dictionary containing the target company's name and ticker symbol.
    data = {}

    # Add stock symbol to URL.
    query_url = re.sub("SYMBOL", symbol, YAHOO_FINANCE_STOCK_NAME_QUERY_URL)
    print("%s Yahoo Finance query: %s" % (OK, query_url))

    try:
        response = requests.get(query_url).json()
    except (requests.HTTPError, requests.ConnectionError, requests.ConnectTimeout) as request_execption:
        print("%s Exception: Failed to retrieve data from %s because: %s" % (ERROR, query_url, request_execption))
        raise

    for company in response['ResultSet']['Result']:
        if company['symbol'] == symbol:
            # Build dictionary containing results.
            data = {
                'name': company['name'],
                'symbol': company['symbol']
            }

            # Exit loop because we found the target company's name and ticker symbol.
            break

    return data
