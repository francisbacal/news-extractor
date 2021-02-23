class Options(object):
    """
    Options class containing configuration for global parser
    """
    def __init__(self):
        """
        Class initialization method
        """
        self.token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.f2X7W_6J8g6y-jKto1fMj5zq7QkOLu9WBGw5b-sHAIc"
        self.testing = False
        self.limit = 1
        self.queued = False
        self.include_error = False

        ## GLOBAL LINKS
        self.url_article_links= "http://192.168.3.143:4040/mmi-endpoints/v0/global-link/"
        self.url_article_links_custom = 'http://192.168.3.143:4040/mmi-endpoints/v0/global-link/custom_query'
        self.url_article_links_count = 'http://192.168.3.143:4040/mmi-endpoints/v0/global-link/count_custom_query'

        ## ARTICLES
        self.url_articles = 'http://192.168.3.143:4040/mmi-endpoints/v0/article/'
        self.url_articles_custom = 'http://192.168.3.143:4040/mmi-endpoints/v0/article/custom_query'
        self.url_articles_count = 'http://192.168.3.143:4040/mmi-endpoints/v0/article/count_custom_query'
        self.url_media_values = 'http://192.168.3.143:3030/lambda-api/article/media_values'

        self.url_articles_test = 'http://192.168.3.143:4040/mmi-endpoints/v0/article-test/'
        self.url_articles_test_custom = 'http://192.168.3.143:4040/mmi-endpoints/v0/article-test/custom_query'
        self.url_articles_test_count = 'http://192.168.3.143:4040/mmi-endpoints/v0/article-test/count_custom_query'

def extend_opt(options, options_items: dict):
    """
    Extend kwargs to options
        @params:  
            options           -   Options class
            option_items      -   dict object containing items to extend to Options if matched
    """
    for key, val in list(options_items.items()):
        if hasattr(options, key):
            setattr(options, key, val)

    return options