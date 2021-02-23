from ..helpers import Compare, TitleVariables

from bs4 import BeautifulSoup
import re, time, nltk


class Title:
    """
    Class to find News Title
        @params:
            html        -   news page source
    """

    def __init__(self, html: str):
        """
        Initialize method
        """

        self.soup = BeautifulSoup(html, "html.parser")
        self.title_variables = TitleVariables()
        self.text = None

        #CLEAN DOM
        self.__clean_html()

        # FIND TITLE TAG IF EXISTING ELSE GET FROM H1
        try:
            title_tag = self.soup.find('title').string
        except:
            title_tag = self.soup.find('h1').string

        # FILTER AND TOKENIZE TITLE TAG
        filtered_title_tag = re.sub(r'[\W_]\s', ' ', title_tag)
        self.title_tag_tokens = nltk.word_tokenize(filtered_title_tag.upper())


        # FIND ALL PROBABLE TAG FOR TITLE
        for tag in self.title_variables.title_tags:
            blocks = self.soup.find_all(tag)
            probab_title = self.__iterate_tag(blocks)

            self.text = probab_title if probab_title else None

            if self.text: break

        if not self.text:
            self.text = title_tag
        
                
    def __iterate_tag(self, blocks):     
        """
        Iterates bs4 blocks to find probable title
        """
        for block in blocks:
            text = block.get_text(separator=" ", strip=True)   

            if text:
                text_tokens = nltk.word_tokenize(text.upper())
                count_percentage = len(text_tokens) / len(self.title_tag_tokens)

                if len(text_tokens) < 3:
                    continue

                if count_percentage <= 0.5:
                    continue

                count = 0
                for token in text_tokens:
                    if token in self.title_tag_tokens: count += 1
                
                similarity = count / len(text_tokens)
                if similarity >= 0.75:
                    return text

    def __clean_html(self):
        """
        Clean up page source
        """
        # REMOVE UNRELATED TAGS
        for key in self.title_variables.tags_for_decompose:
            for tag in self.soup.find_all(key):
                tag.decompose()
