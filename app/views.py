from django.shortcuts import render, redirect
from django.views.generic import View
from django.conf import settings
from .forms import TweetForm
from datetime import datetime, time, timedelta
import tweepy
import pandas as pd
import json

# twitter API 認証
TWEEPY_AUTH = tweepy.OAuthHandler(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
TWEEPY_AUTH.set_access_token(settings.ACCESS_KEY, settings.ACCESS_KEY_SECRET)
# API利用制限にかかった場合、解除まで待機する
TWEEPY_API = tweepy.API(TWEEPY_AUTH, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


def get_search_tweet(keyword, items_count, rl_count, search_start, search_end):
  tweets = tweepy.Cursor(
    TWEEPY_API.search,
    q = keyword + '-filter:retweets',
    exclude_replies=True,
    since=search_start,
    until=search_end,
    tweet_mode='extended',
    lang='ja',
  ).items(items_count)
  
  tweet_data = []
  favorite_data = {}
  retweet_data = {}
  post_data = {}
  date_tmp = ''
  favorite_data_count = 0
  retweet_data_count = 0
  post_data_count = 0
  
  
  for tweet in tweets:
    if tweet.favorite_count + tweet.retweet_count >= rl_count:
      tweet.created_at += timedelta(hours=9)
      created_at = tweet.created_at.strftime('%Y-%m-%d %H:%M')
      
      date = tweet.created_at.strftime('%Y-%m-%d')
      if date_tmp == date:
        favorite_data_count += tweet.favorite_count
        retweet_data_count += tweet.retweet_count
        post_data_count += 1
      else:
        date_tmp = date
        favorite_data_count = tweet.favorite_count
        retweet_data_count = tweet.retweet_count
        post_data_count = 1
        
      favorite_data[date] = favorite_data_count
      retweet_data[date] = retweet_data_count
      post_data[date] = post_data_count
      
        
      
      try:
        media_url = tweet.entities['media'][0]['media_url_https']
      except KeyError:
        media_url = ''
      
      tweet_data.append([
        tweet.user.name,
        tweet.user.screen_name,
        tweet.user.profile_image_url,
        media_url,
        tweet.full_text,
        tweet.retweet_count,
        tweet.favorite_count,
        created_at,
      ])
  return tweet_data, favorite_data, retweet_data, post_data
    
    
def make_df(data):
  name = []
  screen_name = []
  profile_image_url = []
  media_url = []
  full_text = []
  retweet_count = []
  favorite_count = []
  created_at = []
  
  for i in range(len(data)):
    name.append(data[i][0])
    screen_name.append(data[i][1])
    profile_image_url.append(data[i][2])
    media_url.append(data[i][3])
    full_text.append(data[i][4])
    retweet_count.append(data[i][5])
    favorite_count.append(data[i][6])
    created_at.append(data[i][7])
  
  df_name = pd.Series(name)
  df_screen_name = pd.Series(screen_name)
  df_profile_image_url = pd.Series(profile_image_url)
  df_media_url = pd.Series(media_url)
  df_full_text = pd.Series(full_text)
  df_retweet_count = pd.Series(retweet_count)
  df_favorite_count = pd.Series(favorite_count)
  df_created_at = pd.Series(created_at)
  
  df = pd.concat([
    df_name,
    df_screen_name,
    df_profile_image_url,
    df_media_url,
    df_full_text,
    df_retweet_count,
    df_favorite_count,
    df_created_at,
  ], axis=1)
  
  df.columns = [
    'name',
    'screen_name',
    'profile_image_url',
    'media_url',
    'full_text',
    'retweet_count',
    'favorite_count',
    'created_at'
  ]
  
  return df


class IndexView(View):
  def get(self, request, *args, **kwargs):
    form = TweetForm(
      request.POST or None,
      initial={
        'items_count': 100,
        'rl_count': 1,
        'search_start': datetime.today() - timedelta(days=7),
        'search_end': datetime.today(),
      }
    )
    
    return render(request, 'app/index.html', {
      'form' : form
    })
    
  def post(self, request, *args, **kwargs):
    form = TweetForm(request.POST or None)
    
    if form.is_valid():
      keyword = form.cleaned_data['keyword']
      items_count = form.cleaned_data['items_count']
      rl_count = form.cleaned_data['rl_count']
      search_start = form.cleaned_data['search_start']
      search_end = form.cleaned_data['search_end']
      
      data = get_search_tweet(keyword, items_count, rl_count, search_start, search_end)
      tweet_data = data[0]
      favorite_data = data[1]
      retweet_data = data[2]
      post_data = data[3]
      
      graph_data = {
        'date': list(reversed(list(favorite_data.keys()))),
        'favorite_data': list(reversed(list(favorite_data.values()))),
        'retweet_data': list(reversed(list(retweet_data.values()))),
        'post_data': list(reversed(list(post_data.values()))),
      }
      tweet_data = make_df(tweet_data)
      
      limit = TWEEPY_API.last_response.headers['x-rate-limit-remaining']
      
      return render(request, 'app/tweet.html',{
        'keyword' : keyword,
        'tweet_data' : tweet_data,
        'limit' : limit,
        'graph_data': json.dumps(graph_data),
      })
    else:
      return redirect('index')