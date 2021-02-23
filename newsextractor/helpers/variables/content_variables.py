from dataclasses import dataclass, field
from typing import List

@dataclass
class ContentVariables:
    invalid_keys: List = field(default_factory=lambda: ['privacy', 'ads', 'advertisement', 'newsletter', 'modal', 
                                                'subscription', 'related-articles', 'recommended-posts', 
                                                'asset-below', 'related-posts', 'caption', 'stats', 'nav-links'])

    content_tags: List = field(default_factory=lambda: ['article','div'])
    content_keys: List = field(default_factory=lambda: ['content', 'main', 'article', 'body'])
    tags_for_decompose: List = field(default_factory=lambda: ['script', 'nav', 'forms', 'button', 'aside', 'style', 'ul', 'select'])