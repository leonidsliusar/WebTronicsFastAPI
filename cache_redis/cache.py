import redis
from settings import settings


r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)


def add_rate(rate_type: str, post_id: int, email: str) -> int:
    added = r.sadd(f'{rate_type}:{str(post_id)}:set', email)
    return added


def remove_rate(rate_type: str, post_id: int, email: str):
    r.srem(f'{rate_type}:{str(post_id)}:set', email)


def show_reviewers(rate_type: str, post_id: int) -> set:
    result = r.smembers(f'{rate_type}:{str(post_id)}:set')
    return result


def check_exists_rate(rate_type: str, post_id: int, email: str) -> bool:
    is_member = r.sismember(f'{rate_type}:{str(post_id)}:set', email)
    return is_member


def get_rate(rate_type: str, post_id: int) -> int:
    length = r.scard(f'{rate_type}:{post_id}:set')
    return length
