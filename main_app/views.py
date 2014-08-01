import random
import re
from multiprocessing import Pool

from django.shortcuts import render, render_to_response
from django.views.decorators.csrf import csrf_exempt
from requests import request

import tweepy
from giphypop import Giphy
from memoize import memoize

# keys here
# Should put these all in settings.py
consumer_key='Y1a564pRXuGwA5yILOpOuSSOz'
consumer_secret='panvWIWqMWIDmR1rQGyHK1Wu62IvSBl8OsWxs2YnLjejtqaWc3'

access_token='2594549893-eQXRBr2Lrb2X9w68dSxxLf3H99omQR6qo1L1l9s'
access_token_secret='WbDaMifGIsvcvlk7avIZFpAY5X7DN85avggO7b7Inqyfb'


@memoize(timeout=60)
def get_trends():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    # better variable naming, putting numbers in the variable name is a no-no
    trends1 = api.trends_place(2450022) #2450022
    data = trends1[0]
    trends = data['trends']
    trend_names = [trend['name'] for trend in trends]
    return trend_names

def get_gifs(trend):
    """a helper function that will return a list of gifs' urls for a
    given trend"""
    giphy = Giphy()
    results = giphy.search(trend)
    results = [result.media_url for result in results]
    return results

def parse_trend(trend):
    regex = r'[A-Z][a-z]+'
    parsed = re.findall(regex, trend)
    parsed = ' '.join(parsed)
    return parsed

@memoize(timeout=60)
def heuristic_get_gifs(trend):
    # try get a gif for the trend
    gifs = get_gifs(trend)
    # if there is no trend to be had do the rest
    if not gifs:
        heuristic = parse_trend(trend)
        if not heuristic:
            return []
        gifs = get_gifs(heuristic)
        if not gifs:
            heuristic = max(heuristic.split(), key=len)
            gifs = get_gifs(heuristic)
    return gifs




def trends_to_gifs(request):
    trends = get_trends()
    # makes an instance of Pool that takes the length of trends, lets it know how many
    # threads that there will be.
    
    # nice job on messing with multiprocessing stuff and using map and zip
    pool = Pool(len(trends))
    # me create a var gifs, this is map from pool, which takes a function, and list of trends, then magic
    gifs = pool.map(heuristic_get_gifs, trends)
    # pool.close lets it know that we are not adding more tasks
    pool.close()
    # this waits for threads to complete tasks
    pool.join()

    gifs = zip(trends, gifs)
    # the first gif is there incase we want to do something to it ex:
    # '1', '2', '3', '4', '5', '6', '7']
    # >>> [2*x for x in l if x<4]
    # [2, 4, 6]

    gifs = [gif for gif in gifs if gif[1]]
    gifs = [(gif[0], random.sample(gif[1], 1)[0]) for gif in gifs]
    return render(request, 'home.html', locals())




