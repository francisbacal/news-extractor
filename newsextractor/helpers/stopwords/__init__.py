from .tl import tl

from nltk.corpus import stopwords as nltk_stopwords
import advertools as advt


class Stopwords:
    """
    Class to generate stopwords
    """

    def __init__(self):
        self.en = set(nltk_stopwords.words('english'))
        self.es = advt.stopwords['spanish']
        self.tl = tl