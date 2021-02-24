from ..exceptions import HelperError
from urllib.parse import urlparse
from tld import get_tld

import re

class ArticleURL:
    """
    Class for clean article link and returns an urlparse object
        @params:
            url         - Required    : article url to check and clean
    """

    def __init__(self, url: str, agent: str=None, get_redirect: bool=False):
        """
        Initialize method
        """

        if not isinstance(url, str):
            raise HelperError(f"ArticleURL Error: url must be a str not {type(url)}")
        
        self.scheme = "http"
        self.parsed_url = urlparse(url)

        # CHANGE PROTOCOL/SCHEME
        if self.parsed_url.scheme == "":
            new_url = f"{self.scheme}:{url}" if re.match(r"^\/\/", url) else f"{self.scheme}://{url}"
        
        # CLEAN URL
        self.path = str(self.parsed_url.path).rstrip("/")
        self.netloc = self.parsed_url.netloc

        self.url = f"{self.scheme}://{self.netloc}{self.path}"
        
        # RE PARSE
        self.parsed_url = urlparse(self.url)
