import twitter
import json
import itertools
import networkx as nx

def oauth_login():
    CONSUMER_KEY = '3Qx0nlRZJI3O8Sr8zafcR554E'
    CONSUMER_SECRET = '7d8uMNhVEpNukl3bLrTZ2YDWkXlRnMeefQWDQA104CrYAwD02s'
    OAUTH_TOKEN = '1367551327337918470-dOeyx24LbVbOBGWQBV3kp5DvFrhwye'
    OAUTH_TOKEN_SECRET = '65Ztwrt3r9iP206GAxhPOotP4CVWmsXXKzifspy766PF1'

    auth = twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
    twitter_api = twitter.Twitter(auth=auth)
    print(twitter_api)
    return twitter_api

twitter_api = oauth_login()

from functools import partial
from sys import maxsize as maxint


def get_friends_followers_ids(twitter_api, screen_name=None, user_id=None,
                              friends_limit=maxint, followers_limit=maxint):
    # Must have either screen_name or user_id (logical xor)
    assert (screen_name != None) != (user_id != None), "Must have screen_name or user_id, but not both"

    # See http://bit.ly/2GcjKJP and http://bit.ly/2rFz90N for details
    # on API parameters

    get_friends_ids = partial(make_twitter_request, twitter_api.friends.ids,
                              count=5000)
    get_followers_ids = partial(make_twitter_request, twitter_api.followers.ids,
                                count=5000)

    friends_ids, followers_ids = [], []

    for twitter_api_func, limit, ids, label in [
        [get_friends_ids, friends_limit, friends_ids, "friends"],
        [get_followers_ids, followers_limit, followers_ids, "followers"]
    ]:

        if limit == 0: continue

        cursor = -1
        while cursor != 0:

            # Use make_twitter_request via the partially bound callable...
            if screen_name:
                response = twitter_api_func(screen_name=screen_name, cursor=cursor)
            else:  # user_id
                response = twitter_api_func(user_id=user_id, cursor=cursor)

            if response is not None:
                ids += response['ids']
                cursor = response['next_cursor']

            print('Fetched {0} total {1} ids for {2}'.format(len(ids), label, (user_id or screen_name)),
                  file=sys.stderr)

            # XXX: You may want to store data during each iteration to provide an
            # an additional layer of protection from exceptional circumstances

            if len(ids) >= limit or response is None:
                break

    # Do something useful with the IDs, like store them to disk...
    return friends_ids[:friends_limit], followers_ids[:followers_limit]


import sys
import time
from urllib.error import URLError
from http.client import BadStatusLine
import json
import twitter


def make_twitter_request(twitter_api_func, max_errors=10, *args, **kw):
    # A nested helper function that handles common HTTPErrors. Return an updated
    # value for wait_period if the problem is a 500 level error. Block until the
    # rate limit is reset if it's a rate limiting issue (429 error). Returns None
    # for 401 and 404 errors, which requires special handling by the caller.
    def handle_twitter_http_error(e, wait_period=2, sleep_when_rate_limited=True):

        if wait_period > 3600:  # Seconds
            print('Too many retries. Quitting.', file=sys.stderr)
            raise e

        # See https://developer.twitter.com/en/docs/basics/response-codes
        # for common codes

        if e.e.code == 401:
            print('Encountered 401 Error (Not Authorized)', file=sys.stderr)
            return None
        elif e.e.code == 404:
            print('Encountered 404 Error (Not Found)', file=sys.stderr)
            return None
        elif e.e.code == 429:
            print('Encountered 429 Error (Rate Limit Exceeded)', file=sys.stderr)
            if sleep_when_rate_limited:
                print("Retrying in 15 minutes...ZzZ...", file=sys.stderr)
                sys.stderr.flush()
                time.sleep(60 * 15 + 5)
                print('...ZzZ...Awake now and trying again.', file=sys.stderr)
                return 2
            else:
                raise e  # Caller must handle the rate limiting issue
        elif e.e.code in (500, 502, 503, 504):
            print('Encountered {0} Error. Retrying in {1} seconds'.format(e.e.code, wait_period), file=sys.stderr)
            time.sleep(wait_period)
            wait_period *= 1.5
            return wait_period
        else:
            raise e

    # End of nested helper function

    wait_period = 2
    error_count = 0

    while True:
        try:
            return twitter_api_func(*args, **kw)
        except twitter.api.TwitterHTTPError as e:
            error_count = 0
            wait_period = handle_twitter_http_error(e, wait_period)
            if wait_period is None:
                return
        except URLError as e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print("URLError encountered. Continuing.", file=sys.stderr)
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.", file=sys.stderr)
                raise
        except BadStatusLine as e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print("BadStatusLine encountered. Continuing.", file=sys.stderr)
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.", file=sys.stderr)
                raise


