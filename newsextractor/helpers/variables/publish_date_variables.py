from dataclasses import dataclass, field
from typing import List

@dataclass
class PubDateVariables:
    date_keys: List = field(default_factory=lambda: ["DATE", "PLAT"])

    tags_for_decompose: List = field(default_factory=lambda: ["script"])
    pub_date_tags: List = field(default_factory=lambda: ["time","span", "a", "p", "div"])