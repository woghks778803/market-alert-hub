from fastapi import APIRouter
router = APIRouter() 

@router.get("/healthz", summary="헬스체크")
def healthz():
    return {"status": "ok"}