import inquirer
import re

from anaylsis import Analysis

if __name__ == "__main__":
    analysis = Analysis()
    twitter = analysis.twitter

    # Print banner and app description
    print(('-' * 20) + "Tweet2Stocks" + ("-" * 20))
    print("This python program that analyzes recent tweets that mentions\nany publicly traded companies and lunches a "
          "sentiment analysis\nto determine whether the opinion of the company in\nquestion is positive or "
          "negative.\n")

    # Ask the user to enter a target Ticker Symbol (e.g. $AAPL)
    questions = [
        inquirer.Text('ticker', message="Enter a Ticker Symbol (e.g. $AAPL)",
                      validate=lambda _, x: not re.match(r'\$[A-Z]{1-4}', x),
                      ),
        inquirer.Text('numberOfTweets', message="Enter a number of tweets to analyze"),
    ]

    # Obtain user's response to questions
    answers = inquirer.prompt(questions)

    ticker = answers['ticker']
    numberOfTweets = answers['numberOfTweets']

    print()

    # Get tweets pertaining to a given company.
    tweets = analysis.twitter.search(ticker, numberOfTweets)

    print("[-] Analyzing [%s]" % ticker)
    print()

    data = []
    for tweet in tweets:
        # Analyze a tweet & obtain its sentiment.
        results = analysis.obtain_results(tweet)

        # Obtain tweets metadata.
        link = twitter.get_tweet_link(tweet)

        # Should we invest in $TICKER?
        opinions = twitter.compile_opinion_text(results)

        # Add 'opinion' to results.
        for company in results:
            for i in range(len(opinions)):
                opinion = opinions[i]
                if "$" + company['ticker'] == re.findall(r'\$[A-Z]{4}', opinion)[0]:
                    print("[+]", "$" + company['ticker'], re.findall(r'\$[A-Z]{4}', opinion)[0])
                    company.update({'opinion': opinion})

        # Add to results.
        data += results

        if results:
            print("[+] %s", results)
        else:
            print("[!] Didn't find any companies.")

        if len(tweets) > 1:
            print()

    if data and opinions:
        # Write results to csv.
        analysis.write2csv(ticker, data)

    print("\n[!] Done")
