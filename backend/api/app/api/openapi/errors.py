# 공통 응답 스펙/프리셋
from typing import Any, Dict, Optional
from app.api.schema import ErrorSchema 
from app.api.common.envelope import Envelope, ErrorBody

from .types import Responses

# 기본 에러 예시 생성기
def err_example(
    code: str,
    message: str,
    *,
    target: str | None = None,
    meta: Dict[str, Any] | None = None,
    request_id: str = "00000000-0000-0000-0000-000000000000",
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "error": {
            "code": code,
            "message": message,
            "target": target,
            "meta": meta,
        },
    }

# 단일 상태코드 응답 블록 생성
def err(status: int, description: str, example: Dict[str, Any] | None = None) -> Responses:
    return {
        status: {
            "description": description,
            "model": ErrorSchema.ErrorResponse,        
            "content": {
                "application/json": {
                    "example": example or err_example("unknown_error", "Something went wrong")
                }
            },
        }
    }

# 자주 쓰는 프리셋
ERR_400 = err(
    400,
    "유효하지 않은 입력(ValidationAppError)",
    err_example(
        "validation_error",
        "Validation failed",
        meta={
            "errors": [
                {"loc": ["body", "role"], "msg": "Input should be 'user' or 'admin'"},
            ]
        },
    ),
)
ERR_401 = err(401, "인증 실패(AuthError)",
              err_example("unauthorized", "Missing or invalid token"))
ERR_403 = err(403, "권한 없음(PermissionError)",
              err_example("forbidden", "Not allowed"))
ERR_404 = err(404, "리소스 없음(NotFoundError)",
              err_example("not_found", "Resource not found"))
ERR_409 = err(409, "충돌(ConflictError)",
              err_example("conflict", "Email already exists", target="email"))
ERR_500 = err(500, "서버 오류(AppError)",
              err_example("internal_error", "Internal server error"))

