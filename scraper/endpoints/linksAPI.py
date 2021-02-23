from urllib.parse import urlparse
from bson import json_util
from options import *

import json


class LinksAPI:
    """
    Global Links Endpoint
        @params:  
            options       -   Options class object
            **kwargs      -   Other arguments to extend to options
    """
    def __init__(self, options=None, **kwargs):
        self.options = Options()
        self.options = extend_opt(self.options, kwargs)
        self.headers = {"Content-Type": "application/json", "Authorization": self.options.token}
    
    def get(self, query={}, **kwargs):
        """
        Method to get article links form database based on query
            @params:
                query       -   dict object payload query
        """

        self.options = extend_opt(self.options, kwargs)
        endpoint = self.options.get_endpoint('global-link-custom')
        params = {'limit': self.options.limit}

        
        try:
            response = requests.post(endpoint, params=params, data=json.dumps(query, default=json_util.default), headers=self.headers)
            result = result.json()['data']

            return result
        except:
            raise

    def get_one(self, _id: str):
        """
        Method to get one article link from database by id
            @params:  
                id        -   ID of article link to get
        """
        endpoint = f"{self.options.get_endpoint('global-link')}/{_id}"

        try:
            response = requests.get(endpoint, headers=self.headers)
            result = response.json()['data']

            return result
        
        except:
            raise
    
    def update(self, _id: str, query:dict):
        """
        Method to update link in database
            @params:  
                _id        -   String ID of link to update
                query      -   dict object containing payload to update
        """
        endpoint = f"{self.options.get_endpoint('global-link')}/{_id}"

        try:
            response = requests.put(url, data=json.dumps(body), headers=self.headers)
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
        endpoint = self.options.get_endpoint('global-link-count')


        try:
            response = requests.post(endpoint, data=json.dumps(query, default=json_util.default), headers=self.headers)
            result = response.json()['data']

            return result

        except:
            raise
    
    def check(self):
        """
        Checks article link if main website is not for scraping
        """