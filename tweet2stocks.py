import inquirer
import re

from pyfiglet import Figlet

from logs import *
from anaylsis import Analysis, write2csv
from twitter import get_tweet_link, compile_opinion_text

if __name__ == "__main__":
    analysis = Analysis()
    twitter = analysis.twitter

    # Print banner and app description
    custom_fig = Figlet(font='shadow')
    print(custom_fig.renderText('Tweet2Stocks'))
    print("This python program analyzes recent tweets that mentions\nany publicly traded companies and lunches a "
          "sentiment analysis\nto determine whether the opinion of the company in\nquestion is positive or "
          "negative.\n")

    # Ask the user to enter a target Ticker Symbol (e.g. $AAPL)
    questions = [
        inquirer.Text('ticker', message="Enter a Ticker Symbol (e.g. $AAPL)",
                      validate=lambda _, x: re.match(r'\$[A-Z]{1,4}', x),
                      ),
        inquirer.Text('numberOfTweets', message="Enter a number of tweets to analyze"),
    ]

    # Obtain user's response to questions
    answers = inquirer.prompt(questions)

    ticker = answers['ticker']
    numberOfTweets = answers['numberOfTweets']

    print()

    print("%s Analyzing %s tweet(s) for mentions of %s" % (WARNING, numberOfTweets, ticker))
    print()

    # Get tweets pertaining to a given company.
    tweets = analysis.twitter.search(ticker, numberOfTweets)

    data = []
    for tweet in tweets:
        # Analyze a tweet & obtain its sentiment.
        results = analysis.obtain_results(tweet)

        if not results:
            print("%s Didn't find any mention to a known publicly traded company." % ERROR)
            continue

        # Obtain tweets metadata.
        link = get_tweet_link(tweet)

        # Should we invest in $TICKER?
        opinions = compile_opinion_text(results)

        # Add 'opinion' to results.
        for company in results:
            for i in range(len(opinions)):
                opinion = opinions[i]
                if "$" + company['ticker'] == re.findall(r'\$[A-Z]{1,4}', opinion)[0]:
                    company.update({'opinion': opinion})

        print("%s %s" % (OK, results))

        # Add to results.
        data += results

        if len(tweets) > 1:
            print()

    if data:
        # Write results to csv.
        write2csv(ticker, data)

    print("\n%s Done" % SUCCESS)
