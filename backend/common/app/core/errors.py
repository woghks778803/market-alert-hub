from dataclasses import dataclass
from http import HTTPStatus
from typing import Any
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError, EndpointConnectionError

@dataclass
class ErrorReport:
    code: str
    message: str | None
    http_status: int | None
    request_id: str | None
    retryable: bool

_RETRYABLE = {"SES.Throttle","5XX","NET.TIMEOUT","NET.CONNECT"}

def _from_domain_like(e: Exception) -> ErrorReport | None:
    code = getattr(e, "code", None); status = getattr(e, "status_code", None)
    if code and status is not None:
        meta: Any = getattr(e, "meta", None)
        return ErrorReport(str(code), getattr(e, "message", None) or str(e),
                           int(status), (meta or {}).get("request_id") if isinstance(meta, dict) else None, False)
    return None

def classify_exception(e: Exception) -> ErrorReport:
    d = _from_domain_like(e)
    if d: return d
    if isinstance(e, ClientError):
        r = getattr(e, "response", {}) or {}
        err, rm = (r.get("Error") or {}), (r.get("ResponseMetadata") or {})
        code = err.get("Code") or "SES.Error"; status = rm.get("HTTPStatusCode")
        mapped = {"Throttling":"SES.Throttle","TooManyRequestsException":"SES.Throttle","MessageRejected":"SES.MessageRejected"}.get(
            code, "5XX" if (status and status >= 500) else code)
        return ErrorReport(mapped, err.get("Message") or str(e), status, rm.get("RequestId"), mapped in _RETRYABLE)
    if isinstance(e, (NoCredentialsError, PartialCredentialsError)):
        return ErrorReport("AUTH.CREDENTIALS", str(e), None, None, False)
    if isinstance(e, EndpointConnectionError):
        return ErrorReport("NET.CONNECT", str(e), None, None, True)
    if isinstance(e, TimeoutError):
        return ErrorReport("NET.TIMEOUT", str(e), None, None, True)
    return ErrorReport("UNKNOWN", str(e)[:512], None, None, False)
