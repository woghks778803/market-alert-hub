from rq import Queue
from .redis_conn import get_redis

q_outbox = Queue("outbox", connection=get_redis())
