from fastapi import APIRouter
router = APIRouter(tags=["health"])  # prefix는 여기선 안 줌(아래에서 묶음 prefix로)

@router.get("/healthz", summary="헬스체크")
def healthz():
    return {"status": "ok"}