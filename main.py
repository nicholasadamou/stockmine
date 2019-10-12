from anaylsis import Analysis
from twitter import Twitter

if __name__ == "__main__":
    analysis = Analysis()

    # Get a tweet on a publicly traded company
    tweets = analysis.twitter.search("$GOOG", 1)
    tweet = list(tweets.values())[0]

    print(tweet.text)

    # Analyze a tweet
    companies = analysis.find_companies(tweet)



