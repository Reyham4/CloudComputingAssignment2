import pycurl, datetime, json, sys, os
from io import BytesIO
from urllib.parse import urlencode
from twitter_harvester.tweet_processor import TweetProcessor
from couch_setup import CouchDBInstance
import time

import pathlib
path = str(pathlib.Path(__file__).parent.absolute())


def retrieve_tweets(city, start_year, start_month, start_day, end_year, end_month, end_day, id):
	buffer = BytesIO()


	end_key = [city, start_year, start_month, start_day]
	start_key = [city, end_year, end_month, end_day]
	retries = 100
	vals = {'start_key' : start_key,
			'reduce':"false",
			'include_docs':"true",
			'descending':"true",
			'limit': 100}

	if id is not None:
		vals['start_key_doc_id'] = id

	params_ = urlencode(vals)
	# weirdly, urllib uses single quotes to encase strings, but couch needs double quotes. took me forever to debug :(

	params = params_.replace('%27', '%22')
	url = "http://45.113.232.90/couchdbro/twitter/_design/twitter/_view/summary"
	c = pycurl.Curl()
	# print(params)

	c.setopt(c.URL, url+"?"+params)
	c.setopt(c.HTTPGET, 1)
	c.setopt(c.USERPWD,"readonly:ween7ighai9gahR6")
	c.setopt(c.WRITEDATA, buffer)
	c.perform()
	c.close()

	return json.loads(buffer.getvalue().decode('utf-8'))

def read_id(city):

	try:
		with open(path + "/cloud_skip/" + city + "_offset", "r") as f:
			x = int(f.read().strip())
			return x
	except (IOError, ValueError) as e:
		print(e)
		return None


def write_id(city, id):
	try:
		with open(path + "/cloud_skip/" + city + "_offset", "w") as f:
			f.write(str(id))
	except IOError:
		return None

def harvest_cloud_city_tweets(city, tp):
	if not os.path.exists(path + '/cloud_skip/' + city + "_offset"):
		with open(path + '/cloud_skip/' + city + "_offset", 'w'): pass

	limit = 50
	couchdb = CouchDBInstance()
	tp = TweetProcessor()

	start_year, start_month, start_day = 2020,1,1
	now = datetime.datetime.now() - datetime.timedelta(days=5)
	# past = now - datetime.timedelta(days=1)
	print("current time", now)

	max_id = read_id(city)
	#if max_id is None:
	#    max_id = 9223372036854775807
	print(max_id)

	print('harvesting tweets for city: ', city)

	res = retrieve_tweets(city, start_year, start_month, start_day, now.year, now.month, now.day, max_id)
	# print(res)
	if res == None or 'rows' not in res:
		print("Cannot retrieve tweets for ", city)
		return None

	ids = [int(x['doc']['_id']) for x in res['rows']]
	max_id = min(ids)
	res_ = [x for x in res['rows'] if int(x['doc']['_id']) != max_id]
	# print(max_id, "MINID")

	seen = set()
	seen.add(max_id)

	# process and insert tweets into couchdb
	# pagination is way too slow so we have to make do with keys
	while ('rows' in res and len(res['rows']) > 1):
		#res_ = list(filter(lambda x: int(x['doc']['_id']) != max_id, res['rows']))
		for tweet in res_:
			#print(tweet['doc']['_id'], "RES")
			intid = int(tweet['doc']['_id'])
			if intid != max_id:
				processed_tweet = tp.process_archived_status(tweet)
				if processed_tweet is not None:
					#print(processed_tweet)
					couchdb.insertTweet(processed_tweet)
		# print(city, max_id, "NEWMAX")

		res = retrieve_tweets(city, start_year, start_month, start_day, now.year, now.month, now.day, max_id)
		write_id(city, max_id)

		res_ = [x for x in res['rows'] if int(x['doc']['_id']) != max_id]
		ids = [int(x['doc']['_id']) for x in res_]
		max_id = sorted(set(ids))[0] # min id
		if max_id in seen:
			delta = datetime.timedelta(days=1)
			now = now - delta
			print("new time:", city, now)

			seen = set()
		else:
			seen.add(max_id)



# harvest_cloud_city_tweets("hobart", TweetProcessor("search"))
