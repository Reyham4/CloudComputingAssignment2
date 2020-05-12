import pycurl, datetime, json
from io import BytesIO
from urllib.parse import urlencode
from tweet_processor import TweetProcessor
from couch_setup import CouchDBInstance


def retrieve_tweets(city, limit, skip):
    buffer = BytesIO()

    start_year, start_month, start_day = 2014, 1, 1
    now = datetime.datetime.now()
    end_year, end_month, end_day = now.year, now.month, now.day

    start_key = [city, start_year, start_month, start_day]
    end_key = [city, end_year, end_month, end_day]

    vals = {'start_key' : start_key,
            'end_key':end_key,
            'reduce':"false",
            'include_docs':"true",
            'limit': limit}
    if skip != 0:
        vals['skip'] = skip

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



def harvest_cloud_city_tweets(city, tp):
    limit = 500
    skip_count = 0
    couchdb = CouchDBInstance()

    # check if offset exists
    with open("./cloud_skip/" + city + "_offset.txt", "w+") as f:
        o = f.read().strip()
        if o != "":
            try:
                skip_count = int(o)
            except ValueError:
                skip_count = 0
        f.close()

    print('harvesting tweets for city: ', city)
    res = retrieve_tweets(city, limit, skip_count)
    while len(res['rows']) != 0:
        print('new_iter')
        # process and insert tweets into couchdb
        for tweet in res['rows']:
            processed_tweet = tp.process_archived_status(tweet)
            if processed_tweet is None:
                continue
            couchdb.insertTweet(processed_tweet)

        skip_count += limit
        with open("./cloud_skip/" + city + "_offset.txt", "w+") as f:
            f.write(str(skip_count))
            f.close()

        res = retrieve_tweets(city, limit, skip_count) # paginate