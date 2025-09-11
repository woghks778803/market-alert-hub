from fastapi import status


class AppError(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
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
    status_code = status.HTTP_400_BAD_REQUEST
    code = "validation_error"


class AuthError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"


class PermissionError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"
