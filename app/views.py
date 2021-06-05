from django.shortcuts import render, redirect
from django.views.generic import View
from django.conf import settings
from .forms import TweetForm
from datetime import datetime, timedelta
import tweepy
import pandas as pd
import json

# twitter API 認証
TWEEPY_AUTH = tweepy.OAuthHandler(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
TWEEPY_AUTH.set_access_token(settings.ACCESS_KEY, settings.ACCESS_KEY_SECRET)
# API利用制限にかかった場合、解除まで待機する
TWEEPY_API = tweepy.API(TWEEPY_AUTH, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

