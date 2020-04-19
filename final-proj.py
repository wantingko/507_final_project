from requests_oauthlib import OAuth1
from bs4 import BeautifulSoup
import requests
import json
import secrets 

url = "https://www.worldwildlife.org/"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

CACHE_FILENAME = "wwf_cache.json"
CACHE_DICT = {}

#key and secret 
client_key = secrets.GOODREADS_API_KEY
client_secret = secrets.GOODREADS_API_SECRET
oauth = OAuth1(client_key, client_secret=client_secret)

#building cache
def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 

def construct_unique_key(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and 
    repeatably identify an API request by its baseurl and params
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs
    
    Returns
    -------
    string
        the unique key as a string
    '''
    param_strings = []
    connector = '_'
    for k in params.keys():
        param_strings.append(f'{k}_{params[k]}')
    param_strings.sort()
    unique_key = baseurl + connector +  connector.join(param_strings)
    return unique_key

def make_request(baseurl, params):
    '''Make a request to the Web API using the baseurl and params
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dictionary
        A dictionary of param:value pairs
    
    Returns
    -------
    dict
        the data returned from making the request in the form of 
        a dictionary
    '''
    response = requests.get(baseurl, params=params, auth=oauth)
    return response.text

def make_request_with_cache(baseurl, params={}):
    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    hashtag: string
        The hashtag to search (i.e. "#2020election")
    count: int
        The number of tweets to retrieve
    
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    request_key = construct_unique_key(baseurl, params)
    if request_key in CACHE_DICT.keys():
        print("Using cache")
        return CACHE_DICT[request_key]
    else:
        print("Fetching")
        CACHE_DICT[request_key] = make_request(baseurl, params)
        save_cache(CACHE_DICT)
        return CACHE_DICT[request_key]
#finish building cache 
class WWFSite:
    '''a national site

    Instance Attributes
    -------------------
    add docstring!!!
    '''
    def __init__(self, category, name, status, description, scientific_name, weight, length, habitats):
        self.category = category
        self.name = name
        self.status = status
        self.description = description
        self.scientific_name = scientific_name
        self.weight = weight
        self.length = length
        self.habitats = habitats
    def info(self):
        return "{} ({}): The species living in {} is {}.".format(self.name, self.scientific_name, self.habitats, self.status)
