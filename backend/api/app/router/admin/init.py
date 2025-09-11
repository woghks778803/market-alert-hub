from fastapi import APIRouter, Depends, HTTPException, status


router = APIRouter()


# TODO: RBAC 미들웨어 연결
@router.get("/healthz")
def healthz_admin():
    return {"status": "ok!", "scope": "admin"}
