
from logs import init_log
from newsextractor import News, DynamicSource, name_entity
from .endpoints import LinksAPI, ArticlesAPI, WebsiteAPI, MediaValues
from endpoints.exceptions import *

from pebble import ProcessPool
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import current_process
from collections.abc import Callable

import os, sys, datetime, socket, time, random, threading

#INIT WEBSITE
website = WebsiteAPI()

# INIT LOG
log = init_log('DynamicScraperSub')

class DynamicScraper:
    """
    Dynamic scraper
    """

    def __init__(self, for_article: bool = False):
        self.for_article = for_article
        self.website = WebsiteAPI()
    
    @staticmethod
    def multiprocess(articles: list, processors: int, func: Callable, for_article=False):
        """
        Starts the main multiprocess task using pebble ProcessPool
            @params:
                articles            -   articles to be scraped
                processors          -   number of processes to spawn
                func                -   callable function for scraping
        """

        splitted_articles = DynamicScraper.split_list(articles, processors)

        with ProcessPool(max_workers=processors) as executor:
            future = executor.map(DynamicScraper, splitted_articles, [func] * len(splitted_articles), [for_article] * len(splitted_articles), timeout=900)

            try:
                for result in future.result:
                    if result: print(result)
            except TimeoutError:
                log.debug("TimeoutError")
            
            except Exception as e:
                log.error(e, exc_info=True)
                pass

    @staticmethod
    def multithread(articles: list, func: Callable, for_article=False):
        """
        Starts a multithread process using ThreadPoolExecutor
            @params:
                articles        -   articles to be scraped
                func            -   callable function for scraping
        """
        import queue

        in_queue = queue.Queue()
        out_queue = queue.Queue()
        result_queue = queue.Queue()

        if not articles: return

        if len(articles) < 1: return


        MAX_WORKERS = 4
        CPU_THREADS = (os.cpu_count() - 1) * 2

        if CPU_THREADS < MAX_WORKERS:
            MAX_WORKERS = os.cpu_count() - 1

        WORKERS = min(MAX_WORKERS, len(articles))
        REMAINING_WORKERS = (CPU_THREADS - WORKERS)

        browsers = []
        scraped_count = 0

        start = time.time()
        log.info(f"Process {current_process().name} started")

        # INSTANTIATE DRIVER/BROWSER AND GET SOURCE FOR PROCESSING
        process_sources = []
        for i in range(WORKERS):
            seledriver = Seledriver(browser="fox")
            browsers.append(seledriver)
                
            process_source = DynamicSource(in_queue, out_queue, seledriver, for_article=for_article, timeout=900)
            process_source.setDaemon(True)
            process_sources.append(process_source)
            process_source.start()

            # DELAY PER INSTANTIATION
            time.sleep(5)

        log.debug(f"Browsers : {[browser.name for browser in browsers]}")

        # QUEUE LINKS
        log.debug('Queueing Links...')
        for article in articles:
            in_queue.put(article)
        log.debug('Done Queueing Links...')

        # PROCESS ARTICLES
        parsers = []

        for _ in range(REMAINING_WORKERS):
            process_article = ParseArticle(out_queue, result_queue, update=False, timeout=900, log=log)
            process_article.setDaemon(True)
            parsers.append(process_article)
            process_article.start()

        # RESULT VARS
        scraped = []
        results = []

        # START MULTITHREAD
        with ThreadPoolExecutor() as executor:

            futures = [executor.submit(func, article) for article in articles]

            for future in as_completed(futures):
                try:
                    result = future.result()

                    log.debug(result)
                    
                    if result == "Article Scraped":
                        scraped.append(result)
                    else:
                        results.append(result)
                
                except Exception as e:
                    log.error(e, exc_info=True)
                    continue
        
        return results

    @staticmethod
    def split_list(input_list: list, n: int):
        """
        Split input_list into n number of split
            @params:
                input_list      -   list to split
                n               -   number of split
        """
        from itertools import islice

        if not input_list:
            return []
        
        result = []

        iterator = iter(input_list)
        quotient, remainder = divmod(len(input_list), n)

        for _ in range(remainder):
            result.append(list(islice(iterator, quotient+1)))

        for _ in range(n - remainder):
            result.append(list(islice(iterator, quotient)))

        return result

    @staticmethod
    def check_unprocessed_links(processing_status: str=None, for_article: bool=False):
        """
        Checks for unfinished processing links and re queue if any
            @params:
                for_article     -   True for article database False for global links
        """

        status = processing_status or f"Processing@{str(socket.gethostname())}"

        MAX_UNPROCESSED = 10000

        if not for_article: 
            QUERY = {"status": {"$in": [status]}, "created_by": {"$in": ["JS_link", "JS_lazy"]}} 

        else:
            QUERY = {"article_status": {"$in": [status, "Processing"]}, "created_by": {"$in": ["JS_link", "JS_lazy"]}}

        linksAPI = LinksAPI() if for_article else ArticlesAPI()

        while True:
            unprocessed_count = linksAPI.counts(QUERY)

            if unprocessed_count > MAX_UNPROCESSED:
                unprocessed_count = MAX_UNPROCESSED
        
            unprocessed_links = linksAPI.get(query=QUERY, limit=unprocessed_count)
            log.info(f"Unprocessed links - {len(unprocessed_links)}")

            if unprocessed_links:
                log.info(f"Queueing unprocessed links")
                
                # UPDATE TO QUEUE
                with ThreadPoolExecutor(max_workers=2) as executor:
                    executor.map(DynamicScraper.update_to_queued, unprocessed_links)
            else:
                break

            # CHECK AGAIN FOR UNPROCESS COUNT
            unprocessed_count = linksAPI.counts(QUERY)

            if unprocessed_count == 0: break

    @staticmethod
    def update_to_queued(article: dict, processing_status: str=None, for_article: bool = False):
        """
        Update status of article or link to Queued
            @params:
                article             -   dict object containing article or link data
                processing_status   - Status of article/link for query
                for_article         -   True for article database False for global links
        """

        _id = article['_id']
        status = processing_status or f"Processing@{str(socket.gethostname())}"
        API = LinksAPI() if not for_article else ArticlesAPI()
        
        if for_article:
            PAYLOAD = {"article_status": "Queued"}
        else:
            PAYLOAD = {"status": "Queued"}

        
        # UPDATE
        API.update(_id, PAYLOAD)

    @staticmethod
    def check_queued(for_article=False):
        """
        Check for Queued Articles/links
            @params:
                for_article     -   True for article database False for global links
        """
        API = LinksAPI() if not for_article else ArticlesAPI()

        if for_article:
            QUERY = {"article_status": "Queued", "created_by": {"$in": ["JS_link", "JS_lazy"]}, 'original_url': {"$ne": None}}
        else:
            QUERY = {"status": "Queued", "created_by": {"$in": ["JS_link", "JS_lazy"]}} 

        queued_count = API.counts(QUERY)

        return queued_count

    @staticmethod
    def get_queued_links(limit: int, for_article: bool=False):
        """
        Get Queued Links from database
            @params:
                for_article     -   True for article database False for global links

            @returns:
                randomize list of for processing status articles for scraping
        """
        API = LinksAPI() if not for_article else ArticlesAPI()

        if for_article:
            PAYLOAD_QUERY = {
                                "$query":   {
                                            "article_status": "Queued",
                                            "created_by": {"$in": ["JS_link", "JS_lazy"]}
                                            },
                                "$orderby": {"date_created": -1}
                            }

        else:
            PAYLOAD_QUERY = {
                                "status": "Queued"
                                "created_by": {"$in": ["JS_link", "JS_lazy"]},
                                "original_url": {"$ne": None}
                            }

        queued_articles = API.get(PAYLOAD_QUERY, limit=limit)

        if not queued_articles: return None

        # RANDOMIZE
        queued_articles = random.sample(queued_articles, len(queued_articles))

        # UPDATE TO PROCESSING STATUS
        with ThreadPoolExecutor() as executor:
            articles_for_scraping = executor.map(DynamicScraper.update_to_processing, queued_articles)

        return articles_for_scraping

    @staticmethod
    def update_to_processing(article: dict, for_article=False):
        """
        Update article or link to processing status
            @params:
                article         -   dict object containing article data to be updated
                for_article     -   True for article database False for global links
        """

        API = LinksAPI() if not for_article else ArticlesAPI()

        processing_status = f"Processing@{str(socket.gethostname())}"
        PAYLOAD = {"status": processing_status} if not for_article else {"article_status": processing_status}
        _id = article['_id']

        API.update(_id, PAYLOAD)

        return API.get_one(_id)

    @staticmethod
    def is_running(pid: int):
        """
        Check for running process
        """

        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True

    @staticmethod
    def endtime(for_article=False):
        """
        Check if scraper is to be terminated
            @params:
                for_article     -   True for article scraper, False for global link article scraper
        """

        timenow = datetime.datetime.now()

        morning_hour = 6 if for_article else 3
        afternoon_hour = 12 if for_article else 15
        evening_hour = 18 if for_article else 21
        mid_hour = 23 if for_article else 9
        

        # MORNING TIME CHECK
        mn_start = timenow.replace(hour=morning_hour,minute=00, second=0, microsecond=0)
        mn_end = mn_start.replace(minute=30)

        # AFTERNOON TIME CHECK
        an_start = timenow.replace(hour=afternoon_hour,minute=00, second=0, microsecond=0)
        an_end = an_start.replace(minute=30)

        # EVENING TIME CHECK
        ev_start = timenow.replace(hour=evening_hour,minute=00, second=0, microsecond=0)
        ev_end = ev_start.replace(minute=30)

        # MID TIME CHECK
        md_start = timenow.replace(hour=mid_hour,minute=00, second=0, microsecond=0)
        md_end = md_start.replace(hour= 0 if for_article else mid_hour, minute=30)


        # CONDITIONS
        morning_stop = mn_start < timenow < mn_end
        afternoon_stop = an_start < timenow < an_end
        evening_stop = ev_start < timenow < ev_end
        mid_stop = md_start < timenow < md_end


        # LOGIC
        if any([morning_stop, afternoon_stop, evening_stop, mid_stop]):
            return True
        
        return False

    @staticmethod
    def check_website(article_id: str, article_url: str, for_article: bool=False):
        """
        Check website data if for scraping
        """
        website = WebsiteAPI()
        website.check(article_url)

        API = LinksAPI() if not for_article else ArticlesAPI()

        if website.checked and not website.for_scraping:
            # UPDATE PAYLOAD
            update_payload = {"status": "Error"} if not for_article else {"article_status": "Error", "article_error_status": "Unverified Website"}
            try:
                API.update(article_id, update_payload)
            except:
                return False

            return False

        elif not website.checked:
            return False

        elif website.checked and website.for_scraping:
            return website._id

    @staticmethod
    def update_article_error(article_id: str, error: str, for_article=False):
        """
        Update article status to error
        """
        API = LinksAPI() if not for_article else ArticlesAPI()

        UPDATE_PAYLOAD = {'status': 'Error'} if not for_article else {"article_status": "Error", "article_error_status": error}
        API.update(article_id, UPDATE_PAYLOAD)

    @staticmethod
    def parse_article(article: dict, for_article=False):
        """
        Parse article data
            @params:
                article         -   article/link data from database
                for_article     -   True for article scraper, False for global link article scraper
        """
        processing_status = f"Processing@{socket.gethostname()}"

        API = LinksAPI() if not for_article else ArticlesAPI()
        articlesAPI = ArticlesAPI()
        website = WebsiteAPI()

        language = "en" # EDIT FOR FUTURE USE
        article_id = article['_id']
        article_url = article['original_url'] if not for_article else article['article_url']
        article_status = article['status'] if not for_article else article['article_status']

        try:
            # CHECK IF WEBSITE EXISTS IN DATABASE AND IS FOR SCRAPING
            website_id = DynamicScraper.check_website(article_id, article_url)

            # GET SOURCE PAGE OF ARTICLE
            source = StaticSource(article_url)
            page_source = source.text

            # RE VALIDATION
            # IF NOT QUEUED
            if article_status == "Queued":
                PAYLOAD = {"status": processing_status} if for_article else {"article_status": processing_status}
                API.update(article_id, PAYLOAD)

            # CHECK IF ARTICLE IS EXISTING
            if not for_article:
                existing = articlesAPI.get({"article_url": article_url})

                if existing:
                    API.update(article_id, {"status": "Done"})
                    return "Duplicate article"

            # GET NEWS DATA
            news = News(article_url, page_source, lang=language)
            news_data = news.generate_data()
            
            # VALIDATE CONTENT
            if not news.content:
                DynamicScraper.update_article_error(article_id, "Invalid Content", for_article=for_article)
                return "No Content"

            # VALIDATE AUTHORS
            authors = [news_data['article_authors']]

            if not isinstance(authors, list):
                authors = [authors]

            try:
                news_data['article_authors'] = name_entity(authors)
            except:
                news_data['article_authors'] = authors

            if authors and not news_data['article_authors']:
                news_data['article_authors'] = authors

            # VALIDATE TITLE
            if not news_data['article_title']:
                DynamicScraper.update_article_error(article_id, "Invalid article title", for_article=for_article)
                return "No Title"

            # GET MEDIA VALUES
            if website_id:
                media_value_payload = {
                    "text": news_data['article_content'],
                    "images": news_data['article_images'],
                    "videos": news_data['article_videos']
                }

                media_values = MediaValues(website_id, media_value_payload)

                news_data['article_ad_value'] = media_value['advalue']
                news_data['article_pr_value'] = media_value['prvalue']

            # SAVE/UPDATE ARTICLE
            if not for_article:
                articlesAPI.add(news_data)
            else:
                articlesAPI.update(article_id, news_data)

            return "Article Scraped"

        except Exception as e:
            log.error("Error encountered while parsing article", exc_info=True)
            DynamicScraper.update_article_error(article_id, str(e), for_article=for_article)
            
            return "Error"
        
    @staticmethod
    def raw_data(article: dict, for_article=False):
        """
        Get raw article data
            @params:
                article         -   article/link data from database
                for_article     -   True for article scraper, False for global link article scraper
        """

        # GET SOURCE PAGE OF ARTICLE
        
        source = StaticSource(article_url)
        page_source = source.text

        # GET NEWS DATA
        news = News(article_url, page_source, lang=language)
        news_data = news.generate_data()

        return news_data


