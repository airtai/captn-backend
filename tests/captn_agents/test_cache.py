import os
from pathlib import Path

import diskcache

api_key_sweeden = os.getenv("AZURE_OPENAI_API_KEY_SWEEDEN")
api_key_canada = os.getenv("AZURE_OPENAI_API_KEY_CANADA")


def _skip_test_cache() -> None:
    if api_key_canada is None and api_key_sweeden is None:
        return

    pathlist = Path(".cache").iterdir()
    for path in pathlist:
        with diskcache.Cache(str(path)) as cache:
            for key in cache.iterkeys():
                assert api_key_sweeden not in key
                assert api_key_canada not in key

                value = cache.get(key=key)
                assert api_key_sweeden not in value
                assert api_key_canada not in value
