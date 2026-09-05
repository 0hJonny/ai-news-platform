"""Registry + factory mapping a source's config.py `name` (e.g.
"CyberNews") to a Source instance. producer.py and tasks.py both go
through get_parser() instead of branching on the source name themselves —
adding a new source means adding one entry here and one new module, not
touching either of those files.

This is also the composition root for dependency injection: a Source
doesn't build its own HttpClient (see http_client.py), so wiring which
concrete client each source gets happens here, in one place, rather than
inside every Source's __init__.
"""

from collections.abc import Callable

from .base import Source
from .cybernews import CyberNewsSource
from .http_client import CloudscraperHttpClient

_PARSERS: dict[str, Callable[[], Source]] = {
    "CyberNews": lambda: CyberNewsSource(CloudscraperHttpClient()),
}


def get_parser(name: str) -> Source:
    try:
        return _PARSERS[name]()
    except KeyError:
        raise ValueError(f"No Source registered for source {name!r} (see parsers/registry.py)") from None
