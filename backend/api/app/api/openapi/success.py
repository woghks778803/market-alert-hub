# 성공 응답 공통 프리셋
from typing import Any, Dict, Optional, Type
from http import HTTPStatus as HS
from pydantic import BaseModel

from .types import Responses


def _success(
    status: HS,
    model: Optional[Type[BaseModel]] = None,
    *,
    description: str,
    example: Optional[Dict[str, Any]] = None,
) -> Responses:
    response: Dict[str, Any] = {
        "description": description,
    }

    if status != HS.NO_CONTENT:
        if model is None:
            raise ValueError("model is required for success response with body")

        response["model"] = model

        if example:
            response["content"] = {
                "application/json": {
                    "example": example,
                }
            }

    res: Responses = {
        int(status): response,
    }
    return res


def OK(
    model: Type[BaseModel],
    *,
    description: str = "성공",
    example: Optional[Dict[str, Any]] = None
):
    return _success(HS.OK, model, description=description, example=example)


def CREATED(
    model: Type[BaseModel],
    *,
    description: str = "생성됨",
    example: Optional[Dict[str, Any]] = None
):
    return _success(HS.CREATED, model, description=description, example=example)


def NO_CONTENT(
    *,
    description: str = "삭제됨",
):
    return _success(
        HS.NO_CONTENT,
        description=description,
    )


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
