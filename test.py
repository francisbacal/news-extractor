from newsextractor import Fetch, NewsVariables, TitleVariables, News, catch, StaticSource, Compare
from newsextractor.title import Title
from newsextractor.content import Content
from newsextractor.publish_date import PublishDate

from scraper.static import StaticScraper

from dateutil import parser
from bs4 import BeautifulSoup, element as bs4_element
from pprint import pprint
from newspaper import Article
import datefinder, datetime, json

# with open('sample5.html') as f:
#     s = f.read()

#############
### TITLE ###
#############

# title = Title(s)

###############
### CONTENT ###
###############

# content = Content(s, title.text)

# print("####################################################################")
# print(content.text)
# print("####################################################################")


#############
### NEWS ###
#############

# news = News('https://www.raindeocampo.com/2021/02/12/jt-express-unveils-promos-and-treats-to-usher-in-the-year-of-the-metal-ox', s)

# print(news.title)
# print(news.authors)
# print(news.publish_date)
# print(news.images)
# print(news.content)

# url = "https://www.msn.com/en-ph/money/business/greenfield-devt-facing-competition-complaint-over-isp-choice/ar-BB1dHcUk?li=BBr8Mkn"
url = "http://finance.yahoo.com/finance/news/pimco-canada-corp-announces-monthly-171900397.html"
# url = "https://ph.news.yahoo.com/2021-chevrolet-trailblazer-review-cute-150000979.html"
# url = "https://www.scmp.com/news/china/diplomacy/article/3122706/top-eu-diplomats-step-criticism-chinas-crackdown-hong-kong"
src = StaticSource(url)
s = src.text

# title = Title(s)
# print(title.text)
# content = Content(s, title.text)
# print(content.text)


news = News(url, s)

data = news.generate_data()

print(json.dumps(data, indent=4))

# pprint(data)

# c_data = Compare(["AUTHOR"])

# word = "cse_author"

# result = c_data.eval(word)

# print(result)