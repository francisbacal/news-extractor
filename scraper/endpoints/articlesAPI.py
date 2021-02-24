from urllib.parse import urlparse
from bson import json_util
from options import *
from ..exceptions import ArticlesAPIError

import json, datetime, requests


class ArticlesAPI:
    """
    Articles Endpoint
        @params:  
            options       -   Options class object
            **kwargs      -   Other arguments to extend to options
    """
    def __init__(self, options=None, **kwargs):
        self.options = Options()
        self.options = extend_opt(self.options, kwargs)
        self.headers = {"Content-Type": "application/json", "Authorization": self.options.token}

    def add(self, payload: dict={}):
        """
        Add new article in the database
            @params:
                payload         -   dict object containing article data
        """
        endpoint = self.options.get_endpoint('article')

        if not payload:
            return ArticlesAPIError("No article data to add")

        payload['date_created'] = datetime.datetime.now().isoformat()

        try:
            response = requests.post(endpoint, data=json.dumps(payload, default=json_util.default), headers=self.headers)

            if str(response.status_code).startswith('5'):
                if 'error' in response.json():
                    try:
                        if response.json()['error']['code'] == 11000:
                            raise ArticlesAPIError(f"Duplicate value for {payload['article_url']}")
                        else:
                            err_code = response.json()['error']['code']
                            err_name = response.json()['error']['name']
                            err_msg = f"An error occurred while adding article: {err_name} with code {err_code}"

                            raise APIServerError(err_msg)
                    except:
                        raise ArticlesAPIError("Error while adding website")
            else:
                raise ArticlesAPIError("Error while adding website")
        
        except:
            raise ArticlesAPIError("Error while adding website")

    def get(self, query={}, **kwargs):
        """
        Method to get article links form database based on query
            @params:
                query       -   dict object payload query
        """

        self.options = extend_opt(self.options, kwargs)
        endpoint = self.options.get_endpoint('article-custom')
        params = {'limit': self.options.limit}

        try:
            response = requests.post(endpoint, params=params, data=json.dumps(query, default=json_util.default), headers=self.headers)
            result = response.json()['data']

            return result
        except:
            raise

    def get_one(self, _id: str):
        """
        Method to get one article link from database by id
            @params:  
                id        -   ID of article link to get
        """
        endpoint = f"{self.options.get_endpoint('article')}/{_id}"
        try:
            response = requests.get(endpoint, headers=self.headers)
            result = response.json()['data']

            return result
        
        except:
            raise
    
    def update(self, _id: str, query:dict):
        """
        Method to update article link in database
            @params:  
                _id        -   String ID of article link to update
                query      -   dict object containing payload to update
        """
        endpoint = f"{self.options.get_endpoint('article')}/{_id}"

        if 'updated_by' not in query:
            query['updated_by'] = "Python Global Scraper"
        
        query['date_updated'] = datetime.datetime.now().isoformat()

        try:
            response = requests.put(endpoint, data=json.dumps(query), headers=self.headers)
            result = response.json()['data']

            return result

        except:
            raise

    def counts(self, query={}, **kwargs):
        """
        Method to count number of article links based on payload query
            @params:  
                body        -   dict object containing payload query to count
                **kwargs    -   Additional arguments to extend to options
        """

        self.options = extend_opt(self.options, kwargs)
        endpoint = self.options.get_endpoint('article-count')


        try:
            response = requests.post(endpoint, data=json.dumps(query, default=json_util.default), headers=self.headers)
            result = response.json()['data']

            return result

        except:
            raise