def get_user_profile(twitter_api, screen_names=None, user_ids=None):
    # Must have either screen_name or user_id (logical xor)
    assert (screen_names != None) != (user_ids != None), "Must have screen_names or user_ids, but not both"

    items_to_info = {}

    items = screen_names or user_ids

    while len(items) > 0:

        # Process 100 items at a time per the API specifications for /users/lookup.
        # See http://bit.ly/2Gcjfzr for details.

        items_str = ','.join([str(item) for item in items[:100]])
        items = items[100:]

        if screen_names:
            response = make_twitter_request(twitter_api.users.lookup,
                                            screen_name=items_str)
        else:  # user_ids
            response = make_twitter_request(twitter_api.users.lookup,
                                            user_id=items_str)

        for user_info in response:
            if screen_names:
                items_to_info[user_info['screen_name']] = user_info
            else:  # user_ids
                items_to_info[user_info['id']] = user_info

    return items_to_info
 #############################################################################
 #############################################################################
##############################################################################
# EVERYTHING BELOW IS MY OWN CODE

#1: Selected my friend Alex Capurro as the starting point for the assignment
friends_ids, followers_ids = get_friends_followers_ids(twitter_api, screen_name="AlexCapurro3", friends_limit=200, followers_limit=200)


#2: With the function in #1, it created a list of friends and followers of my selected user
print('Friend IDs:' + '\n\n')
print(friends_ids)
print('\n\n' +'Follower IDs:' + '\n\n')
print(followers_ids)

#3: used example to retrieve reciprocal friends of selected user
reciprocal_friends = set(friends_ids) & set(followers_ids)

print('\n\n' + 'Reciprocal Friends:' +'\n\n')
print(reciprocal_friends)


#4: in order to get popular friends, had to retrieve the profile of reciprocal friends to find number of followers
response = get_user_profile(twitter_api, user_ids=list(reciprocal_friends))
# used response to put reciprocals into a dictionary and sorted by follower count
popular_friends = {}
for n in reciprocal_friends:
    popular_friends[n] = response[n]["followers_count"]
popular_friends = (sorted(popular_friends.items(), key=lambda item: item[1], reverse=True))

#used below function to retrieve first 5 items in the dictionary and set the dictionary equal to only those top5 most popular
from itertools import islice

def take(n, iterable):
    #"Return first n items of the iterable as a list"
    return dict(islice(iterable, n))

popular_friends = (take(5, popular_friends))
print("\n\nTop 5 popular friends:")
print(popular_friends)

#5, #6, and #7: Started the crawler with the top5 most popular reciprocal friends of the selected user


crawl_results = {} # for crawl results
depth = 1
maxdepth = 4

# queue is the first dictionary the crawler will go through
queue = popular_friends

# initialize network with selected user as the start and add the top5 popular friends to the network
G = nx.Graph()
G.add_node("AlexCapurro3")
for id in queue:
    G.add_node(id)
    G.add_edge("AlexCapurro3", id)

#crawler will run as long maxdepth is not reached or the length of the crawl results is not over 100 ids
while depth < maxdepth and len(crawl_results) < 100:

    #initialized next queue item which will be the next dictionary that will be used for the crawler
    nextqueue = {}

    # for loop to individually get user data from each ID
    for id in queue.keys():

        #print statements to check progress
        print("Current crawl results: ")
        print(crawl_results)
        print("Current nodes: ")
        print(G.number_of_nodes())

        #repeating previous steps to get top5 popular reciprocal friends
        friends_ids, followers_ids = get_friends_followers_ids(twitter_api, user_id=id, friends_limit=10000, followers_limit=10000)
        reciprocal_friends2 = set(friends_ids) & set(followers_ids)
        response = get_user_profile(twitter_api, user_ids=list(reciprocal_friends2))
        popular_friends2 = {}
        for n in reciprocal_friends2:
            popular_friends2[n] = response[n]["followers_count"]
        popular_friends2 = (sorted(popular_friends2.items(), key=lambda item: item[1], reverse=True))
        top5 = take(5, popular_friends2)

        #go through the current top5 popular and add the users to the nextqueue and the top5 to the current network along with edges in the correct places
        for n in top5.keys():
            nextqueue[n] = top5[n]
            if not G.has_node(n):
                G.add_node(n)
            G.add_edge(id,n)
            if n not in crawl_results.keys(): #checking for duplicates in crawl results
                crawl_results[n] = top5[n]

    # setting queue to nextqueue for next depth level
    queue = nextqueue
    depth += 1

print("Number of nodes: ")
print(G.number_of_nodes())
print("\nNumber of edges: ")
print(G.number_of_edges())
print("\nNetwork diameter: ")
print(nx.diameter(G))
print("\nNetwork average distance: ")
print(nx.average_shortest_path_length(G))
print("\nCrawl results: ")
print(crawl_results)


