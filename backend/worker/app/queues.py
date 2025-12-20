from rq import Queue
from .deps import get_redis

q_outbox = Queue("outbox", connection=get_redis())
