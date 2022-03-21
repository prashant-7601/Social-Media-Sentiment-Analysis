# imports
from pydoc import doc
from django.shortcuts import render, HttpResponse
from youtubesearchpython import *
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy import API, Cursor
import nltk
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.stem import WordNetLemmatizer
import regex as re

# init
# nltk.download("all")
ACCESS_TOKEN = "925747018156273665-ijNwRFdQeYw80OrDmk0TfZvlTOtjMTL"
ACCESS_TOKEN_SECRET = "lwCwxlky0Qtf8SBElh3egt571YWCFm0BD5Fl1Hh12g49M"
CONSUMER_KEY = "jVQuktuXbywXUXRsGCjnylfal"
CONSUMER_KEY_SECRET = "RF5Q1rtb8t7cgl8dA62TRByMvez8nAbrviH7oO0yGRLsG1xdaf"
auth = OAuthHandler(CONSUMER_KEY, CONSUMER_KEY_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
twitter_client = API(auth)
analyzer = SentimentIntensityAnalyzer()

# globals
scores = {}
all_group = {}
youtube_group = {}
twitter_group = {}
all_sentiment = {}
youtube_sentiment = {}
twitter_sentiment = {}


def analyze(sents):
    scores = {}
    for s in sents:
        scores[s] = analyzer.polarity_scores(str(s))
    return scores


def get_youtube_comments(search):
    total = []
    videosSearch = VideosSearch(search, limit=3)
    results = videosSearch.result()
    for r in results["result"]:
        id = r["id"]
        comments = Comments.get(id)
        for c in comments["result"]:
            total.append(c["content"])
    return total


def bag_of_words(sents):
    bag = {}
    sentiment = {}
    group = {}
    stop = stopwords.words("english")
    lemmatizer = WordNetLemmatizer()
    for s in sents:
        for word in s.split():
            word = str(word)
            word = re.sub(r"^https?://.*[rn]*", "", word, flags=re.MULTILINE)
            word = re.sub("<[^<]+?>!,.", "", word)
            word = re.sub('[^A-Za-z0-9]+', '', word)
            word = lemmatizer.lemmatize(word.lower())
            tag = nltk.pos_tag([word])[0][1]
            if tag not in ('NN', 'NNP'):
                continue
            if word in stop or word=="" or word=="rt":
                continue
            else:
                if word in bag:
                    bag[word] += 1
                    if s not in group[word]:
                        group[word].append(s)
                else:
                    bag[word] = 1
                    group[word] = [s]
        sentiment[s] = analyzer.polarity_scores(s)
    return bag, sentiment, group


def get_tweets(search):
    tweets = []
    for tweet in Cursor(
        twitter_client.search_tweets, q=search, lang="en", tweet_mode="extended"
    ).items(500):
        tweets.append(str(tweet.full_text))
    return tweets


def index(request):
    return render(request, "homepage.html")

def get_hot_details(bag, group, sentiment):
    i = 0
    hotwords = []
    for w in sorted(bag, key=bag.get, reverse=True):
        hotwords.append(w)
        i+=1
        if i==5:
            break
    count = 0
    sum = 0
    res = {}
    for word in hotwords:
        for s in group[word]:
            print(word, sentiment[s])
            sum += float(sentiment[s]['compound'])
            count += 1
        print(word, sum, count)
        if sum*1.0/count > 0.10:
            res[word] = "Positive"
        elif sum*1.0/count < 0:
            res[word] = "Negative"
        else:
            res[word] = "Neutral"
    return res


def search(request):
    global all_sentiment, twitter_sentiment, youtube_sentiment, all_group, youtube_group, twitter_group
    all = []
    scores = {}
    all_group = {}
    youtube_group = {}
    twitter_group = {}
    all_sentiment = {}
    youtube_sentiment = {}
    twitter_sentiment = {}
    search = request.POST.get("name")
    youtube_comments = []
    try:
        youtube_comments = get_youtube_comments(search)
    except:
        pass
    tweets = get_tweets(search)
    all.extend(youtube_comments)
    all.extend(tweets)
    all_bag, all_sentiment, all_group = bag_of_words(all)
    youtube_bag, youtube_sentiment, youtube_group = bag_of_words(youtube_comments)
    twitter_bag, twitter_sentiment, twitter_group = bag_of_words(tweets)
    youtube_sum, twitter_sum, all_sum = 0.0, 0.0, 0.0
    youtube_count, twitter_count, all_count = 0, 0, 0
    for s, values in all_sentiment.items():
        all_sum += float(values['compound'])
        all_count += 1
    for s, values in twitter_sentiment.items():
        twitter_sum += float(values['compound'])
        twitter_count += 1
    for s, values in youtube_sentiment.items():
        youtube_sum += float(values['compound'])
        youtube_count += 1
    youtube_score = 0
    if youtube_count>0:
        youtube_score = youtube_sum*1.0/youtube_count
    twitter_score = 0
    if twitter_count>0:
        twitter_score = twitter_sum*1.0/twitter_count
    all_score = 0
    if all_count>0:
         all_score = all_sum*1.0/all_count
    if youtube_score > 0.10:
        youtube_score = "Positive"
    elif youtube_score < 0:
        youtube_score = "Negative"
    else:
        youtube_score = "Neutral"
    if twitter_score > 0.10:
        twitter_score = "Positive"
    elif twitter_score < 0:
        twitter_score = "Negative"
    else:
        twitter_score = "Neutral"
    if all_score > 0.10:
        all_score = "Positive"
    elif all_score < 0:
        all_score = "Negative"
    else:
        all_score = "Neutral"
    all_data = get_hot_details(all_bag, all_group, all_sentiment)
    twitter_data = get_hot_details(twitter_bag, twitter_group, twitter_sentiment)
    youtube_data = get_hot_details(youtube_bag, youtube_group, youtube_sentiment)
    return render(request, "result.html", {'Search': search, 'All': all_data, 'Twitter': twitter_data, 'Youtube': youtube_data,
    'all_score': all_score, 'twitter_score': twitter_score, 'youtube_score': youtube_score})
