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
