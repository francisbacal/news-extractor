from urllib.parse import urlparse

class MediaURL:
    """
    Class for clean article media link and returns an urlparse object
        @params:
        link         - Required    : media src url (String)
    """
    def __init__(self, link):
        parsed_url = urlparse(link)

        if parsed_url.scheme == "":

            if re.match(r"^\/\/", link):
                new_link = f"http:{link}"
            
            elif re.match(r"^\/", link):
                new_link = link
            
            else:
                new_link = f"http://{link}"
        
            new_parsed_url = urlparse(new_link)

            self.scheme = new_parsed_url.scheme
            self.netloc = new_parsed_url.netloc
            self.path = new_parsed_url.path
        
        else:
            self.scheme = parsed_url.scheme
            self.netloc = parsed_url.netloc
            self.path = parsed_url.path

        if self.scheme == "":
            prefix = ""
        else:
            prefix = f"{self.scheme}://"

        self.link = f"{prefix}{self.netloc}{self.path}"