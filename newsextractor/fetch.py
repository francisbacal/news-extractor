from .helpers import catch, Compare
from options import *
from .exceptions import NoResponseError, HelperError
from fake_useragent import UserAgent
import cloudscraper, requests, traceback

class Fetch:
    """
    Fetch class primarily for page source downloading
        @params:    
            url         -   URL to fetch
            method      -   requests method to perform. [Default: GET]
            headers     -   headers to pass in requests.
            body        -   dict object containing payload query if any
            options     -   Options class to pass if any
            timeout     -   Timeout in seconds before raising Timeout Exception
            max_retries -   Number of retries to perform upon timeout or exception
            agent       -   User agent to be passed in requests if any
            **kwargs    -   Additional arguments to extend to options
    """

    def __init__(self, url: str="", method='GET', headers: dict={}, body: dict={},
                options=None, timeout: int=30, max_retries: int=2, agent: str='random', **kwargs):
        """
        Initialize method
        """
        self.url = url
        self.method = method
        self.headers = headers
        self.body = body
        self.timeout = timeout
        self.max_retries = max_retries
        self.agent = agent
        self.is_html = True
        self.page_headers = None
        self.r_url = None
        self.status_code = None
        self.text = None

        self.options = options or Options()
        self.options = extend_opt(self.options, kwargs)

    def __raise_errors(self, response):
        """
        Private method to check for response errors
            @params:
                response            -   response instance to check
        """

        if str(response.status_code) in ['403', '404', '400']:
            response.raise_for_status()

    def __get_page_headers(self, response):
        """
        Private method to get page headers from requests response
            @params:
                response        -   requests response instance to check
        """
        try:
            headers = response.headers
        except:
            headers = None

        return headers
    
    def __is_html(self, page_headers: dict):
        """
        Check if page is an html page
            @params:
                page_headers        -   dict object containing response headers
        """
        if page_headers:
            if 'Content-Type' in page_headers:
                content_type_data = Compare(["text/html"])
                comparison_result = content_type_data.eval(page_headers['Content-Type'])

                if comparison_result:
                    similarity = float(comparison_result[0]['similarity'].strip("%"))

                    if similarity >= 50:
                        return True
                    else:
                        return False

    def download(self, timeout: int=0):
        """
        Method to download page source, redirected url, and status code
            @params:
                timeout             -   timeout in seconds
        """

        timeout = timeout or self.timeout
        user_agent = UserAgent()

        # SET HEADERS USER-AGENT
        if self.agent == "random":
            self.headers['User-Agent'] = str(user_agent.random)
        else:
            self.headers = {}

        # TRY CLOUDSCRAPER
        cs = cloudscraper.create_scraper()

        response = catch('None', lambda: cs.get(self.url, timeout=timeout))

        # TRY REQUESTS IF NO RESPONSE
        if not response:
            response = catch('None', lambda: requests.request(self.method, self.url, headers=self.headers, timeout=timeout))

        # RAISE ERROR IF NO RESPONSE
        if not response:
            raise NoResponseError(f"Fetch Error: No Response from page {self.url}")

        # CHECK PAGE STATUS AND RAISE FOR ERRORS
        self.__raise_errors(response)

        self.page_headers = self.__get_page_headers(response)
        self.is_html = self.__is_html(self.page_headers)
        self.r_url = response.url
        self.status_code = response.status_code
        self.text = response.content