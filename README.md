# StockBird

This bot watches recent tweets that mentions any publicly traded companies. When someone does, it uses sentiment analysis to determine whether the aggregate opinion is positive or negative toward those companies. The bot then automatically executes trades on the relevant stocks according to the expected market reaction. It also tweets out a summary of its findings in real time at [@StockBird](https://twitter.com/Stockbird).

![HackUIowa 2019](https://img.shields.io/badge/hackathon-Intern%20HackUIowa%202019-yellow)
![License](https://img.shields.io/badge/license-GPLv3-blue.svg?style=flat-square)
![Say Thanks](https://img.shields.io/badge/say-thanks-ff69b4.svg)

---

The code is written in Python and is meant to run on a
[Google Compute Engine](https://cloud.google.com/compute/) instance. It uses the
[Twitter Streaming APIs](https://dev.twitter.com/streaming/overview) to get
notified whenever Trump tweets. The entity detection and sentiment analysis is
done using Google's
[Cloud Natural Language API](https://cloud.google.com/natural-language/) and the
[Wikidata Query Service](https://query.wikidata.org/) provides the company data.
The [TradeKing API](https://developers.tradeking.com/) does the stock trading.

The [`main`](main.py) module defines a callback where incoming tweets are
handled and starts streaming its feed:

```python
def twitter_callback(tweet):
    companies = analysis.find_companies(tweet)
    if companies:
        trading.make_trades(companies)
        twitter.tweet(companies, tweet)
if __name__ == "__main__":
    twitter.start_streaming(twitter_callback)
```

The core algorithms are implemented in the [`analysis`](analysis.py) and
[`trading`](trading.py) modules. The former finds mentions of companies in the
text of the tweet, figures out what their ticker symbol is, and assigns a
sentiment score to them. The latter chooses a trading strategy, which is either
buy now and sell at close or sell short now and buy to cover at close. The
[`twitter`](twitter.py) module deals with streaming and tweeting out the
summary.

Follow these steps to run the code yourself:

### 1. Create VM instance

Check out the [quickstart](https://cloud.google.com/compute/docs/quickstart-linux)
to create a Cloud Platform project and a Linux VM instance with Compute Engine,
then SSH into it for the steps below. Pick a predefined
[machine type](https://cloud.google.com/compute/docs/machine-types) matching
your preferred price and performance.

#### Container

Alternatively, you can use the [`Dockerfile`](Dockerfile) to build a
[Docker container](https://www.docker.com/what-container) and
[run it on Compute Engine](https://cloud.google.com/compute/docs/containers/deploying-containers)
or other platforms.

```shell
docker build -t stockbird .
docker tag stockbird gcr.io/<YOUR_GCP_PROJECT_NAME>/stockbird
docker push gcr.io/<YOUR_GCP_PROJECT_NAME>/stockbird:latest
```

### 2. Set up auth

The authentication keys for the different APIs are read from shell environment
variables. Each service has different steps to obtain them.

#### Twitter

Log in to your [Twitter](https://twitter.com/) account and
[create a new application](https://apps.twitter.com/app/new). Under the *Keys
and Access Tokens* tab for [your app](https://apps.twitter.com/) you'll find
the *Consumer Key* and *Consumer Secret*. Export both to environment variables:

```shell
export TWITTER_CONSUMER_KEY="<YOUR_CONSUMER_KEY>"
export TWITTER_CONSUMER_SECRET="<YOUR_CONSUMER_SECRET>"
```

If you want the tweets to come from the same account that owns the application,
simply use the *Access Token* and *Access Token Secret* on the same page. If
you want to tweet from a different account, follow the
[steps to obtain an access token](https://dev.twitter.com/oauth/overview). Then
export both to environment variables:

```shell
export TWITTER_ACCESS_TOKEN="<YOUR_ACCESS_TOKEN>"
export TWITTER_ACCESS_TOKEN_SECRET="<YOUR_ACCESS_TOKEN_SECRET>"
```

#### Google

Follow the
[Google Application Default Credentials instructions](https://developers.google.com/identity/protocols/application-default-credentials#howtheywork)
to create, download, and export a service account key.

```shell
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials-file.json"
```

You also need to [enable the Cloud Natural Language API](https://cloud.google.com/natural-language/docs/getting-started#set_up_your_project)
for your Google Cloud Platform project.

#### TradeKing

Log in to your [TradeKing](https://www.tradeking.com/) account and
[create a new application](https://developers.tradeking.com/applications/CreateApplication).
Behind the *Details* button for
[your application](https://developers.tradeking.com/Applications) you'll find
the *Consumer Key*, *Consumer Secret*, *OAuth (Access) Token*, and *Oauth (Access)
Token Secret*. Export them all to environment variables:

```shell
export TRADEKING_CONSUMER_KEY="<YOUR_CONSUMER_KEY>"
export TRADEKING_CONSUMER_SECRET="<YOUR_CONSUMER_SECRET>"
export TRADEKING_ACCESS_TOKEN="<YOUR_ACCESS_TOKEN>"
export TRADEKING_ACCESS_TOKEN_SECRET="<YOUR_ACCESS_TOKEN_SECRET>"
```

Also export your TradeKing account number, which you'll find under
*[My Accounts](https://investor.tradeking.com/Modules/Dashboard/dashboard.php)*:

```shell
export TRADEKING_ACCOUNT_NUMBER="<YOUR_ACCOUNT_NUMBER>"
```

### 3. Install dependencies

There are a few library dependencies, which you can install using
[pip](https://pip.pypa.io/en/stable/quickstart/):

```shell
$ pip install -r requirements.txt
```

### 4. Start the bot

Enable real orders that use your money:

```shell
$ export USE_REAL_MONEY=YES
```

Have the code start running in the background with this command:

```shell
$ nohup python main.py &
```

## License

Copyright 2017 Nicholas Adamou, Cole Horner, Angel Fabila

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
