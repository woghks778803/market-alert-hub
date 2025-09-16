from typing import Dict, Any

def combine(*blocks: Dict[int, Any]) -> Dict[int, Any]:
    """여러 응답 블록을 합치는 헬퍼."""
    merged: Dict[int, Any] = {}
    for b in blocks:
        merged.update(b)
    return merged
