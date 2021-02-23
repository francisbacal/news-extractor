from bs4 import BeautifulSoup, element as bs4Element
from ..helpers import Compare, Stopwords, MediaURL, ContentVariables, catch
from pebble import concurrent
from pprint import pprint


import nltk, re, string, time, math

stopwords = Stopwords()

class Content:
    """
    Class to get the article content
        @params:  
            html            -   page source of article
            headline        -   Title of article
            lang            -   article language
    """

    def __init__(self, html: str, headline: str, lang: str="en"):
        """
        Initialize method
        """
        self.content_variables = ContentVariables()

        self.soup = BeautifulSoup(html, 'html.parser')
        self.headline = headline
        self.images = []
        self.text = None
        self.content_container = None
        self.no_child_containers = []
        self.iteration = 0
        self.last_divs = []

        # SETUP STOPWORDS
        if lang != "en":
            sw_lang = set(getattr(stopwords, lang))
            en_lang = set(getattr(stopwords, "en"))

            self.stop_words = sw_lang.union(en_lang)
        else:
            self.stop_words = set(getattr(stopwords, "en"))
        
        # TOKENIZE AND FILTER HEADLINE/TITLE
        self.filtered_headline_tokens = self.__tokenize(headline)

        # CREATE COMPARISON DATA
        self.data = Compare(self.filtered_headline_tokens)

        self.div_strings = [] # CONTAINER OF STRINGS IN A DIV ELEMENT
        self.stripped_strings = []

        # CLEAN PAGE SOURCE
        self.__clean_html()

        # GET BODY TAG
        self.body_node = catch('None', lambda: self.soup.find('body'))

        # GET ALL DIV AND EXTRACT TEXT CONTENT
        
        for tag in self.content_variables.content_tags:
            blocks = self.body_node.find_all(tag) if self.body_node is not None else self.soup.find_all(tag)
            
            if not list(blocks):
                continue

            self.__iterate_tag(blocks)

            if self.text:
                break
            
    def __iterate_tag(self, blocks):
        """
        Iterates bs4 blocks to find probable content
        """
        token_add_count = 1 # COUNTER LIMIT FOR ADDING TOKEN
 
        for block in blocks:
            # GET HIGHEST STRIPPED STRINGS
            if len(self.stripped_strings) < len(list(block.stripped_strings)):
                self.stripped_strings = list(block.stripped_strings)
                
                self.content_container = block

        # RECURSIVE ITERATE CONTAINER
        self.iteration = 1
        self.__recursive_iterate(self.content_container)

        # USED CASE: DIFFERENT DIV WITH SAME ATTRIBUTES, MERGE AND COMBINE TO A SINGLE STRING
        self.__merge_containers()

        # GET ALL DIVS WITH STRINGS AND SCORE POSSIBLE STRINGS
        probable_strings = self.__get_possible_strings()
        
        # SCORING OF POSSIBLE CONTENT
        scored_strings = self.__score_strings(probable_strings)

        if not scored_strings:
            self.__recursive_iterate(self.content_container)
        
        # GET STRINGS WITH LOWEST INVALID SCORE
        lowest_invalid_score = 1
        lowest_invalid_strings = None
        longest_string = 0

        # CHECK IF ALL STRINGS HAVE AN INVALID SCORE OF 0
        # AND GET LONGEST STRING

        for scored_string in scored_strings:
            strings = scored_string['strings']
            joined_string = "\n".join(strings)
            strings_length = len(joined_string)
            invalid_score = scored_string['score']['invalid_score']

            if invalid_score <= lowest_invalid_score and strings_length > longest_string: 
                lowest_invalid_score = invalid_score
                lowest_invalid_strings = strings
                longest_string = strings_length

        # CHECK FOR INVALID STRINGS AND CONTENT RELATIVITY TO TITLE
        relativity_count = 0
        token_add_count = 0
        LOWEST_INVALID_STRINGS_LENGTH = len(lowest_invalid_strings)
        INVALID_STRING_DATA = Compare(self.content_variables.invalid_keys)

        for string in lowest_invalid_strings:

            if len(string) < 80:
                #CHECK IF INVALID
                invalid_result = INVALID_STRING_DATA.eval(string)
                match_result = self.data.eval(string)
                invalid_similarity = 0
                match_similarity = 0

                if invalid_result:
                    invalid_similarity = int(re.search(r'\d+', invalid_result[0]['similarity']).group())
                    if invalid_similarity > 70:
                        continue
                
                if match_result:
                    match_similarity = int(re.search(r'\d+', match_result[0]['similarity']).group())
                    if match_similarity <= 70:
                        continue 
                
                if any([
                    (not match_result and not invalid_result), 
                    (not match_result and invalid_similarity <= 70)]):
                    continue
            
            # CHECK FOR RELATIVITY
            comparison_result = self.data.eval(string)

            if comparison_result:
                relativity_count += 1
            
                # ADD TOKEN TO INCREASE ACCURACY UNTIL token_add_count
                if token_add_count <= math.floor(LOWEST_INVALID_STRINGS_LENGTH * 0.33):
                    additional_tokens = [token.lower() for token in nltk.word_tokenize(string) if token.lower() not in self.stop_words]
                    new_tokens = [token for token in additional_tokens if token not in self.filtered_headline_tokens]
                    self.filtered_headline_tokens.extend(new_tokens)
                    self.filtered_headline_tokens = [token for token in self.filtered_headline_tokens if re.search(r"\w+", token)]

                    self.data = Compare(self.filtered_headline_tokens)
                    token_add_count += 1
                
                self.div_strings.append(string)
        
        self.text = "\n\n".join(self.div_strings)

        return self.text

    def __merge_containers(self):
        """
        Merge all possible containers with same class or attributes
        """
        merged_containers = []

        for container in self.no_child_containers:
            added = False
            attribute = container.attrs

            
            for merged in merged_containers:
                if merged[1] == attribute:
                    merged[0].append(container)
                    added = True
                    self.no_child_containers.remove(container)
                if added:
                    break
    
            if not added:
                merged_containers.append([[container], attribute])
                self.no_child_containers.remove(container)
        
        if merged_containers:
            self.no_child_containers = []

            for container in merged_containers:
                soup = BeautifulSoup()
                new_div = soup.new_tag('div', attrs=container[1])

                for tag in container[0]:
                    new_p = soup.new_tag('p')
                    new_p.string = "\n".join(list(tag.stripped_strings))
                    new_div.append(new_p)

                self.no_child_containers.append(new_div)
        
    def __get_possible_strings(self):
        """
        Get all possible content strings
        """

        strings = []
        
        for container in self.no_child_containers:
            container_strings = list(container.stripped_strings)
            if container_strings and container_strings not in strings:
                strings.append(container_strings)

        strings = [string for string in strings]

        highest_ratio = 0
        probable_strings = []
        for string in strings:
            if isinstance(string, list):
                word_count = 0
                
                for word in string:
                    if len(word) >= 100:
                        for string in strings:
                            if string not in probable_strings:
                                probable_strings.append(string)
                        break
                    if len(word) >= 30:
                        word_count += 1
                
                ratio = word_count / len(string)
                
                if ratio >= 0.5:
                    joined_string = "\n\n".join(string)

                    if len(joined_string) >= 100:
                        probable_strings.append(joined_string)

        return probable_strings

    def __score_strings(self, strings: list):
        """
        Score for possible content
        """
        match_tokens = self.filtered_headline_tokens
        MATCH_KEY_DATA = Compare(self.filtered_headline_tokens)
        INVALID_KEY_DATA = Compare(self.content_variables.invalid_keys)
        
        scored_strings = []

        score = {
            "no_of_words_negative": 0,
            "length_of_list": 0,
            "invalid_score": 0
        }

        for string in strings:
            no_of_words_negative = 0

            if isinstance(string, list):
                
                for words in string:
                    words_to_list = self.__tokenize(words)
                    
                    match_count = 0
                    invalid_count = 0
                    add_token_count = 0

                    if len(words_to_list) == 0:
                        no_of_words_negative += 1

                    elif 1 <= len(words_to_list)  <= 4:
                        
                        # CHECK FOR INVALID KEYS AND MATCH KEYS
                        for word in words_to_list:
                            invalid_key_result = INVALID_KEY_DATA.eval(word)
                            match_key_result = MATCH_KEY_DATA.eval(word)

                            if invalid_key_result: invalid_count += 1

                            if match_key_result: 
                                match_count += 1

                                # INCREASE MATCH_TOKENS TO INCREASE ACCURACY UNTIL add_token_count >= 4
                                if not add_token_count == 4:
                                    match_tokens.extend(words_to_list)
                                    MATCH_KEY_DATA = Compare(match_tokens)
                                    add_token_count += 1

                        # COMPUTE FOR RATIO OF RESULTS TO LIST LENGTH
                        invalid_ratio = invalid_count / len(words_to_list)
                        match_ratio = match_count / len(words_to_list)


                        if invalid_ratio >= 0.5 or match_ratio >= 0.5: no_of_words_negative += 1

                        if invalid_ratio == 0 and match_ratio == 0: no_of_words_negative += 1

                    elif len(words_to_list) > 4:
                        no_of_words_negative = 0

                score['length_of_list'] = len(string)
                score['no_of_words_negative'] = no_of_words_negative
                score['invalid_score'] = no_of_words_negative / len(string)

                # FILTER OUT STRINGS WITH INVALID SCORE OF 0.7++
                if score['invalid_score'] <= 0.7:

                    string_score = {
                        "strings": string,
                        "score": score
                    }

                    scored_strings.append(string_score)

                    
        return scored_strings
                    
    def __recursive_iterate(self, tag: type(bs4Element.Tag)):
        """
        Recursive iterate an element until last node has no children
        """ 
        child_tags = tag.find_all(self.__is_valid_tag)
        
        # if not child_tags:
        #     for content_tag in self.content_variables.content_tags:
        #         child_tags = tag.find_all(content_tag)

        if child_tags is not None and self.iteration <= 30:
            
            if isinstance(child_tags, bs4Element.ResultSet):
                for child_tag in child_tags:
                    if child_tag not in self.last_divs:
                        self.__recursive_iterate(child_tag)
        else:
            self.last_divs.append(tag)
        
        # REITERATE CONDITIONS
        conditions = [
                not self.__score_links(tag),
                tag.text.strip() == "",
                tag in self.last_divs
            ]

        #FIND PARENT TAG IF CONDITIONS ARE MET
        if any(conditions):
            self.last_divs.append(tag)
            
            parent_tag = self.__find_parent(tag)

            if parent_tag != self.body_node:
                self.__recursive_iterate(parent_tag)
        else:
            if tag not in self.no_child_containers:
                self.no_child_containers.append(tag)

    def __score_links(self, tag: type(bs4Element.Tag)):
        """
        Check for number of links in a tag
        """
        child_links = list(tag.find_all('a', href=True))
        tag_strings = list(tag.stripped_strings)

        if not tag_strings:
            return False

        link_string_ratio = len(child_links) / len(tag_strings)

        if len(child_links) > 5 and link_string_ratio > 0.6:    
            return False
        elif len(child_links) > 10:
            return False
        else:
            return True

    def __clean_html(self):
        """
        Clean up page source
        """

        # DECOMPOSE TAGS WITH INVALID KEY OR MATCHING INVALID KEY
        for tag in self.soup.find_all(self.__is_invalid_tag):
            if self.__is_valid_tag(tag): continue
            tag.decompose()

        # REMOVE UNRELATED TAGS
        for key in self.content_variables.tags_for_decompose:
            for tag in self.soup.find_all(key):
                tag.decompose()

    def __find_parent(self, tag):
        """
        Find parent of a tag
        """
        
        parent_tag = tag.parent

        parent_string = list(parent_tag.stripped_strings)

        if not parent_string:
            return self.__find_parent(parent_tag)
        elif len(parent_string) <= 3:
            return self.__find_parent(parent_tag)
        else:
            return parent_tag 

    def __is_valid_tag(self, tag):
        """
        Returns the tag that contains specific valid keyword
            @params:
                tag     -   BS4 tag/element
        """
        VALID_KEYS = self.content_variables.content_keys
        
        # GET COMPARISON DATA
        VALID_KEY_DATA = Compare(VALID_KEYS)
        comparison = None

        for _, v in tag.attrs.items():

            for key in VALID_KEYS:
                # SET TAG ATTRIBUTE VALUE FOR COMPARISON TO KEYS
                if not isinstance(v, list):
                    comparison = VALID_KEY_DATA.eval(v)
                
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
                        _comparison = VALID_KEY_DATA.eval(_v)

                        if _comparison:
                            similarity = str(_comparison[0]['similarity']).rstrip("%")
                        
                            if int(similarity) >= 70: return True

    def __is_invalid_tag(self, tag):
        """
        Returns the tag that contains specific invalid keyword
            @params:
                tag     -   BS4 tag/element
        """
        INVALID_KEYS = self.content_variables.invalid_keys
        
        # GET COMPARISON DATA
        INVALID_KEY_DATA = Compare(INVALID_KEYS)
        comparison = None

        for k, v in tag.attrs.items():
            if k not in ['class', 'id']: continue
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
                        
                            if int(similarity) >= 70:
                                return True

    def __tokenize(self, words):
        data_tokens = nltk.word_tokenize(words)
        filtered_tokens = [token.lower() for token in data_tokens if not token.lower() in self.stop_words]
        filtered_tokens = [token for token in filtered_tokens if re.search(r"\w+", token)]

        return filtered_tokens