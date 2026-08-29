"""Shared Celery application for the Parser and Annotation workers.

Wires up the Celery app, its Redis broker/result backend, and queue
routing. It does NOT define any @app.task functions itself — those live
in `parser/tasks.py` and `annotation/tasks.py` inside each worker's own
container. Import this module from there as:

    from shared.celery_app import app

    @app.task(name="parsing.scrape_source")
    def scrape_source(...): ...

    @app.task(name="annotation.annotate_article")
    def annotate_article(...): ...

Routing below is keyed on that "parsing."/"annotation." task-name prefix
rather than on a module path, so it doesn't need to change once the actual
task modules exist — name the task, and it lands in the right queue.
"""

import os

from celery import Celery

BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")

app = Celery("ai_news_platform", broker=BROKER_URL, backend=BROKER_URL)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Late ack + prefetch=1: together these are what make the queue safe
    # against a worker dying mid-task. Late ack means a task is only
    # removed from Redis once it actually finishes (success OR failure),
    # not the moment a worker picks it up — so a killed worker's in-flight
    # task gets redelivered instead of silently vanishing. Prefetch=1 caps
    # how many unacked tasks a worker can hold at once (default is 4x
    # concurrency); without it, late-ack alone would still let a crash
    # lose/duplicate a whole prefetched batch instead of just the one task
    # actually being worked on.
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # task_acks_late's guarantee only kicks in once Celery actually notices
    # the worker is gone. task_reject_on_worker_lost=True makes it notice
    # immediately when a prefork child dies (segfault, OOM-killed) — the
    # parent process sees that directly and requeues right away. But if the
    # whole container/host disappears, nothing survives to report that, so
    # Redis's own visibility_timeout is the real backstop: an unacked
    # message just sits there until this many seconds pass, then goes back
    # on the queue. The Redis transport's default is 3600s (1 hour) — way
    # too long for a "worker died, retry the task" recovery — so it's cut
    # down here. Kept well above how long a single task should ever
    # realistically take (a slow LLM annotation included), since a
    # visibility_timeout shorter than that would redeliver a task that's
    # still legitimately running, not actually dead — the PATCH-based
    # updates in tasks.py are upsert-style/idempotent, so a duplicate
    # delivery just wastes some compute rather than corrupting data, but
    # it's still wasted work worth avoiding.
    task_reject_on_worker_lost=True,
    broker_transport_options={
        "visibility_timeout": 300,  # 5 minutes, not Redis's 1-hour default
    },
    task_routes={
        "parsing.*": {"queue": "parsing_queue"},
        "annotation.*": {"queue": "annotation_queue"},
    },
)
