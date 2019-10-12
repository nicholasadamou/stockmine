from twitter import Twitter

if __name__ == "__main__":
    twitter = Twitter()

    tweets = twitter.search("APPL", 1000)

    print(tweets)
