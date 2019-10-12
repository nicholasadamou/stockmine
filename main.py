from twitter import Twitter

t = Twitter()
tweets = t.search("APPL", 10)
print(tweets)
