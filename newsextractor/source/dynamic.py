import threading, json, time

from urllib.parse import urlparse
from ..content import Content
from ..helpers import Compare
from endpoints import ArticlesAPI

from selenium.common.exceptions import TimeoutException

class DynamicSource(threading.Thread):
    """
    Class for dynamic source parsing
        @params:    
            in_queque         -   queue object to get websites from
            out_queue         -   queue object to pass page source
            browser            -   selenium driver
            timeout           -   timeout for getting source [Default: 1800]
    """

    def __init__(self, in_queue, out_queue, browser, for_article: bool=False, timeout=1800):

        threading.Thread.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.browser = browser
        self.timeout = timeout
        self.page_source = None
        self.article_url = None

        self.stop_thread = False
        self.global_link = global_link

    def run(self):
        """
        Threading start
        """
        thread_id = self.get_id()
        try:
            while True:
                if self.stop_thread:
                    break

                articlesAPI = ArticlesAPI()

                article = self.in_queue.get()
                self.article_url = article['original_url'] if for_article else article['article_url']

                # CHECK IF EXISTING
                existing = articlesAPI.get({"article_url": self.article_url})

                if existing:
                    self.page_source = "Duplicate"
                    data = (article, self.page_source)

                    self.out_queue.put(data)
                    self.in_queue.task_done()
                    continue

                # CHECK IF LAZY LOADED
                is_lazy = self.__check_lazy(self.article_url, 'data/lazy.json')

                # GET PAGE SOURCE VIA SELENIUM
                try:
                    self.browser.get(self.article_url)

                    is_html = True
                    try:
                        for request in self.browser.requests:
                            if request.response:
                                is_html = self.__is_html(request.response.headers)
                    except:
                        print(traceback.format_exc())
                        is_html = True   

                    self.page_source = self.browser.page_source
                    if is_lazy: self.page_source = self.__navigate_scroll()

                except TimeoutException as e:
                    print(e)
                    self.page_source = None

                except Exception as e:
                    self.page_source = None

                data = (article, self.page_source)

                self.out_queue.put(data)
                self.in_queue.task_done()
                
        finally:
            print('Source Ended')

    def __check_lazy(self, url: str, json_file: str):
        """
        Checks if article link has lazy loaded content
            @params:
                url         - Required    : article url (String)
                json_file   - Required    : json filename with extension that contains websites that has lazy loaded content (String)
        """

        parsed_url = urlparse(url)

        netloc = parsed_url.netloc

        with open(json_file) as lazy_sites:
            data = json.load(lazy_sites)
        
            for site in data['lazy_sites']:
                match = re.match(site['domain'], netloc)

                if match:
                    return True
            
            return False

    def __navigate_scroll(self):
        """
        Scrolling function for lazy loaded articles like scmp
        """
        try:
            _title = self.browser.title
            _body = self.browser.find_element_by_tag_name('body')

            i = 0
            while i < 3:
                _html = str(self.browser.page_source)
                _content = Content(_html, _title)
                _attrs = _content.last_divs

                scroll_items = []
                for _attr in _attrs:
                    xpath_string = '//div'

                    for k, v in _attr.items():
                        if not v:
                            xpath_string = xpath_string + "[@" + str(k) + "]"
                        else:
                            if isinstance(v, list):
                                _vstring = ["contains(@" + str(k) + ", '" + str(_v) + "')" for _v in v]
                                vstring = " and ".join(_vstring)

                                xpath_string = xpath_string + "[" + vstring + "]"

                    div = self.browser.find_elements_by_xpath(xpath_string)

                    for d in div: scroll_items.append(d)

                if len(scroll_items) > 10:
                    j = 0
                    while j < 10:
                        try:
                            self.browser.execute_script("arguments[0].scrollIntoView(true)", scroll_items[j])
                            self.browser.execute_script("arguments[0].scrollIntoView(true)", scroll_items[0])
                            time.sleep(1)
                            j += 1
                        except Exception as e:
                            print(e)
                            j += 1
                            continue
                
                else:
                    for item in scroll_items:
                        try:
                            self.browser.execute_script("arguments[0].scrollIntoView(true)", item)
                            self.browser.execute_script("arguments[0].scrollIntoView(true)", scroll_items[0])
                            _body.send_keys(Keys.HOME)
                            time.sleep(1)
                        except Exception as e:
                            print(e)
                            continue

                self.browser.execute_script("arguments[0].scrollIntoView(true)", scroll_items[0])
                new_html = str(self.driver.page_source)
                new_content = Content(new_html, _title)
                new_attrs = new_content.last_divs

                i += 1
                if new_attrs == _attrs:
                    break
                else:
                    continue

            return self.browser.page_source

        except:
            return None

    def __is_html(self, response_headers):
        """
        Check if page is html
        """

        if 'Content-Type' in result.headers:
            content_type_data = Compare(["text/html"])
            match_result = content_type_data.eval(response_headers['Content-Type'])

            if match_result:
                similarity = float(match_result[0]['similarity'].strip("%"))

                if similarity >= 50:
                    return True
        
        return False

    def get_id(self):
        """
        Method to get pid of thread
        """
        for id, thread in threading._active.items(): 
            if thread is self: 
                return id
    
    def stop(self):
        """
        Method to raise stop flag for threading
        """

        self.stop_thread = True
