#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""yahoo.py - obtain company headlines from Yahoo Finance using Beautiful-Soup.

See README.md or https://github.com/nicholasadamou/stockmine
for more information.

Copyright (C) Nicholas Adamou 2019
stockmine is released under the Apache 2.0 license. See
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
    print(f"{OK} Yahoo Finance query: {query_url}")

    latest_headlines = []
    headline_links = []
    parsed_uri = urlparse.urljoin(query_url, '/')

    try:
        html = requests.get(query_url).text
        soup = BeautifulSoup(html, 'html.parser')

        headlines = soup.findAll('h3')
        print(f'{OK} Scrapped Headlines: {headlines}')

        links = soup.findAll('a')
        print(f'{OK} Scrapped Links: {links}')

        if headlines:
            latest_headlines.extend(
                (element.next.next.next.next, query_url)
                for element in headlines
            )
            print(f'{OK} Latest Headlines: {latest_headlines}')

        if follow_links:
            print(f"{WARNING} Following any link and scrapping its contents")
            if links:
                for element in links:
                    if '/news/' in element['href']:
                        link = parsed_uri.rstrip('/') + element['href']
                        headline_links.append(link)
                print(f'{OK} Links: {headline_links}')

        for link in headline_links:
            latest_headlines.extend((p, link) for p in crawl_page_text(link))
        print(f"{OK} Latest Headlines: {latest_headlines}")
    except requests.exceptions.RequestException as request_exception:
        print(f"{ERROR} Exception: can't crawl web-site ({request_exception})")
    return latest_headlines


def crawl_page_text(url):
    """Crawl a Yahoo Finance page for relevant text."""

    try:
        print(f"{OK} Using URL: {url}")

        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')

        paragraphs = soup.findAll('p')
        print(f"{OK} Scrapped paragraphs: {paragraphs}")

        if paragraphs:
            for n, p in enumerate(paragraphs, start=1):
                if n <= MAX_PARAGRAPHS and p.string is not None:
                    print(f"{OK} Crawling {p.string}")
                    yield p.string
    except requests.exceptions.RequestException as re:
        print(f"{ERROR} Exception: can't crawl web-site ({re})")


def request(symbol, url):
    """Makes a request to a web-server and returns its response."""

    # Add stock symbol to URL.
    query_url = re.sub("SYMBOL", symbol, url)
    print(f"{OK} Yahoo Finance query: {query_url}")

    try:
        response = requests.get(query_url).json()
    except (requests.HTTPError, requests.ConnectionError, requests.ConnectTimeout) as request_execption:
        print(
            f"{ERROR} Exception: Failed to retrieve data from {query_url} because: {request_execption}"
        )
        raise

    return response


def scrap_company_data(symbol):
    """Scraps Yahoo Finance for stock price data pertaining to a given ticker symbol."""

    # Obtain response from Yahoo Finance
    response = request(symbol=symbol, url=YAHOO_FINANCE_STOCK_QUERY_URL)

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

    # Obtain response from Yahoo Finance
    response = request(symbol=symbol, url=YAHOO_FINANCE_STOCK_NAME_QUERY_URL)

    return next(
        (
            {'name': company['name'], 'symbol': company['symbol']}
            for company in response['ResultSet']['Result']
            if company['symbol'] == symbol
        ),
        {},
    )
