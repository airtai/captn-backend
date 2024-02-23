import os
from pathlib import Path

import diskcache

api_key_sweden = os.getenv("AZURE_OPENAI_API_KEY_SWEDEN")


def _skip_test_cache() -> None:
    if api_key_sweden is None:
        return

    pathlist = Path(".cache").iterdir()
    for path in pathlist:
        with diskcache.Cache(str(path)) as cache:
            for key in cache.iterkeys():
                assert api_key_sweden not in key

                value = cache.get(key=key)
                assert api_key_sweden not in value
