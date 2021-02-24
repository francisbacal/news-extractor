from .exceptions import APIServerError
from options import *
import requests, json, datetime

class MediaValues:
    def __init__(self, website_id: str, body: dict={}, options=None):

        body_keys = ['text', 'images', 'videos']

        for key, val in body.items():
            if key not in body_keys:
                raise APIServerError(f"Error in Key {key} passed")

            if key == 'text': self.text = val or ""
            if key == 'images': self.images = val or []
            if key == 'videos': self.videos = val or []

        self.website_id = website_id
        self.options = options or Options()
        self.headers = {"Content-Type" : "application/json", "Authorization": self.options.token}
        self.global_value = 0
        self.local_value = 0
        self.website_cost = 0
        self.advalue = 0
        self.prvalue = 0

        self.__get_website_values()

        url = self.options.get_endpoint('lambda-article-media-value')

        data = {
            "global": self.global_value,
            "local": self.local_value,
            "website_cost": self.website_cost,
            "text": self.text,
            "images": self.images,
            "videos": self.videos
        }

        try:
            response = requests.post(url, data=json.dumps(data), headers=self.headers)

            self.__raise_errors(response, url)

            media_value = response.json()['data']

            if media_value:
                self.advalue = media_value['advalue']
                self.prvalue = media_value['prvalue']

        except:
            raise

    def __get_website_values(self):
        ws = Website()
        try:
            website = ws.get_one(self.website_id)
            self.global_value = website['alexa_rankings']['global']
            self.local_value = website['alexa_rankings']['local']
            self.website_cost = website['website_cost']
        except:
            pass

    def __raise_errors(self, response, url):

        if str(response.status_code).startswith('5'):
            if 'error' in response.json():
                try:
                    err_code = response.json()['error']['code']
                    err_name = response.json()['error']['name']
                    raise APIServerError(f"An error occurred while adding website: {err_name} with code {err_code}")
                except:
                    raise APIServerError("Error in response")
            else:
                raise APIServerError(f"Error while accesing {url}")

    @staticmethod
    def default():

        default = {
            "global": 0,
            "local": 0,
            "website_cost": 300,
            "text": "",
            "images": [],
            "videos": []
        }

        return default

    
