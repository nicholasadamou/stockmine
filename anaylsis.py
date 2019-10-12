from google.cloud import language
from re import compile
from re import IGNORECASE
from urllib.parse import quote_plus
from requests import get

from twitter import Twitter

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


class Analysis:
    """A helper for analyzing company data in text."""

    def __init__(self):
        self.language_client = language.LanguageServiceClient()
        self.twitter = Twitter()

    def get_company_data(self, mid):
        """Looks up stock ticker information for a company via its Freebase ID.
        """

        query = MID_TO_TICKER_QUERY % mid
        bindings = self.make_wikidata_request(query)

        if not bindings:
            print("No company data found for MID: %s" % mid)
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
                print("Adding company data: %s" % company)
                companies.append(company)
            else:
                print("Skipping duplicate company data: %s" % company)

        return companies

    def find_companies(self, tweet):
        """Finds mentions of companies in a tweet."""

        if not tweet:
            print("No tweet to find companies.")
            return None

        # Use the text of the tweet with any mentions expanded to improve
        # entity detection.
        text = tweet.text
        if not text:
            print("Failed to get text from tweet: %s" % tweet)
            return None

        # Run entity detection.
        document = language.types.Document(
            content=text,
            type=language.enums.Document.Type.PLAIN_TEXT,
            language="en")
        entities = self.language_client.analyze_entities(document).entities
        print("Found entities: %s" %
                        self.entities_tostring(entities))

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
                print("No MID found for entity: %s" % name)
                continue

            company_data = self.get_company_data(mid)

            # Skip any entity for which we can't find any company data.
            if not company_data:
                print("No company data found for entity: %s (%s)" %
                                (name, mid))
                continue
            print("Found company data: %s" % company_data)

            for company in company_data:

                # Extract and add a sentiment score.
                sentiment = self.get_sentiment(text)
                print("Using sentiment for company: %s %s" %
                                (sentiment, company))
                company["sentiment"] = sentiment

                # Add the company to the list unless we already have the same
                # ticker.
                tickers = [existing["ticker"] for existing in companies]
                if not company["ticker"] in tickers:
                    companies.append(company)
                else:
                    print("Skipping company with duplicate ticker: %s" % company)

        return companies

    def get_expanded_text(self, tweet):
        """Retrieves the text from a tweet with any @mentions expanded to
        their full names.
        """

        if not tweet:
            print("No tweet to expand text.")
            return None

        try:
            text = self.twitter.get_tweet_text(tweet)
            mentions = tweet["entities"]["user_mentions"]
        except KeyError:
            print("Malformed tweet: %s" % tweet)
            return None

        if not text:
            print("Empty text.")
            return None

        if not mentions:
            print("No mentions.")
            return text

        print("Using mentions: %s" % mentions)
        for mention in mentions:
            try:
                screen_name = "@%s" % mention["screen_name"]
                name = mention["name"]
            except KeyError:
                print("Malformed mention: %s" % mention)
                continue

            print("Expanding mention: %s %s" % (screen_name, name))
            pattern = compile(screen_name, IGNORECASE)
            text = pattern.sub(name, text)

        return text

    def make_wikidata_request(self, query):
        """Makes a request to the Wikidata SPARQL API."""

        query_url = WIKIDATA_QUERY_URL % quote_plus(query)
        print("Wikidata query: %s" % query_url)

        response = get(query_url)

        try:
            response_json = response.json()
        except ValueError:
            print("Failed to decode JSON response: %s" % response)
            return None
        print("Wikidata response: %s" % response_json)

        try:
            results = response_json["results"]
            bindings = results["bindings"]
        except KeyError:
            print("Malformed Wikidata response: %s" % response_json)
            return None

        return bindings

    def entities_tostring(self, entities):
        """Converts a list of entities to a readable string."""

        return "[%s]" % ", ".join([self.entity_tostring(entity) for entity in entities])

    def entity_tostring(self, entity):
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

    def get_sentiment(self, text):
        """Extracts a sentiment score [-1, 1] from text."""

        if not text:
            print("No sentiment for empty text.")
            return 0

        document = language.types.Document(
            content=text,
            type=language.enums.Document.Type.PLAIN_TEXT,
            language="en")
        sentiment = self.language_client.analyze_sentiment(
            document).document_sentiment

        print(
            "Sentiment score and magnitude for text: %s %s \"%s\"" %
            (sentiment.score, sentiment.magnitude, text))

        return sentiment.score