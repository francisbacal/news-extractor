import nltk, datetime, cloudscraper, time, platform, os, requests, pytz, re

from .exceptions import *
from .helpers import ArticleURL, rand_sleep, NewsVariables, Compare, catch, unicode
from .author import Author
from .publish_date import PublishDate
from .title import Title
from .content import Content

from newspaper import Article
from bs4 import BeautifulSoup
from dateutil.parser import parse
from logs import init_log


class News:
    """
    Instantiate a news article object
        @params:
            url     - url of article to be parsed
            js      - True if article is a javascript rendered site else False
            source  - page source of article
    """

    def __init__(self, url: str, source=None, js: bool=False, lang: str="en", timeout: int=60):
        """
        Initialize method
        """
        if not url or not isinstance(url, str):
            raise NewsError("Invalid URL passed")

        # INSTANTIATE NEWS VARIABLES
        self.news_variables = NewsVariables()

        # CLEAN URL
        CLEAN_URL = ArticleURL(url)
        rand_sleep(3, 5)

        self.url = CLEAN_URL.url
        self.html = source
        self.lang = lang
        self.timeout = timeout
        self.scraped = False

        # PAGE SOURCE IS REQUIRED
        if not self.html:
            raise NewsError("No Page Source passed")

        if js and not self.html:
            raise NewsError("Page source required for dynamic pages.")
        
        # CLEAN HTML
        clean_html = self.__clean_html(self.html, js=js) if self.html else None

        #NEWSPAPER 3K
        article = catch('None', lambda: Article(self.url, request_timeout=30, MIN_WORD_COUNT=600))
        catch('None', lambda: article.download(input_html=clean_html))
        catch('None', lambda: article.parse())

        # AUTHOR
        author = catch('None', lambda: Author(clean_html))

        # PUBLISH DATE
        publish_date = catch('None', lambda: PublishDate(clean_html))

        # TITLE
        title = catch('None', lambda: Title(clean_html))

        # CONTENT
        content = catch('None', lambda: Content(clean_html, title.text, lang=self.laang) if title 
                        else Content(clean_html, article.title, lang=self.lang) if article
                        else None)

        # CLASS VARIABLES
        self.title = self.__get_title(title.text, article)
        self.authors = self.__get_authors(author.names, article)
        self.publish_date = self.__get_publish_date(publish_date.date, article)
        self.images = self.__get_images(article)
        self.content = self.__get_content(content.text, article, js=js)


        self.videos = catch('list', lambda: article.movies if article.movies else [])
        self.language = catch('None', lambda: article.meta_lang if not article.meta_lang else 'en')

        # BOOLEAN SCRAPED
        self.scraped = True

    def generate_data(self):
        """
        Generates article dict data
        """
        if not self.scraped: raise NewsError("Article not scraped")
        date_now = datetime.datetime.today().isoformat()

        data = {
                'article_title': self.title,
                'article_section': [],
                'article_authors': self.authors,
                'article_publish_date': self.publish_date,
                'article_images': self.images,
                'article_content': self.content,
                'article_videos': self.videos,
                'article_media_type': 'web',
                'article_ad_value': 0,
                'article_pr_value': 0,
                'article_language': self.language,
                'article_status': 'Done',
                'article_error_status': None,
                "article_source_from": None,
                'keyword': [],
                'article_url': self.url,
                'date_created': date_now,
                'date_updated': date_now,
                'created_by': "Python Global Scraper",
                'updated_by': "Python Global Scraper"
            }
        
        return data
    
    def __clean_html(self, html: str=None, js: bool=False):
        """
        Private method to clean page source
            @params:
                html    -   page source to clean
                js      -   True if dynamic page else False
        """

        if not html:
            return None
        
        soup = BeautifulSoup(html, "html.parser")

        # REMOVE ALL UNRELATED TAGS FROM SOURCE
        tags_for_decompose = self.news_variables.tags_for_decompose

        for tag in tags_for_decompose:
            for _tag in soup(tag):
                _tag.decompose()
        
        if js:
            for tag in soup.find_all(self.__is_invalid_tag):
                tag.decompose()

        return str(soup)
    
    def __is_invalid_tag(self, tag):
        """
        Returns the tag that contains specific invalid keyword
            @params:
                tag     -   BS4 tag/element
        """
        INVALID_KEYS = self.news_variables.invalid_keys
        
        # GET COMPARISON DATA
        INVALID_KEY_DATA = Compare(INVALID_KEYS)
        comparison = None

        for _, v in tag.attrs.items():

            for key in INVALID_KEYS:
                # SET TAG ATTRIBUTE VALUE FOR COMPARISON TO KEYS
                if not isinstance(v, list):
                    comparison = INVALID_KEY_DATA.eval(v)
                
                if key in v:
                    return True
                elif isinstance(v, list) and any(key in i for i in v): # IF V IS A LIST ITERATE THRU ITEMS IN V AND CHECK FOR KEY
                    return True
                elif comparison: # IF KEY IS SIMILAR TO V
                    similarity = str(comparison[0]['similarity']).rstrip("%")

                    if int(similarity) >= 70:
                        return True
                elif isinstance(v, list):
                    for _v in v:
                        _comparison = INVALID_KEY_DATA.eval(v)

                        if _comparison:
                            similarity = str(_comparison[0]['similarity']).rstrip("%")
                        
                        if int(similarity) >= 70: return True

    def __get_title(self, _title: str, article: type(Article)):
        """
        Generate news title
        """
        
        title = catch('None', lambda: unicode(_title) if _title else
                        unicode(article.title) if article.title else 
                        None)

        substring = self.news_variables.invalid_title_keys
        
        if not title:
            return None
        
        for string in substring:
            match = catch('None', lambda: title.lower().index(string.lower()))

            if match: return None
        
        return title

    def __get_authors(self, _author: str, article: type(Article)):
        """
        Generate news authors
        """

        if article:
            authors = catch('list', lambda: _author if _author
                            else article.authors if len(article.authors) != 0
                            else [])
        else:
            authors = _author if _author else []

        if not isinstance(authors, list):
            authors = [authors]

        return authors

    def __get_publish_date(self, _date, article: type(Article)):
        """
        Generate news publish date
        """
        pht = pytz.timezone('Asia/Singapore')

        try:
            article_date = article.meta_data['article']['published_time']

            if not isinstance(article_date, datetime.datetime):
                article_date = parse(str(article_date))

        except:
            article_date = None

        # GET BOTH DATES
        dates = [_date, article_date]
        # REPLACE TZINFO
        datetime_dates = [date.replace(tzinfo=pht) for date in dates if date is not None]

        # GET MIN DATE IF DATETIME_DATES IS NOT NONE
        publish_date = datetime.datetime.now().isoformat() if not datetime_dates else min(datetime_dates).isoformat()

        return publish_date

    def __get_images(self, article: type(Article)):
        """
        Generate news images
        """
        if not article:
            images = [catch('list', lambda: article.top_image if article.top_image else [])]
        else:
            images = []

        return images

    def __get_content(self, _content: str, article: type(Article), js: bool=False):
        """
        Generate news content
        """

        if js:
            content = catch('None', lambda: unicode(' '.join(_content.replace('’', '').split())) if _content else None )
        else:
            content = catch('None', lambda: unicode(' '.join(_content.replace('’', '').split())) if _content
                            else  unicode(' '.join(article.text.replace('’', '').split())) if article.text
                            else None)

        return content