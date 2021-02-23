from seleniumwire import webdriver


class Seledriver:
    """
    Selenium class with name
        @params:  
            name            -   name of browser
            browser         -   browser type [chrome, fox]
            headless        -   option for headless browser
            timeout         -   selenium timeout [Default: 300]
    """
    def __init__(self, name=None, browser:str="fox", headless: bool=True, timeout: int=300):
        
        self.name = name or self.__random_name()
        self.headless = headless

        # INSTANTIATE SELENIUM DRIVER

        if browser == "fox":
            options = self.__set_driver_options(headless=self.headless, browser=browser)
            driver = webdriver.Firefox(options=options)
            driver.set_page_load_timeout(timeout)  

        else:
            options = self.__set_driver_options(headless=self.headless, browser="chrome")
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(timeout)

    
        self.driver = driver
  
    def __set_driver_options(self, headless=True, browser="chrome"):
        """
        Private method to set options for browser
            @params:  
                headless          -   option for headless browser
                browser           -   type of browser ['chrome', 'firefox']
        """
        if browser == "chrome":
            from selenium.webdriver.chrome.options import Options
            options = Options()

            if os.name != 'nt':
                options.binary_location = "/opt/google/chrome/chrome"
            elif os.name == 'nt':
                options.add_argument("--disable-gpu")
      
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-setuid-sandbox")
            if headless:
                options.headless = True
            options.add_argument("--log-level=3")
            options.add_argument("--disable-logging")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--incognito")
            options.add_argument("--start-maximized")
      
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
    
        if browser == "fox":
            from selenium.webdriver.firefox.options import Options
            options = Options()

            if headless:
                options.headless = True
        
            options.add_argument('-private')

        return options
  
    def __random_name(self):
        """
        Private method to generate random name
        """
        alpha_strings = string.ascii_lowercase + string.digits
        result = ''.join((random.choice(alpha_strings) for i in range(8)))

        return str(result)