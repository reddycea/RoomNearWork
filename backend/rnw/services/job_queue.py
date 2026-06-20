from __future__ import annotations

import os

from redis import Redis
from rq import Queue


def get_queue(name: str = "default") -> Queue:
    return Queue(name, connection=Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0")))


def enqueue_or_run(fn, *args, **kwargs):
    from flask import current_app
    if current_app.config.get("RUN_JOBS_INLINE", True):
        return fn(*args, **kwargs)
    return get_queue().enqueue(fn, *args, **kwargs)
