import csv

from google.cloud import language

from datetime import date

from urllib.parse import quote_plus

from requests import get

from re import findall

from twitter import Twitter, get_tweet_link

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


def entity_tostring(entity):
    """Converts one entity to a readable string."""

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
    """Converts a list of entities to a readable string."""

    return "[%s]" % ", ".join([entity_tostring(entity) for entity in entities])


def write2csv(ticker, results):
    file_name = ticker + "_" + date.today().strftime("%d-%m-%Y") + ".csv"

    print('\n%s Writing results to %s' % (WARNING, file_name))

    f = csv.writer(open(file_name, "w"))

    header = ['ticker', 'name', 'sentiment', 'opinion',  'tweet', 'url']
    f.writerow(header)

    for company in results:
        f.writerow([company['ticker'], company['name'], company['sentiment'],
                    company['opinion'], company['tweet'], company['url']])


def get_company_data(mid):
    """Looks up stock ticker information for a company via its Freebase ID.
    """

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


class Analysis:
    """A helper for analyzing company data in text."""

    def __init__(self):
        self.language_client = language.LanguageServiceClient()
        self.twitter = Twitter()

    def obtain_results(self, tweet):
        """Finds & analyzes mentions of companies in a tweet."""

        if not tweet:
            print("%s No tweet to find companies." % WARNING)
            return None

        text = tweet.text
        if not text:
            print("%s Failed to get text from tweet: %s" % (WARNING, tweet))
            return None

        # Run entity detection.
        document = language.types.Document(
            content=text,
            type=language.enums.Document.Type.PLAIN_TEXT,
            language="en")
        entities = self.language_client.analyze_entities(document).entities
        print("%s Found entities: %s" % (OK, entities_tostring(entities)))

        # Collect all entities which are publicly traded companies, i.e.
        # entities which have a known stock ticker symbol.
        results = []
        print("%s companies: %s" % (OK, findall(r"\$[A-Z]{1,4}", text)))

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
                    print("No MID found for entity: %s" % name)
                continue

            company_data = get_company_data(mid)

            # Skip any entity for which we can't find any company data.
            if not company_data:
                if name and mid:
                    print("%s No company data found for entity: %s (%s)" % (WARNING, name, mid))
                continue
            print("%s Found company data: %s" % (OK, company_data))

            for company in company_data:
                # Extract and add a sentiment score.
                sentiment = self.get_sentiment(text)
                # print("Using sentiment for company: %s %s" % (sentiment, company))
                company["sentiment"] = sentiment
                company["tweet"] = text
                company["url"] = get_tweet_link(tweet)

                # Add the company to the list unless we already have the same
                # name, ticker, and that its not from the NASDAQ.
                names = [existing["name"] for existing in results]
                tickers = [existing["ticker"] for existing in results]
                if not company["name"] in names \
                    and not company["ticker"] in tickers:
                    results.append(company)
                else:
                    print("%s Skipping company with duplicate name and ticker: %s" % (WARNING, company))

                break

        return results

    def get_sentiment(self, text):
        """Extracts a sentiment score [-1, 1] from text."""

        if not text:
            print("%s No sentiment for empty text." % WARNING)
            return 0

        document = language.types.Document(
            content=text,
            type=language.enums.Document.Type.PLAIN_TEXT,
            language="en")
        sentiment = self.language_client.analyze_sentiment(
            document).document_sentiment

        print("%s Sentiment score and magnitude for text: %s %s \"%s\"" % (OK, sentiment.score, sentiment.magnitude, text))

        return sentiment.score

