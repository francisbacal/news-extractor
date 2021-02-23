from options import *
from pytest import mark

options = Options()

# @mark.skip()
def test_endpoint_global():
    global_link = options.get_endpoint('global-link')

    assert global_link == "http://192.168.3.143:4040/mmi-endpoints/v0/global-link"

def test_endpoint_global_count():
    global_count = options.get_endpoint('global-link-count')

    assert global_count == "http://192.168.3.143:4040/mmi-endpoints/v0/global-link/count_custom_query"


def test_endpoint_global_custom():
    global_custom = options.get_endpoint('global-link-custom')

    assert global_custom == "http://192.168.3.143:4040/mmi-endpoints/v0/global-link/custom_query"

def test_endpoint_article():
    global_link = options.get_endpoint('article')

    assert global_link == "http://192.168.3.143:4040/mmi-endpoints/v0/article"

def test_endpoint_article_count():
    global_count = options.get_endpoint('article-count')

    assert global_count == "http://192.168.3.143:4040/mmi-endpoints/v0/article/count_custom_query"


def test_endpoint_article_custom():
    global_custom = options.get_endpoint('article-custom')

    assert global_custom == "http://192.168.3.143:4040/mmi-endpoints/v0/article/custom_query"

def test_endpoint_lambda_article_media_val():
    lambda_article_media = options.get_endpoint('lambda-article-media-value')

    assert lambda_article_media == "http://192.168.3.143:3030/lambda-api/article/media_values"