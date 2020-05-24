#!/usr/bin/env python

from itertools import islice
from tweet_processor import TweetProcessor
from couch_setup import CouchDBInstance

couch_db = CouchDBInstance()

def insert_to_couch(tweet):
    status = tweet_processor.process_status(status)
        if status == None:
            return True
        couchdb.insertTweet(status)

if __name__ == "__main__":
    
    DATASET = 'twitter-melb.json'
    
    with open(DATASET, 'r', encoding='utf-8') as f:
        for line in islice(f, 1):
            try:
                insert_to_couch(json.loads(line.rstrip(",\n")))
            except ValueError:
                print("End of file.\n")
                break
    
    