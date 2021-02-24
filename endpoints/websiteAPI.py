import requests, json, re, random, time, datetime
from options import *
from tld import get_tld
from newsextractor import Fetch, MediaURL, ArticleURL

from .exceptions import *

class WebsiteAPI:
    """
    Website class to connect to website database api. Contains methods for website checking
    """
    def __init__(self, options=None, **kwargs):
        """
        Initialization method
            @params:  
                options           -   Options class
                **kwargs          -   Additional arguments to extend to options
        """

        self.params = kwargs
        self.options = options or Options()
        self.headers = {"Content-Type" : "application/json", "Authorization": self.options.token}
        self._id = None
        self.name = None
        self.domain = None
        self.subdomain = None
        self.protocol = None
        self.netloc = None
        self.website_url = None
        self.tld = None
        self.website_icon_url = None
        self.html = None
        self.country = "Unknown"
        self.country_code = "NoC"
        self.website_type = "INTERNATIONAL_NEWS"
        self.for_scraping = False
        self.parsed = False
        self.duplicate = False
        self.checked = False
       
    def parse(self, article_url, html=None):
        """
        Initial parsing of website data:
            @params:  article_url       -   URL of website to be parsed.
            @params:  html              -   Source page of website for icon parsing. [Default: None]
        """
        self.__clean_website_url(article_url)

        if not html:
            raise WebsiteError("No page source passed to arguments")

        self.html = html

        # GET WEBSITE ICON IF SOURCE PAGE IS GIVEN
        if self.html:
            soup = BeautifulSoup(self.html, "html.parser")
            icon_tags = soup.find_all("link",{"rel":"icon"})
            
            #GET FROM LINK REL
            try:
                icon = icon_tags[0]['href']

            # ELSE TRY COMMON ICON SOURCE 'http://www.example.com/favicon.ico'
            except:
                icon = f"{self.website_url}/favicon.ico"
                try:
                    fetch_icon = Fetch(icon) # TRY TO CHECK IF EXISTS BY FETCHING URL
                    fetch_icon.download()
                    if str(fetch_icon.status_code) not in ['200']:
                        icon = None
                except:
                    icon = None

            if icon:
                website_icon_url = MediaURL(icon) # CLEAN ICON URL

                # VALIDATIONS
                if all([website_icon_url.scheme == '', website_icon_url.netloc == '']):
                    icon_url = f"{self.website_url}/{website_icon_url.link}"
                else:
                    icon_url = website_icon_url.link
            else:
                icon_url = None

            self.website_icon_url = icon_url
        
        else:
            raise WebsiteError('No page source')
        
        self.parsed = True # BOOLEAN SET TO TRUE AFTER PARSING

    def get_one(self, website_id: str=None):
        """
        Method to get a single website from database
            @params:  website_id          -   String ID of website in database
        """
        _id = website_id or self._id

        if not _id:
            return None
        
        url = f"{self.options.get_endpoint('web')}/{_id}"

        try:
            response = requests.get(url, headers=self.headers)

            self.__raise_errors(response, None, url)

            result = response.json()['data'][0]

            if not result:
                return None
            
            return result
        
        except:
            raise
    
    def get(self, body={}, **kwargs):
        """
        Method to get websites from database
            @params:  body        -   dict object containing payload query to get websites from database
            @params:  **kwargs    -   Additional arguments to extend to options
        """
        url = self.options.get_endpoint('web-custom')
        self.options = extend_opt(self.options, kwargs)
        params = {'limit': self.options.limit}

        try:
            response = requests.post(url, params=params, data=json.dumps(body), headers=self.headers)

            self.__raise_errors(response, body, url)

            result = response.json()['data']

            return result

        except:
            raise

    def check(self, article_url: str= None):
        """
        Method to check if website exists
        """
        if not self.parsed and not article_url:
            raise WebsiteError("Website not parsed")
        elif article_url:
            self.__clean_website_url(article_url)

        url = self.options.get_endpoint('web-custom')

        if self.fqdn:
            body = {
                "fqdn": self.fqdn
            }
        else:
            raise WebsiteError("Website not parsed")

        try:
            response = requests.post(url, data=json.dumps(body), headers=self.headers)

            self.__raise_errors(response, body, url)

            result = response.json()['data']
            self.checked = True

            if not result:
                return None

            
            self.name = result[0]['website_name']
            self._id = result[0]['_id']
            self.__is_to_scrape(_id=self._id)

            return self._id
        
        except:
            raise

    def add(self):
        """
        Method to add website to database
        """
        if not self.parsed:
            raise WebsiteError("Website not parsed")

        if not self.checked:
            self.check()

        # FINAL VALIDATION
        existing_id = self.__validate()
        if existing_id:
            duplicate_ws = self.get_one(website_id=existing_id)

            _same_url = duplicate_ws['website_url'] == self.website_url
            _same_fqdn = duplicate_ws['fqdn'] == self.fqdn

            if all([not _same_url, not _same_fqdn]):
                self._id = None
            
            if _same_url and not _same_fqdn:
                self.update(website_id=existing_id, body={"fqdn": self.fqdn})
            
        if not self._id:
            # INCLUDE SUB-DOMAIN IF NAME EXISTS
            self.__check_duplicates()
            if self.duplicate:
                if self.subdomain != "www":
                    self.name = f"{str(self.subdomain).capitalize()} {self.name}"
            
            # INCLUDE TLD EXTENSION IF NAME EXISTS
            self.__check_duplicates()
            if self.duplicate:
                _tld = re.sub(r"\.", " ", self.tld)
                _tld_arr = _tld.split(" ")
                _tld_arr = [w.capitalize() for w in _tld_arr]

                tld_clean = " ".join(_tld_arr)
                
                self.name = f"{self.name} {tld_clean}"

        url = self.options.get_endpoint('web')

        body = {
            "website_name": self.name,
            "website_icon_url": self.website_icon_url,
            "website_url": self.website_url,
            "website_cost": 300,
            "website_type": self.website_type,
            "country": self.country,
            "country_code": self.country_code,
            "fqdn": self.fqdn,
            "programming_language": "Python",
            "date_created": datetime.datetime.now().isoformat(),
            "date_updated": datetime.datetime.now().isoformat(),
            "created_by": "Python Global Scraper",
            "updated_by": "Python Global Scraper"
        }
        
        try:
            response = requests.post(url, data=json.dumps(body), headers=self.headers)
        
            self.__raise_errors(response, body, url)

            result = response.json()['data']

            self.__set_to_false()

            if not result:
                return None
            
            check_result = self.check()

            if check_result: 
                return check_result
            else:
                raise WebsiteError("Unknown error while adding website")
        
        except:
            raise

    def update(self, body: dict={}, website_id: str=None):
        """
        Method to update a website in the database
            @params:  body        -   dict object containing payload query to update
            @params:  website_id  -   String ID of website to be updated
        """
        if not body:
            raise WebsiteError("No valid data to be updated")
        
        url = f"{self.options.get_endpoint('web')}/{website_id}"

        body['date_updated'] = datetime.datetime.now().isoformat()

        try:
            response = requests.put(url, data=json.dumps(body), headers=self.headers)
        
            self.__raise_errors(response, body, url)

            result = response.json()['data']
            
            if not result:
                return None
            
            check_result = self.check()

            if check_result: 
                return check_result
            else:
                raise WebsiteError("Unknown error while updating website")
        
        except:
            raise

    def counts(self, body: dict={}, **kwargs):
        """
        Method to count websites in the database
            @params:  body          -   dict object containiing payload query to count
            @params:  **kwargs      -   Additional arguments to extend to options
        """
        self.options = extend_opt(self.options, kwargs)
        url = self.options.get_endpoint('web-count')

        try:
            response = requests.post(url, data=json.dumps(body, default=json_util.default), headers=self.headers)
            self.__raise_errors(response, body, url)

            result = response.json()['data']

            if not result:
                return None

            return result
        except:
            raise
    
    def __validate(self):
        """
        Private method to validate website duplicates
        """
        try:
            ws = self.get(body={"website_name": self.name})

            if not ws:
                ws = self.get(body={"fqdn": self.fqdn})

            if not ws:
                ws = self.get(body={"website_url": self.website_url})

            if not ws:
                self._id = None
                return None
            else:
                
                if len(ws) > 1:
                    self._id = None
                else:
                    return ws[0]['_id']
        except:
            raise

        def __set_to_false(self):
            """
            Private method to reset website attributes to False
            """
            self.parsed = False
            self.duplicate = False
            self.checked = False  

    def __raise_errors(self, response: type(requests), body: dict, url:str):
        """
        Private method to check requests response for errors
            @params:  response            -   requests response
            @params:  body                -   dict object containing query passed to requests for error logging
            @params:  url                 -   URL passed on requests
        """
        if str(response.status_code).startswith('5'):
            if 'error' in response.json():
                try:
                    if response.json()['error']['code'] == 11000:
                        raise DuplicateValue(body['website_url'])
                    else:
                        err_code = response.json()['error']['code']
                        err_name = response.json()['error']['name']
                        raise Exception(f"An error occurred while adding website: {err_name} with code {err_code}")
                except KeyError:
                    raise APIServerError(f"error occured at {url}, response: {response.status_code}")
            else:
                raise APIServerError(f"error occured at {url}, response: {response.status_code}")
        
        if str(response.status_code).startswith('4'):
            raise APIServerError(f"error occured at {url}, response: {response.status_code}")
        
    def __clean_website_url(self, article_url: str):
        """
        Private method to clean url of website
            @params:  article_url       -    url of website
        """
        _article_url = ArticleURL(article_url)
        
        try:
            ws = get_tld(_article_url.url, fix_protocol=True, as_object=True)
        except:
            ws = None

        self.protocol = "http"
        
        if ws:
            self.domain = ws.domain
            self.tld = ws.tld
            self.subdomain = ws.subdomain

            if self.subdomain == "www":
                _subdomain = ""
            elif self.subdomain == "":
                _subdomain = self.subdomain
            else:
                _subdomain = f"{self.subdomain}."

            self.netloc = _article_url.netloc
            clean_sub = re.sub(r"(www\.)?", "", _subdomain)

            self.fqdn = f"{clean_sub}{self.domain}.{self.tld}"
        else:
            self.netloc = _article_url.netloc
            self.subdomain = ""
            self.tld = ""
            self.fqdn = re.sub(r"(www\.)?", "", self.netloc)
        
        match_replace = [
            (r"(www\.)|\.([^.]*)$", ""),
            (r"\.", " "),
            (r"(\d)([^\d\s%])", r"\1 \2")
        ]

        clean_domain = self.domain

        if clean_domain == "www":
            clean_domain = self.tld

        for r, m in match_replace:
            clean_domain = re.sub(r, m, clean_domain)

        clean_domain_arr = clean_domain.split(" ")
        clean_domain_arr = [w.capitalize() for w in clean_domain_arr]


        self.name = " ".join(clean_domain_arr)
        self.website_url = f"{self.protocol}://{self.netloc}"
    
    def __check_duplicates(self):
        """
        Private method to check for duplicates in database
        """
        if not self.parsed:
            raise WebsiteError("Website not parsed")

        url = self.url + "custom_query/"

        body = {
            "website_name": self.name
        }
        
        response = requests.post(url, data=json.dumps(body), headers=self.headers)
        # self.__raise_errors(response, body, url)
        result = response.json()['data']

        if not result:
            self.duplicate = False
        else:
            self.duplicate = True

    def __is_to_scrape(self, _id: str=None):
        """
        Private method to check if website is for scraping
        """
        # CHECK PROPERTY is_to_be_scraped FIRST.
        # IF NO RESULT PROCEED TO VALIDATION FOR country and status
        if not _id:
            self.for_scraping = False
            return False
            
        # IF PARAMETER is_to_be_scraped WILL BE THE FACTOR
        # to_be_scraped_websites = self.counts({"is_to_be_scraped": True})
        to_be_scraped_websites = None 

        website = self.get_one(website_id=_id)

        if website:
            if not to_be_scraped_websites:
                validators = [
                    # website['country'] == "Unknown", # UNCOMMENT AND REMOVE BELOW CODE IF WEBSITE COUNTRY ARE ALREADY VERIFIED
                    website['country'] not in ["Philippines", "Singapore"],
                    website['is_aggregator'],
                    website['fqdn'] in ["philstar.com"]
                ]
            else:
                validators = [not website['is_to_be_scraped']]

            if any(validators):
                self.for_scraping = False
            else:
                self.for_scraping = True
 
    def generate_country_data(self):
        """
        Method to get alexa data of website
        """

        alexa_data_url = "http://data.alexa.com/data"

        payload = {
            "cli": 10,
            "dat": "snbamz",
            "url": self.website_url
        }

        time.sleep(random.randint(5, 15))

        response = requests.get(alexa_data_url, params=payload)
        self.__raise_errors(response, payload, alexa_data_url)
        data = response.content

        if data:
            soup = BeautifulSoup(data, "lxml")
            try:
                country = soup.find("country").attrs
                if country:
                    for key, value in country.items():
                        if key == "name":
                            self.country = value
                        elif key == "code":
                            if value == "US":
                                value = "USA"
                            self.country_code = value
                        else:
                            pass
            except:
                self.country = None
                self.country_code = None

            if self.country == 'Philippines':
                self.website_type = "LOCAL_NEWS"

            if all([not self.country, not self.country_code]):
                self.website_type = "INTERNATIONAL_NEWS"    

def update_country(web_url: str, country: str=None, country_code: str=None, ignore_ph: bool=False):
    """
    Method to update country of a website
        @params:    web_url           -   URL of website
        @params:    country           -   new country to be recorded
        @params:    country_code      -   country code to be recorded
        @params:    ignore_ph         -   True if Philippines is to be ignored else False
    """
    if not web_url:
        raise WebsiteError("No website url parameter found")

    else:
        website.parse(web_url)
        website.check()
        website.generate_country_data()

    website_id = website._id

    if ignore_ph and any([website.country is not None, website.country_code is not None]):
        if website.country == "Philippines":
            _country = "Unknown"
            _country_code = "NoC"
    else:
        _country = country or website.country or "Unknown"
        _country_code = country_code or website.country_code or "NoC"

    query = {
        "country": _country,
        "country_code": _country_code
    }

    if not website_id: raise WebsiteError("No website found in the Database")

    response = website.update(query, website_id)

    if not response:
        print('Nothing was updated')
    else:
        print(f"Updated website {website.name} (country is now '{_country}' with country_code '{_country_code}')")

    