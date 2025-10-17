from typing import Dict, Any

from .types import Responses

def combine(*blocks: Responses) -> Responses:
    """여러 응답 블록을 합치는 헬퍼."""
    merged: Responses = {}
    for b in blocks:
        merged.update(b)
    return merged
