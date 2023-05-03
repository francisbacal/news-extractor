import os;

class Options(object):
    """
    Options class containing configuration for global parser
    """
    def __init__(self):
        """
        Class initialization method
        """
        self.token = f"Bearer {os.environ['API_TOKEN']}"
        self.testing = False
        self.limit = 1
        self.queued = False
        self.include_error = False

        # END POINT SETTINGS
        self.API_HOST = os.environ['API_HOST']
        self.API_NAME = os.environ['API_NAME']
        self.LAMBDA_API_NAME = 'lambda-api'
        self.API_VERSION = 'v0'                            
        self.API_SETTINGS = {
            'main': (self.API_NAME,),
            'lambda-api': (self.LAMBDA_API_NAME,),
            'version': ('/main', self.API_VERSION),
            'lambda-article': ('/lambda-api', 'article'),
            'lambda-article-media-value': ('/lambda-article', 'media_values'),
            'global-link': ('/version', 'global-link'),
            'global-link-custom': ('/global-link', 'custom_query'),
            'global-link-count': ('/global-link', 'count_custom_query'),
            'article': ('/version', 'article'),
            'article-custom': ('/article', 'custom_query'),
            'article-count': ('/article', 'count_custom_query'),
            'article-test': ('/version', 'article-test'),
            'article-test-custom': ('/article-test', 'custom_query'),
            'article-test-count': ('/article-test', 'count_custom_query'),
            'web': ('/version', 'web'),
            'web-custom': ('/web', 'custom_query'),
            'web-count': ('/web', 'count_custom_query'),
        }
        self.END_POINTS = dict(self.__get_end_points())
    
    def __get_end_points(self):
        for name, path in self.API_SETTINGS.items():
            yield name, list(self.__expand_path(name))

    def __expand_path(self, name):

        path = self.API_SETTINGS[name]
        for name in path:
            if name[0] != '/':
                yield "/" + name
            else:
                yield from self.__expand_path(name[1:])

    def get_endpoint(self, endpoint: "str"):
        """
        Generate the endpoint url for a specified name
        """
        from urllib.parse import urljoin
        from functools import reduce

        paths = reduce(lambda a, b: a + b, self.END_POINTS[endpoint])

        if endpoint.startswith("lambda"):
            HOST = f"{self.API_HOST}:{os.environ['API_LAMBDA_PORT']}"
        else:
            HOST = f"{self.API_HOST}:{os.environ['API_PORT']}"

        return urljoin(HOST, paths)

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