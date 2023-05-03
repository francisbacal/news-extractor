from options import *
from pytest import mark

import os

options = Options()

# @mark.skip()
def test_endpoint_global():
    global_link = options.get_endpoint('global-link')

    assert global_link == f"{os.environ['API_HOST']}:{os.environ['API_HOST']}/mmi-endpoints/v0/global-link"