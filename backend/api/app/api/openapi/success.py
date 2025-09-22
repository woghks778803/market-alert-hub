# 성공 응답 공통 프리셋
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel

def _success(
    status: int,
    model: Type[BaseModel],
    description: str,
    example: Optional[Dict[str, Any]] = None,
) -> Dict[int, Any]:
    return {
        status: {
            "description": description,
            "model": model,  
            "content": {"application/json": {"example": example}} if example else {},
        }
    }

def OK(model: Type[BaseModel], *, description: str = "성공", example: Optional[Dict[str, Any]] = None):
    return _success(200, model, description, example)

def CREATED(model: Type[BaseModel], *, description: str = "생성됨", example: Optional[Dict[str, Any]] = None):
    return _success(201, model, description, example)

