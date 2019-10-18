# stockflight 🛫

Crowd-sourced stock analyzer and stock predictor using Google's [Cloud Natural Language API](https://cloud.google.com/natural-language/), Twitter, and [Wikidata Query Service](https://query.wikidata.org/) in order to determine how much do emotions affect a stock price?

![HackUIowa 2019](https://img.shields.io/badge/hackathon-HackUIowa%202019-yellow)
[![License](https://img.shields.io/github/license/nicholasadamou/stockflight.svg?label=License&maxAge=86400)](./LICENSE)
![Say Thanks](https://img.shields.io/badge/say-thanks-ff69b4.svg)

---

## 🤔 Why make '_Stock Flight_'?

This project was created for the 2019 [HackUIowa](https://hackuiowa-2019.devpost.com/) event. 

HackUIowa was a 2 day non-stop hackathon, and it was held at University of Iowa in the heart of downtown Iowa City, USA.

## Technologies

The code is written in Python and its entity detection and sentiment analysis is
done using Google's [Cloud Natural Language API](https://cloud.google.com/natural-language/) and the
[Wikidata Query Service](https://query.wikidata.org/) provides the company data.

Follow these steps to run the code yourself:

### 1. Set up auth

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

### 2. Install dependencies

There are a few library dependencies, which you can install using
[pip](https://pip.pypa.io/en/stable/quickstart/):

```shell
$ pip3 install -r requirements.txt
```

### 3. Set up `.env`

`.env` is the file used to store API keys.

```shell
TWITTER_CONSUMER_KEY=
TWITTER_CONSUMER_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=
GOOGLE_APPLICATION_CREDENTIALS=
```

### 4. Run the program using the following examples

Run `stockflight` to start mining and analyzing tweets using keywords.

```shell
$ python3 stockflight.py --keywords TSLA,'Elon Musk',Musk,Tesla,SpaceX
```

Run `stockflight` to start mining and analyzing tweets using keywords along with a set of ignored keywords.

```shell
$ python3 stockflight.py \
    --keywords TSLA,'Elon Musk',Musk,Tesla,SpaceX \
    --ignored-keywords win,Win,giveaway,Giveaway
```

Run `stockflight` to start mining and analyzing tweets from specific users specified in a file.

```shell
$ python3 stockflight.py --file users.txt
```

Run `stockflight` to start mining and analyzing tweets from specific users specified in a file along with a set of required keywords that each tweet from those user's feeds must contain.

```shell
$ python3 stockflight.py \
    --file users.txt \
    --required-keywords Tesla,@Tesla,#Tesla,tesla,TSLA,tsla,#TSLA,#tsla,'elonmusk',Elon,Musk
```

Run `stockflight` to start mining and analyzing tweets from specific users specified in a file along with a set of required keywords that each tweet from those user's feeds must contain, plus ignored keywords.

```shell
$ python3 stockflight.py \
    --file users.txt \
    --required-keywords Tesla,@Tesla,#Tesla,tesla,TSLA,tsla,#TSLA,#tsla,'elonmusk',Elon,Musk \
    --ignored-keywords win,Win,giveaway,Giveaway
```

Run `stockflight` to start mining and analyzing Yahoo Finance news headlines and following headline links and scraping relevant text on landing page.

```sh
$ python3 stockflight.py --news-headlines --follow-links --symbol TSLA
```

Run `stockflight` to fetch stock data pertaining to a given company.

```sh
$ python3 stockflight.py --symbol TSLA
```

### CLI options

```
usage: stockflight.py [-h] [-k KEYWORDS]
                      [--required-keywords REQUIRED_KEYWORDS]
                      [--ignored-keywords IGNORED_KEYWORDS] [-f FILE] [-u URL]
                      [-s SYMBOL] [--news-headlines] [--frequency FREQUENCY]
                      [--follow-links] [-V]

optional arguments:
  -h, --help            show this help message and exit
  -k KEYWORDS, --keywords KEYWORDS
                        Use keywords to search for in Tweets instead of feeds.
                        Separated by comma, case insensitive, spaces are ANDs
                        commas are ORs. Example: TSLA,'Elon
                        Musk',Musk,Tesla,SpaceX
  --required-keywords REQUIRED_KEYWORDS
                        Words that each tweet from a user's feed must contain.
                        Separated by comma, case insensitive. Example: Tesla,@
                        Tesla,#Tesla,tesla,TSLA,tsla,#TSLA,#tsla,'elonmusk',El
                        on,Musk
  --ignored-keywords IGNORED_KEYWORDS
                        Words that each tweet must not contain. Can be used
                        with feeds or keywords. Separated by comma, case
                        insensitive, spaces are ANDs commas are ORs. Example:
                        win,Win,giveaway,Giveaway
  -f FILE, --file FILE  Use Twitter User IDs from file.
  -u URL, --url URL     Scrap Twitter User IDs from URL.
  -s SYMBOL, --symbol SYMBOL
                        Stock symbol to use when fetching stock data.,
                        example: TSLA
  --news-headlines      Get news headlines instead of Twitter using stock
                        symbol, example: TSLA
  --frequency FREQUENCY
                        How often in seconds to retrieve news headlines.
                        (default: 120 sec)
  --follow-links        Follow links on news headlines and scrape relevant
                        text from landing page.
  -V, --version         Prints version and exits.
  ```

## License

Copyright 2019 Nicholas Adamou, Cole Horner, Angel Fabila

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
