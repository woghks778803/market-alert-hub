# 성공 응답 공통 프리셋
from typing import Any, Dict, Optional, Type
from http import HTTPStatus as HS
from pydantic import BaseModel

from .types import Responses


def _success(
    status: int,
    model: Type[BaseModel],
    description: str,
    example: Optional[Dict[str, Any]] = None,
) -> Responses:
    return {
        status: {
            "description": description,
            "model": model,
            "content": {"application/json": {"example": example}} if example else {},
        }
    }


def OK(
    model: Type[BaseModel],
    *,
    description: str = "성공",
    example: Optional[Dict[str, Any]] = None
):
    return _success(HS.OK, model, description, example)


def CREATED(
    model: Type[BaseModel],
    *,
    description: str = "생성됨",
    example: Optional[Dict[str, Any]] = None
):
    return _success(HS.CREATED, model, description, example)


def NO_CONTENT(
    model: Type[BaseModel],
    *,
    description: str = "삭제됨",
    example: Optional[Dict[str, Any]] = None
):
    return _success(HS.NO_CONTENT, model, description, {})


def wrap_example(
    data_example: Dict[str, Any],
    *,
    request_id: str = "00000000-0000-0000-0000-000000000000"
):
    return {
        "success": True,
        "data": data_example,
        "meta": {"request_id": request_id, "timestamp": "2025-09-30T00:00:00Z"},
    }