class ParseArticle(threading.Thread):
    """
    Thread parser for dynamic articles
    """

    def __init__(self, out_queue, result_queue, for_article: bool=False, timeout=1800):
        """
        Initialization
        """
        threading.Thread.__init__(self)
        self.out_queue = out_queue
        self.result_queue = result_queue
        self.stop_thread = False
        self.for_article = for_article

    def run(self):
        """
        Thread start
        """
        while True:
            if self.stop_thread: break

            item = self.out_queue.get()
            article = item[0]
            source = item[1]

            # CHECK IF SOURCE IS DUPLICATE
            if source == "Duplicate": 
                result = "Duplicate Article"
                self.result_queue.put(result)
                self.out_queue.task_done()
                continue

            self.article_url = article['original_url'] if not self.for_article else article['article_url']
            self._id = article['_id']

            is_lazy = self.__check_lazy(self.article_url, 'data/lazy.json')

            # CHECK IF WEBSITE EXISTS IN DATABASE AND IS FOR SCRAPING
            website_id = DynamicScraper.check_website(article_id, article_url)

            if not website_id: 
                result = "Website not for scraping"
                self.result_queue.put(result)
                self.out_queue.task_done()
                continue

            else:
                country = website.get_one(website._id)['country']
                language = "tl" if country == "Philippines" else "en"


    

    def __check_lazy(self, url: str, json_file: str):
        """
        Checks if article link has lazy loaded content
            @params:
                url         - Required    : article url (String)
                json_file   - Required    : json filename with extension that contains websites that has lazy loaded content (String)
        """
        parsed_url = urlparse(url)
        # protocol = parsed_url.scheme
        domain = parsed_url.netloc

        with open(json_file) as lazy_sites:
            data = json.load(lazy_sites)

            for i in data['lazy-sites']:
                match = re.match(i['domain'], domain)
                if match:
                    return True
            
        return False


            

    def stop(self):
        """
        Method to raise boolean for stopping thread
        """
        self.stop_thread = True
