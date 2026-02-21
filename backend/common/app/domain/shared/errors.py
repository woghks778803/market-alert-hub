from http import HTTPStatus as HS


class AppError(Exception):
    status_code: int = HS.INTERNAL_SERVER_ERROR
    code: str = "internal_error"
    message: str = "Internal server error"
    target: str | None = None
    meta: dict | None = None

    def __init__(
        self,
        message: str | None = None,
        *,
        target: str | None = None,
        meta: dict | None = None
    ):
        if message:
            self.message = message
        if target:
            self.target = target
        if meta:
            self.meta = meta
        super().__init__(self.message)


class ValidationAppError(AppError):
    status_code = HS.BAD_REQUEST
    code = "validation_error"


class AuthError(AppError):
    status_code = HS.UNAUTHORIZED
    code = "unauthorized"


class PermissionError(AppError):
    status_code = HS.FORBIDDEN
    code = "forbidden"


class NotFoundError(AppError):
    status_code = HS.NOT_FOUND
    code = "not_found"


class ConflictError(AppError):
    status_code = HS.CONFLICT
    code = "conflict"


class InternalServerError(AppError):
    status_code = HS.INTERNAL_SERVER_ERROR
    code = "internal_error"


class TemplateRenderError(AppError):
    status_code = HS.INTERNAL_SERVER_ERROR
    code = "template_render_error"


class EmailSendError(AppError):
    status_code = HS.BAD_GATEWAY  # (외부 서비스 오류)
    code = "email_send_error"


class RateLimitError(AppError):
    status_code = HS.TOO_MANY_REQUESTS  # 429
    code = "rate_limited"
