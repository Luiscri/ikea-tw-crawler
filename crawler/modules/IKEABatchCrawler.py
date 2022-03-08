import os
import logging
from datetime import date
from typing import Any, Union

import tweepy
import dateutil.parser

import utils.gcp_utils as gcp_utils

MONGODB_COLLECTION = os.environ.get('MONGODB_COLLECTION')
GOOGLE_CLOUD_PROJECT = os.environ.get('GOOGLE_CLOUD_PROJECT')

class IKEABatchCrawler():
    """
    Class used to crawl batch data from Twitter API.

    Attributes
    ----------
    api: tweepy.api
        Twitter API object used to perform the queries.
    db: pymongo.database.Database | google.cloud.bigquery.Client
        Database object used to save the results.
    tweet_ids: list
        List contaning the tweet ids which have been collected.
    count: int
        Counter with the quantity of tweets collected.

    Methods
    -------
    crawl_tweets(self, query: str, lang: str, count: str, until: str)
        Method which crawls the tweets which fits the given parameters.
    """

    def __init__(self, consumer_key: str, consumer_secret: str,
                 access_token: str, access_token_secret:str, db: Any):
        """
        Parameters
        ----------
        consumer_key: str
            Consumer key from Twitter API.
        consumer_secret: str
            Consumer secret from Twitter API.
        access_token: str
            Access token from Twitter API.
        access_token_secret: str
            Access token secret from Twitter API.
        db: pymongo.database.Database | google.cloud.bigquery.Client
            Database object used to save the results.
        """

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token,access_token_secret)
        self.api = tweepy.API(auth, wait_on_rate_limit=True)
        self.db = db
        self.tweet_ids = []
        self.count = 0
    
    def crawl_tweets(self, query: str, lang: str, count: Union[str, int],
                     until: Union[str, date]):
        """Method which crawls the tweets which fits the given parameters.

        Data is processed, transformed and only certain fields are retrieved:

        [ id, created_at, text, lang, coordinates, source, favorite_count,
          retweet_count, quote_count, reply_count ]

        Finally, data is stored to the database defined as a calss atribute.

        Parameters
        ----------
        query: str
            Defines the query which the tweets must match in order to be
            retrieved.
        lang: str
            Defines the language in which the tweets must be written in order
            to be retrieved.
        count: str | int
            The number of results to try and retrieve per page.
        until: str | date
            Returns tweets created before the given date. Date should be
            formatted as YYYY-MM-DD.
        """
        
        statuses = self.api.search_tweets(
            q=query, count=count, lang=lang, until=until
        )

        output = []
        for status in statuses:
            status = status._json
            
            tweet = {}
            tweet['id'] = status['id_str']
            created_at = dateutil.parser.parse(status['created_at'])
            tweet['created_at'] = created_at.strftime('%Y-%m-%d %H:%M:%S')
            if ('extended_tweet' in status
                    and 'full_text' in status['extended_tweet']):
                tweet['text'] = status['extended_tweet']['full_text']
            else:
                tweet['text'] = status['text']
            
            keys = ['lang', 'coordinates', 'source']
            for key in keys:
                if status.get(key) != None:
                    tweet[key] = status[key]
            keys = ['favorite_count', 'retweet_count', 'quote_count',
                    'reply_count']
            for key in keys:
                if status.get(key) != None:
                    if 'interactions' not in tweet:
                        tweet['interactions'] = {}
                    tweet['interactions'][key] = status[key]
            tweet['crawler'] = 'batch'
            output.append(tweet)

        if GOOGLE_CLOUD_PROJECT == "False":
            self.db[MONGODB_COLLECTION].insert_many(output)
            ids = [tweet['_id'] for tweet in output if '_id' in tweet]
        else:
            gcp_utils.upload_data_to_bq(self.db, output)
            ids = [tweet['id'] for tweet in output if 'id' in tweet]
        self.tweet_ids = ids
        self.count = len(ids)
        
        message = "BATCH | {} tweets saved to db.".format(len(output))
        print(message)
        logging.info(message)