"""Registry + factory mapping a source's config.py `name` (e.g.
"CyberNews") to its Source implementation. producer.py and tasks.py both
go through get_parser() instead of branching on the source name
themselves — adding a new source means adding one entry here and one new
module, not touching either of those files.
"""

from .base import Source
from .cybernews import CyberNewsSource

_PARSERS: dict[str, type[Source]] = {
    "CyberNews": CyberNewsSource,
}


def get_parser(name: str) -> Source:
    try:
        return _PARSERS[name]()
    except KeyError:
        raise ValueError(f"No Source registered for source {name!r} (see parsers/registry.py)") from None
