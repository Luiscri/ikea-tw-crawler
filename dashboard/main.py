import os
import json
import requests

from flask import Flask, render_template, request

CRAWLER_BASEURL = os.environ['CRAWLER_BASEURL'].strip()

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route('/')
def index():
    """Index route.

    get:
        description: renders the index page.
        responses:
            200:
                description: HTML page.
    """

    return render_template('index.html')

@app.route('/streaming', methods=['GET', 'POST'])
def streaming():
    """/streaming route

    get:
        description: renders the streaming page.
        responses:
            200:
                description: HTML page.
    post:
        description: sends the start/stop request to the crawler.
        parameters:
            - name: track
              description: comma separated list of terms to search.
              required: true
    """

    if request.method == 'POST':
        r = get_stream_status()
        status = json.loads(r.text).get('message')
        if status == False:
            track = request.form['track'].strip() or 'IKEA,#IKEA'
            start_stream(track)
        else:
            stop_stream()
    r = get_stream_status()
    status = json.loads(r.text).get('message')
    r = get_stream_tweets()
    tweets = json.loads(json.loads(r.text).get('message'))
    r = get_stream_count()
    count = json.loads(r.text).get('message')
    return render_template(
        'streaming.html', status=status, tweets=tweets, count=count
    )

@app.route('/batch', methods=['GET', 'POST'])
def batch():
    """/batch route.
    
    get:
        description: renders the batch page.
        responses:
            200:
                description: HTML page.
    post:
        description: sends the crawl request to the crawler.
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

    crawled = False
    if request.method == 'POST':
        query = request.form['query'].strip() or 'IKEA #IKEA'
        lang = request.form['lang'].strip() or None
        count = request.form['count'].strip() or None
        until = request.form['until'].strip() or None
        crawl_tweets(query, lang, count, until)
        crawled = True
    r = get_batch_tweets()
    tweets = json.loads(json.loads(r.text).get('message'))
    r = get_batch_count()
    count = json.loads(r.text).get('message')
    return render_template(
        'batch.html', crawled=crawled, tweets=tweets, count=count
    )

def start_stream(track: str):
    """Method which sends a request to the crawler to start the stream.

    Parameters
    ----------
    track: str
        comma separated list of terms to search.
    """

    data = {
        'track': track
    }
    url = '{}/stream/start'.format(CRAWLER_BASEURL)
    return requests.post(url, json=data)

def stop_stream():
    """
    Method which sends a request to the crawler to stop the stream.
    """

    url = '{}/stream/stop'.format(CRAWLER_BASEURL)
    return requests.post(url)

def get_stream_status():
    """
    Method which sends a request to the crawler to get the stream status.
    """

    url = '{}/stream/status'.format(CRAWLER_BASEURL)
    return requests.get(url)

def get_stream_tweets():
    """
    Method which sends a request to the crawler to get the stream tweets.
    """

    url = '{}/stream/tweets'.format(CRAWLER_BASEURL)
    return requests.get(url)

def get_stream_count():
    """
    Method which sends a request to the crawler to get the stream tweet count.
    """

    url = '{}/stream/count'.format(CRAWLER_BASEURL)
    return requests.get(url)

def crawl_tweets(query: str, lang: str, count: str, until: str):
    """Method which sends a request to the crawler to start the batch process.

    Parameters
    ----------
    query: str
        Defines the query which the tweets must match in order to be
        retrieved.
    lang: str
        Defines the language in which the tweets must be written in order
        to be retrieved.
    count: str
        The number of results to try and retrieve per page.
    until: str
        Returns tweets created before the given date. Date should be
        formatted as YYYY-MM-DD.
    """

    data = {
        'query': query,
        'lang': lang,
        'count': count,
        'until': until
    }
    url = '{}/batch/crawl'.format(CRAWLER_BASEURL)
    return requests.post(url, json=data)

def get_batch_tweets():
    """
    Method which sends a request to the crawler to get the batch tweets.
    """

    url = '{}/batch/tweets'.format(CRAWLER_BASEURL)
    return requests.get(url)

def get_batch_count():
    """
    Method which sends a request to the crawler to get the batch tweet count.
    """

    url = '{}/batch/count'.format(CRAWLER_BASEURL)
    return requests.get(url)