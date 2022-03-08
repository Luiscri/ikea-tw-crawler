import os
import json
from google.cloud import bigquery

from flask import Flask, request, jsonify, make_response
from flask_pymongo import PyMongo

import utils.mongo_utils as mongo_utils
import utils.gcp_utils as gcp_utils
from modules.IKEABatchCrawler import IKEABatchCrawler
from modules.IKEAStreamingCrawler import IKEAStreamingCrawler

API_KEY = os.environ['API_KEY'].strip()
API_SECRET = os.environ['API_SECRET'].strip()
ACCESS_TOKEN = os.environ['ACCESS_TOKEN'].strip()
ACCESS_SECRET = os.environ['ACCESS_SECRET'].strip()
GOOGLE_CLOUD_PROJECT = os.environ.get('GOOGLE_CLOUD_PROJECT')

app = Flask(__name__)
# Check the environment where the project has been deployed
if GOOGLE_CLOUD_PROJECT == "False":
    app.config["MONGO_URI"] = ('mongodb://' + os.getenv('MONGODB_USERNAME')
                            + ':' + os.environ.get('MONGODB_PASSWORD') + '@'
                            + os.environ.get('MONGODB_HOSTNAME') + ':27017/'
                            + os.environ.get('MONGODB_DATABASE'))
    mongo = PyMongo(app)
    db = mongo.db
else:
    db = bigquery.Client()

streaming_crawler = IKEAStreamingCrawler(
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_SECRET,
    db=db
)
batch_crawler = IKEABatchCrawler(
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_SECRET,
    db=db
)

confirmation_response = {
    'status': 200,
    'message': 'OK'
}

@app.route('/')
def index():
    """Index route.
    
    get:
        description: checks the server status.
        responses:
            200:
                description: welcome message.
    """
    
    return jsonify(
        status=200,
        message='Welcome to the IKEA crawler!'
    )
    
@app.route('/stream/status')
def get_status():
    """/stream/status route.
    
    get:
        description: checks the stream status.
        responses:
            200:
                description: boolean indicating the stream status.
    """

    return jsonify(
        status=200,
        message=streaming_crawler.running
    )

@app.route('/stream/start', methods=['POST'])
def start_stream():
    """/stream/start route.
    
    post:
        description: creates a new stream connection.
        parameters:
            - name: track
              description: comma separated list of terms to search.
              required: true
    """

    try:
        data = request.get_json()
        track = data.get('track', None)
        if not track:
            return jsonify(
                code=400,
                message="Missing required argument: 'track'."
            )
        streaming_crawler.count = 0
        streaming_crawler.tweet_ids = []
        streaming_crawler.filter(
            track=track.split(','), threaded=True
        )
        return jsonify(confirmation_response)
    except Exception as e:
        print(e)
        return jsonify(
            status=500,
            message='Interval server error: disconnected.'
        )
    
@app.route('/stream/stop', methods=['POST'])
def stop_stream():
    """/stream/stop route.
    
    post:
        description: closes a previously created stream connection.
    """

    try:
        streaming_crawler.disconnect()
        return jsonify(confirmation_response)
    except Exception as e:
        print(e)
        return jsonify(
            status=500,
            message='Interval server error: disconnected.'
        )

@app.route('/stream/tweets')
def get_stream_tweets():
    """/stream/tweets route.
    
    get:
        description: get the tweets collected by the stream.
        responses:
            200:
                description: list of tweets collected by the stream.
    """

    if GOOGLE_CLOUD_PROJECT == "False":
        tweets = list(mongo_utils.get_by_ids(db, streaming_crawler.tweet_ids))
    else:
        tweets = gcp_utils.get_by_ids(db, streaming_crawler.tweet_ids)
    return jsonify(
        status=200,
        message=json.dumps(tweets)
    )
    
@app.route('/stream/count')
def get_stream_count():
    """/stream/count route.
    
    get:
        description: get the number of tweets collected by the stream.
        responses:
            200:
                description: number of tweets collected by the stream.
    """

    return jsonify(
        status=200,
        message=streaming_crawler.count
    )

@app.route('/batch/crawl', methods=['POST'])
def batch_crawl():
    """/batch/crawl route.
    
    post:
        description: starts a batch process to download the tweets.
        parameters:
            - name: query
              description: query of terms that the tweets must match.
              required: true
            - name: lang
              description: language in which the tweets must be written.
              required: false
            - name: count
              description: number of tweets to be retrieved.
              required: false
            - name: until
              description: limit date to retrieve tweets from.
              required: false
    """

    try:
        data = request.get_json()
        query = data.get('query', None)
        if not query:
            return jsonify(
                code=400,
                message="Missing required argument: 'query'."
            )
        lang = data.get('lang', None)
        count = data.get('count', None)
        until = data.get('until', None)
        batch_crawler.crawl_tweets(
            query=query, lang=lang, count=count, until=until
        )
        return jsonify(confirmation_response)
    except Exception as e:
        print(e)
        return jsonify(
            status=500,
            message='Interval server error: disconnected.'
        )

@app.route('/batch/tweets')
def get_batch_tweets():
    """/batch/tweets route.
    
    get:
        description: get the tweets collected by the batch process.
        responses:
            200:
                description: list of tweets collected by the batch process.
    """

    if GOOGLE_CLOUD_PROJECT == "False":
        tweets = list(mongo_utils.get_by_ids(db, batch_crawler.tweet_ids))
    else:
        tweets = gcp_utils.get_by_ids(db, batch_crawler.tweet_ids)
    return jsonify(
        status=200,
        message=json.dumps(tweets)
    )

@app.route('/batch/count')
def get_batch_count():
    """/batch/count route.
    
    get:
        description: get the number of tweets collected by the batch process.
        responses:
            200:
                description: number of tweets collected by the batch process.
    """

    return jsonify(
        status=200,
        message=batch_crawler.count
    )
    
if __name__ == '__main__':
    ENVIRONMENT_DEBUG = os.environ.get('APP_DEBUG', True)
    ENVIRONMENT_PORT = os.environ.get('APP_PORT', 5000)
    app.run(host='0.0.0.0', port=ENVIRONMENT_PORT, debug=ENVIRONMENT_DEBUG)