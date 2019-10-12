from anaylsis import Analysis

if __name__ == "__main__":
    analysis = Analysis()

    # Print banner and app description
    print(('-' * 20) + "Tweet2Stocks" + ("-" * 20))
    print("This python program that analyzes recent tweets that mentions\nany publicly traded companies and lunches a "
          "sentiment analysis\nto determine whether the aggregate opinion of the company in\nquestion is positive or "
          "negative.\n")

    ticker = input("[?] Enter a Ticker Symbol (e.g. $AAPL): ")
    numberOfTweets = input("[?] Enter a number of tweets to analyze: ")
    print()

    # Get tweets pertaining to a given company.
    tweets = analysis.twitter.search(ticker, numberOfTweets)

    print("[+] Analyzing [%s]" % ticker)

    for tweet in tweets:
        # Analyze a tweet.
        companies = analysis.find_companies(tweet)
        if companies:
            print(companies)

    print("[!] Done!")



