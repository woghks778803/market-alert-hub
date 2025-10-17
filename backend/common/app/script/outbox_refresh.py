import os
from redis import Redis
from rq import Queue
from rq.job import Job
from rq.registry import (
    ScheduledJobRegistry, StartedJobRegistry, DeferredJobRegistry,
    FinishedJobRegistry, FailedJobRegistry
)

host = os.getenv("REDIS_HOST", "redis")
port = int(os.getenv("REDIS_PORT", "6379"))
db   = int(os.getenv("REDIS_DB", "0"))
qname = os.getenv("RQ_QUEUE", "outbox")

r = Redis(host=host, port=port, db=db)
q = Queue(qname, connection=r)

print(f"[*] target redis={host}:{port}/{db}, queue='{qname}'")

# 1) 대기중(pending) 전부 제거
pending = len(q.job_ids)
print(f"[1] pending={pending} → empty()")
q.empty()

# 2) 레지스트리별 잡 삭제 (예약/시작됨/지연/완료/실패)
total = 0
for Reg in [ScheduledJobRegistry, StartedJobRegistry, DeferredJobRegistry,
            FinishedJobRegistry, FailedJobRegistry]:
    reg = Reg(qname, connection=r)
    ids = reg.get_job_ids()
    print(f"[2] {Reg.__name__}: {len(ids)} → delete()")
    for jid in ids:
        try:
            Job.fetch(jid, connection=r).delete()
            total += 1
        except Exception:
            pass

# 3) 경쟁 상태 대비 잔여 pending 한 번 더 정리
left = len(q.job_ids)
if left:
    print(f"[3] leftover pending={left} → empty() again")
    q.empty()

print(f"[DONE] registries deleted={total}, pending now={len(q.job_ids)}")
