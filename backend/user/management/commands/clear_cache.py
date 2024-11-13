import logging
from typing import Any

import redis
from django.conf import settings
from django.core.cache import cache
from django.core.management import BaseCommand


# Taken from PCx:
# https://github.com/pennlabs/penn-courses/blob/master/backend/review/management/commands/clearcache.py


def clear_cache() -> int:
    # If we are not using redis as the cache backend, then we can delete everything from the cache.
    if (
        settings.CACHES is None
        or settings.CACHES.get("default").get("BACKEND") != "django_redis.cache.RedisCache"
    ):
        cache.clear()
        return -1

    # If redis is the cache backend, then we need to be careful to only delete django cache entries,
    # since celery also uses redis as a message broker backend.
    r = redis.Redis.from_url(settings.REDIS_URL)
    count = 0
    for key in r.scan_iter("*views.decorators.cache*"):
        r.delete(key)
        count += 1
    return count


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> None:
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        del_count = clear_cache()
        print(f"{del_count if del_count >= 0 else 'all'} cache entries removed.")
