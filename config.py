# The keys for the Twitter app we're using for API requests
# (https://apps.twitter.com/app/13239588). Read from environment variables.
TWITTER_CONSUMER_KEY = "JxGdJEPig8Gb1FchNvw2BwC0M"
TWITTER_CONSUMER_SECRET = "DCIAfLJv01khTIwsI5qTRUQ7E3xtyhAFZSByhOIRDc6xNh4sbF"

# The keys for the Twitter account we're using for API requests.
# Read from environment variables.
TWITTER_ACCESS_TOKEN = "2184221952-6k8IG87lvtlrlpRDHuz40af2JQOYA2TJZ92g8WQ"
TWITTER_ACCESS_TOKEN_SECRET = "Wl07Ke4pzwdL6xGzqCOgrO45bft2bBuJu0CubMaNa1F5I"

# Required words that each tweet must contain.
REQUIRED_NLTK_TOKENS = ["Tesla", "@Tesla", "#Tesla", "tesla", "TSLA", "tsla",
                        "#TSLA", "#tsla", "elonmusk", "Elon", "Musk"]

# Words that each tweet must not contain.
IGNORED_NLTK_TOKENS = ["win", "Win", "giveaway", "Giveaway"]

# List of target users to listen for tweets from.
USERS = ["@elonmusk", "@cnbc", "@benzinga", "@stockwits",
         "@Newsweek", "@WashingtonPost", "@breakoutstocks", "@bespokeinvest",
         "@WSJMarkets", "@stephanie_link", "@nytimesbusiness", "@IBDinvestors",
         "@WSJDealJournal", "@jimcramer", "@TheStalwart", "@TruthGundlach",
         "@Carl_C_Icahn", "@ReformedBroker", "@bespokeinvest", "@stlouisfed",
         "@muddywatersre", "@mcuban", "@AswathDamodaran", "@elerianm",
         "@MorganStanley", "@ianbremmer", "@GoldmanSachs", "@Wu_Tang_Finance",
         "@Schuldensuehner", "@NorthmanTrader", "@Frances_Coppola",
         "@BuzzFeed", "@nytimes"]
