import os
import json
import logging
from typing import Any

import tweepy
import dateutil.parser

import utils.gcp_utils as gcp_utils

MONGODB_COLLECTION = os.environ.get('MONGODB_COLLECTION')
GOOGLE_CLOUD_PROJECT = os.environ.get('GOOGLE_CLOUD_PROJECT')

class IKEAStreamingCrawler(tweepy.Stream):
    """
    Class used to crawl streaming data from Twitter API.

    Extends
    -------
    tweepy.Stream

    Attributes
    ----------
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

    def __init__(self, db: Any, *args, **kw):
        """
        Parameters
        ----------
        db: pymongo.database.Database | google.cloud.bigquery.Client
            Database object used to save the results.
        """

        super().__init__(*args, **kw)
        self.db = db
        self.tweet_ids = []
        self.count = 0
    
    def on_data(self, raw_data: str):
        """Method which runs whenever a new tweet reachs the stream.

        Data is processed, transformed and only certain fields are retrieved:

        [ id, created_at, text, lang, coordinates, source, favorite_count,
          retweet_count, quote_count, reply_count ]

        Finally, data is stored to the database defined as a class atribute.

        Parameters
        ----------
        raw_data: str
            JSON-like object containing the tweet data.
        """

        tweet = json.loads(raw_data)
        
        output = {}
        output['id'] = tweet['id_str']
        created_at = dateutil.parser.parse(tweet['created_at'])
        output['created_at'] = created_at.strftime('%Y-%m-%d %H:%M:%S')
        if ('extended_tweet' in tweet
                and 'full_text' in tweet['extended_tweet']):
            output['text'] = tweet['extended_tweet']['full_text']
        else:
            output['text'] = tweet['text']
        
        keys = ['lang', 'coordinates', 'source']
        for key in keys:
            if tweet.get(key) != None:
                output[key] = tweet[key]
        keys = ['favorite_count', 'retweet_count', 'quote_count',
                    'reply_count']
        for key in keys:
            if tweet.get(key) != None:
                if 'interactions' not in output:
                    output['interactions'] = {}
                output['interactions'][key] = tweet[key]
        output['crawler'] = 'streaming'
        
        if GOOGLE_CLOUD_PROJECT == "False":
            self.db[MONGODB_COLLECTION].insert_one(output)
            id = output.get('_id', '')
        else:
            gcp_utils.upload_data_to_bq(self.db, [output])
            id = output.get('id', '')

        if id:
            self.tweet_ids.append(id)
            self.count += 1
        
        message = "STREAMING | Tweet '{}' saved to db.".format(str(id))
        print(message)
        logging.info(message)
        
    def on_connect(self):
        """
        Method which runs whenever a new streaming connection is created.
        """

        message = 'STREAMING | IKEAStreamingCrawler connected.' 
        print(message)
        logging.info(message)
        
    def on_disconnect(self):
        """
        Method which runs whenever a new streaming connection is closed.
        """

        message = 'STREAMING | IKEAStreamingCrawler disconnected.'
        print(message)
        logging.info(message)
        
    def on_exception(self, exception: Exception):
        """Method which runs whenever a exception occurs.

        Parameters
        ----------
        exception: Exception
            Exception which has ocurred.
        """

        print(exception)
        logging.error(exception)