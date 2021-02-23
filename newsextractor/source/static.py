from ..fetch import Fetch
from ..helpers import ArticleURL

class StaticSource(Fetch):
    """
    Get static source
    """

    def __init__(self, url: str='', timeout: int=30):

        self.url = ArticleURL(url)
        self.timeout = timeout


        super().__init__(url, timeout=timeout)
        self.download()