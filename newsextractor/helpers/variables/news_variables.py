from dataclasses import dataclass, field
from typing import List

@dataclass
class NewsVariables:
    invalid_keys: List = field(default_factory=lambda: ['privacy', 'newsletter', 'modal', 
                                                'subscription', 'related-articles', 'recommended-posts', 
                                                'asset-below', 'card'])
    tags_for_decompose: List = field(default_factory=lambda: ['script', 'forms', 'button', 'aside'])

    invalid_title_keys: List = field(default_factory=lambda: ["page not found", "attention required!", "Página no encontrada"])