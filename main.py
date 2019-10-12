from anaylsis import Analysis
from twitter import Twitter

if __name__ == "__main__":
    analysis = Analysis()

    # Get a tweet
    tweets = analysis.twitter.search("$AMZN", 1)
    # tweet = list(tweets.values())[0]

    # print(tweet.text)

    for tweet in tweets:
        print(tweet.text)
        # Analyze a tweet
        companies = analysis.find_companies(tweet)
        print(companies)
        print("\n")



