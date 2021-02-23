"""
News Extractor Custom Exceptions
"""

class NewsError(Exception):
    def __init__(self, error: str):
        super().__init__(f"News Module Error: {error}")

class HelperError(Exception):
    def __init__(self, error: str):
        super().__init__(f"Helper Error: {error}")

class NoResponseError(Exception):
    def __init__(self, error: str):
        super().__init__(f"Helper Error: {error}")