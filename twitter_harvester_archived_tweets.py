import pycurl, datetime, json, sys
from io import BytesIO
from urllib.parse import urlencode
from tweet_processor import TweetProcessor
from couch_setup import CouchDBInstance
import time



def retrieve_tweets(city, start_year, start_month, start_day, end_year, end_month, end_day, id):
    buffer = BytesIO()


    start_key = [city, start_year, start_month, start_day]
    end_key = [city, end_year, end_month, end_day]
    retries = 100
    vals = {'start_key' : start_key,
            'end_key':end_key,
            'reduce':"false",
            'include_docs':"true",
            'limit': 100}

    if id is not None:
        vals['start_key_doc_id'] = id

    params_ = urlencode(vals)
    # weirdly, urllib uses single quotes to encase strings, but couch needs double quotes. took me forever to debug :(

    params = params_.replace('%27', '%22')
    url = "http://45.113.232.90/couchdbro/twitter/_design/twitter/_view/summary"
    c = pycurl.Curl()


    c.setopt(c.URL, url+"?"+params)
    c.setopt(c.HTTPGET, 1)
    c.setopt(c.USERPWD,"readonly:ween7ighai9gahR6")
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()
    return json.loads(buffer.getvalue().decode('utf-8'))
    '''
    while retries > 0:
        try:
            c.perform()
            success = True
        except pycurl.error:
            retries -= 1
            time.sleep(5)
            print(pycurl.error)
    if success:
        return json.loads(buffer.getvalue().decode('utf-8'))
    else:
        return None
    '''

def read_id(city):
    try:
        with open("./cloud_skip/" + city + "_offset", "a+") as f:
            x = int(f.read().strip())
            return x
    except (IOError, ValueError) as e:
        print(e)
        return None


def write_id(city, id):
    try:
        with open("./cloud_skip/" + city + "_offset", "w+") as f:
            f.write(str(id))
    except IOError:
        return None

def harvest_cloud_city_tweets(city, tp):
    limit = 50
    couchdb = CouchDBInstance()

    start_year, start_month, start_day = 2020,1,1
    now = datetime.datetime.now()
    # past = now - datetime.timedelta(days=1)

    max_id = read_id(city)
    if max_id is None:
        max_id = 0

    print('harvesting tweets for city: ', city)

    res = retrieve_tweets(city, start_year, start_month, start_day, now.year, now.month, now.day, max_id)

    if res == None or 'rows' not in res:
        print("Cannot retrieve tweets for ", city)
        return None

    # process and insert tweets into couchdb
    # pagination is way too slow so we have to make do with keys
    while ('rows' in res and len(res['rows']) > 1):

        for tweet in res['rows']:
            _id = int(tweet['doc']['_id'])
            if _id > max_id:
                max_id = _id

        # identify and remove tweet with max_id
        res_ = list(filter(lambda x: x['doc']['_id'] != max_id, res['rows']))

        for tweet in res_:
            if tweet['doc']['id'] == str(max_id):
                print("ERROR BAD FUNC")
            # move out to process ALL TWEETS EXCEPT THE MAX ID TWEET
            processed_tweet = tp.process_archived_status(tweet)
            if processed_tweet is not None:
                couchdb.insertTweet(processed_tweet)

        # fetch new results, for the same day and city
        res = retrieve_tweets(city, start_year, start_month, start_day, now.year, now.month, now.day, max_id)
        write_id(city, max_id)


'''
vals = {'start_key' : ["adelaide", 2020, 1, 1],
        'end_key': ["adelaide", 2020, 5,1],
        'reduce':"false",
        'include_docs':"true",
        'start_doc_id':1212161563605356544,
        'limit': 10}

params_ = urlencode(vals)
# weirdly, urllib uses single quotes to encase strings, but couch needs double quotes. took me forever to debug :(

params = params_.replace('%27', '%22')
url = "http://45.113.232.90/couchdbro/twitter/_design/twitter/_view/summary"
c = pycurl.Curl()

c.setopt(c.URL, url+"?"+params)
c.setopt(c.HTTPGET, 1)
c.setopt(c.USERPWD,"readonly:ween7ighai9gahR6")
c.perform()
c.close()
'''
