from requests_oauthlib import OAuth1
from bs4 import BeautifulSoup
import requests
import json
import secrets 

url = "https://www.worldwildlife.org"
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
    def __init__(self, name, status, description, scientific_name, weight, length, habitats):
        self.name = name
        self.status = status
        self.description = description
        self.scientific_name = scientific_name
        self.weight = weight
        self.length = length
        self.habitats = habitats
    def info(self):
        return "{} ({}): The species living in {} is {}.".format(self.name, self.scientific_name, self.habitats, self.status)

def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    species_url_dic = {}
    species_list = []
    url_list = []
    searching_div = soup.find(id = 'content')

    child_divs = searching_div.find_all('ul', class_='masonry')
    for c_div in child_divs:
        c_link = c_div.find_all('a')
        for header in c_link:
            species_name = header.text
            species_list.append(species_name.lower())
        for link in c_link:
            c_path = link['href']
            url_path = 'https://www.worldwildlife.org' + c_path
            url_list.append(url_path)
    species_url_dic = {species_list[i]: url_list[i] for i in range(len(species_list))} 
    return species_url_dic

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    response = requests.get(site_url)
    response = make_request_with_cache(site_url)
    soup = BeautifulSoup(response, "html.parser")

    try:
        species_name = soup.find('li', class_='current').text.strip()
    except:
        species_name = 'No Name'

    try:
        species_status = soup.find('div', class_='container').text.strip()
    except:
        species_status = 'No Status'

    try:
        species_description = soup.find('div', class_='wysiwyg lead').text.strip()
    except:
        species_description = 'No Description'

    try: 
        species_scientific_name = soup.find('em').text.strip()
    except: 
        species_scientific_name = 'No Scientific Name'

    try:
        species_weight = soup.find('div', class_='container').text.strip()
    except:
        species_weight = 'No Weight'

    try:
        species_length = soup.find('div', class_='container').text.strip()
    except:
        species_length = 'No Length'  

    try:
        species_habitats = soup.find('div', class_='container').text.strip()
    except:
        species_habitats = 'No Habitat'

    instance_species_site = WWFSite(species_name, species_status, species_description, species_scientific_name, species_weight, species_length, species_habitats)
    return instance_species_site
# what if the class names are the same across different search items 

#populate database

import sqlite3

db_name = 'goodreads_reviews_title.sqlite'

def create_db():
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    
    drop_reviews = '''
        DROP TABLE IF EXISTS "Reviews";
    '''

    create_reviews_sql = '''
        CREATE TABLE IF NOT EXISTS 'Reviews'(
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "Title" TEXT NOT NULL,
            "publicationYear" INTEGER NOT NULL,
            "Country" TEXT NOT NULL,
            "reviewsCount" INTEGER NOT NULL,
            "ratingsSum" INTEGER NOT NULL,
            "ratingsCount" INTEGER NOT NULL
        )
    '''
    cur.execute(drop_reviews)
    cur.execute(create_reviews_sql)

    conn.commit()
    conn.close()

# create_db()

def load_reviews():
    base_url = 'https://www.goodreads.com/book/title.json'
    reviews = requests.get(base_url, auth=oauth).json()

    insert_sql = '''
        INSERT INTO Reviews
        VALUES (NULL, ?, ?, ?, ?, ?, ?)
    '''
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    for review in reviews:
        cur.execute(insert_sql,
            [
                review['title'],
                review['original_publication_year'],
                review['country_code'],
                review['reviews_count'],
                review['ratings_sum'],
                review['ratings_count']
            ]
        )
    conn.commit()
    conn.close()

create_db()
load_reviews()
