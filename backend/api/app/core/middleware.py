import logging, uuid, time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
        finally:
            duration = (time.perf_counter() - start) * 1000
            logger.info(
                "request_end",
                extra={
                    "request_id": req_id,
                    "path": request.url.path,
                    "ms": round(duration, 2),
                },
            )
        response.headers["x-request-id"] = req_id
        request.state.request_id = req_id
        return response
