from .article_url import ArticleURL
from .media_url import MediaURL
from .compare import Compare
from .logging import init_log
from .stopwords import Stopwords
from .variables import *
from unidecode import unidecode

import random, time, traceback, requests

#---------- UNICODE ----------#
def unicode(text: str):
    """
    Returns a unidecoded str
    """

    return unidecode(text).strip()


#---------- RANDOM SLEEP ----------#
def rand_sleep(min: int=5, max: int=10):
    """
    Sleep method at random seconds
        @params:
            min         -   Minimum seconds
            max         -   Max seconds
    """
    RANDOM_SEC = random.randint(min, max)
    DIFF = random.randint(1, 2) - random.random()

    SLEEP_TIME = RANDOM_SEC - DIFF
    time.sleep(SLEEP_TIME)


#---------- ERROR CATCHER ----------#
errors = {'None': None, 'list': [], 'dict': {}, 'article_error': 'Error'}
def catch(default, func, handle=lambda e: e, *args, **kwargs):
    """
    Catching errors
        @params:
            default   - Required    : key values on error dict - 'None', 'list', 'dict' (String)
            func      - Required    : lambda handle (Lambda Function)
    """
    try:
        return func(*args, **kwargs)
        
    except Exception as e:
        # log.error(e)
        # print(traceback.format_exc())
        return errors[default]

#---------- RECURSIVE TAG ITERATOR ----------#
def recursive_iterate(tags):
    """
    Iterate list for nested list. Returns a single list instance
        @params:
            tags            -   bs4 element tag to iterate
    """
    result = []
    for tag in tags:
        if isinstance(tag, list):
            recursive_iterate(tag)
        else:
            result.append(tag)
    return result

#---------- NAME_ENTITY ----------#
def name_entity(authors: list):
    """
    Calls name entity api to verify author list
    """

    if not isinstance(authors, list):
        raise TypeError("Authors must be a list")

    if not authors:
        return []

    filtered_authors = []

    for author in authors:
        url = 'http://192.168.3.113:8000/api/name_entity'
        headers = {"Content-Type" : "application/json", "Accept": "*/*",}
        payload = {"entity_filter": ["PERSON"] , "content": author, "entities_only" : True}

        try:
            response = requests.post(url, data=json.dumps(payload), headers=headers)
        
            if str(response.status_code).startswith('5'):
                raise APIServerError(url, response.status_code)

            json_response = response.json()
            data = json_response['data']

            if data:
                for d in data:
                    entity_group = d['entity_group']

                    if entity_group == 'PERSON':
                        author_result = d['entity_name']
                    else:
                        author_result = None

                    if author_result: 
                        if author_result not in filtered_authors:
                            filtered_authors.append(author_result)

        except Exception as e:
            continue
  
    if len(filtered_authors) > 2:
        return filtered_authors[0:2]
  
    return filtered_authors

