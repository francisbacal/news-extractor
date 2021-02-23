from dataclasses import dataclass, field
from typing import List

@dataclass
class AuthorVariables:
    comment_keys: List = field(default_factory=lambda: ["COMMENT"])
    footer_keys: List = field(default_factory=lambda: ["FOOTER", "SOCIAL", "SHARE", "FACEBOOK", "TWITTER"])
    author_keys: List = field(default_factory=lambda: ["AUTHOR", "BYLINE"])

    tags_for_decompose: List = field(default_factory=lambda: ["nav", "script", "time"])
    author_tags: List = field(default_factory=lambda: ["span", "a", "p", "div"])