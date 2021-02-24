"""
Endpoints Custom Exceptions
"""

class APIServerError(Exception):
    def __init__(self, error: str):
        super().__init__(f"API Server Error: {error}")

class WebsiteError(Exception):
    def __init__(self, error: str):
        super().__init__(f"Website Error Encountered: {error}")

class ArticlesAPIError(Exception):
    def __init__(self, error: str):
        super().__init__(f"Error encountered in Articles API: {error}")