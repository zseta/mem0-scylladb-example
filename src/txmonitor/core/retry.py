"""Retry helper for mem0 calls that can hit the LLM provider's rate limits.

A short backoff-and-retry absorbs occasional 429s from bursts of mem0.add()
calls without needing to hand-tune delays around a limit mem0 doesn't expose.
"""

import time

from mem0.exceptions import LLMError

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_SECONDS = 15


def with_rate_limit_retry(fn, *args, max_attempts=DEFAULT_MAX_ATTEMPTS, backoff_seconds=DEFAULT_BACKOFF_SECONDS, **kwargs):
    for attempt in range(1, max_attempts + 1):
        try:
            return fn(*args, **kwargs)
        except LLMError as e:
            is_rate_limit = "rate_limit" in str(e) or "429" in str(e) or "413" in str(e)
            if not is_rate_limit or attempt == max_attempts:
                raise
            time.sleep(backoff_seconds)
