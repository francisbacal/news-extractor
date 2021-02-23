from bs4 import BeautifulSoup
from ..helpers import Compare, recursive_iterate, AuthorVariables
from nltk.corpus import stopwords

import nltk, re, string


class Author:
    """
    Get the most probable author
    """

    def __init__(self, html: str):
        """
        Initialize method
        """

        self.soup = BeautifulSoup(html, "html.parser")
        self.names = []
        self.stop_words = set(stopwords.words('english'))

        #CLEAN DOM
        self.__clean_html()

        # SET UP DATA FOR AUTHOR KEY COMPARISON
        self.author_data = Compare(self.author_variables.author_keys)

        # FIND ALL PROBABLE TAG FOR AUTHORS
        for tag in self.author_variables.author_tags:
            blocks = self.soup.find_all(tag)
            author = self.__iterate_tag(blocks)

            if author:
                self.names = [author]
                break

    def __iterate_tag(self, blocks):     
        """
        Iterates bs4 blocks to find probable author
        """
        for block in blocks:
            attr_values = block.attrs.values()   

            for attr_val in attr_values:
                if any([attr_val == "", len(attr_val) > 20, not attr_val]):
                    continue

                if isinstance(attr_val, list):
                    final_list = recursive_iterate(attr_val)

                    for val in final_list:
                        if len(val) > 25:
                            continue

                        result = self.author_data.eval(val)

                        if result:
                            similarity = int(re.search(r'\d+', result[0]['similarity']).group())
                            if similarity < 60:
                                continue

                            possible_auth = block.get_text(separator=" ", strip=True).replace("\n", " ")

                            if possible_auth == "":
                                continue

                            possible_auth_tokens = nltk.word_tokenize(possible_auth)
                            filtered_auth = [word for word in possible_auth_tokens if word.lower() not in self.stop_words]
                            filtered_auth = [word for word in filtered_auth if word.lower() not in string.punctuation]

                            possible_auth = " ".join(filtered_auth)

                            return possible_auth

                    continue

                result = self.author_data.eval(attr_val)

                if result:
                    similarity = int(re.search(r'\d+', result[0]['similarity']).group())

                    if similarity < 60:
                        continue

                    possible_auth = block.get_text(separator=" ", strip=True).replace("\n", " ")
                    
                    if possible_auth == "":
                        continue
            
                    possible_auth_tokens = nltk.word_tokenize(possible_auth)
                    filtered_auth = [word for word in possible_auth_tokens if word.lower() not in self.stop_words]
                    filtered_auth = [word for word in filtered_auth if word.lower() not in string.punctuation]
                    possible_auth = " ".join(filtered_auth)

                    return possible_auth 

    def __clean_html(self):
        """
        Clean up page source
        """
        self.author_variables = AuthorVariables()

        # DECOMPOSE TAGS WITH INVALID KEY OR MATCHING INVALID KEY
        for tag in self.soup.find_all(self.__is_invalid_tag):
            tag.decompose()

        # REMOVE UNRELATED TAGS
        for key in self.author_variables.tags_for_decompose:
            for tag in self.soup.find_all(key):
                tag.decompose()
    
    def __is_invalid_tag(self, tag):
        """
        Returns the tag that contains specific invalid keyword
            @params:
                tag     -   BS4 tag/element
        """
        INVALID_KEYS = self.author_variables.comment_keys + self.author_variables.footer_keys
        
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
                        _comparison = INVALID_KEY_DATA.eval(_v)

                        if _comparison:
                            similarity = str(_comparison[0]['similarity']).rstrip("%")
                        
                            if int(similarity) >= 70: return True

