from dataclasses import dataclass, field
from typing import List

@dataclass
class TitleVariables:
    title_keys: List = field(default_factory=lambda: ["DATE", "PLAT"])

    tags_for_decompose: List = field(default_factory=lambda: ["script"])
    title_tags: List = field(default_factory=lambda: ['h1', 'h2', 'h3'])

    main_title_tag: str= "title"