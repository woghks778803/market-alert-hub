# app/api/router/private/alerts.py   # (폴더는 네 구조에 맞춰 public/ or private/)
from fastapi import APIRouter, Depends, Security, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.service import ServiceFactory
import app.api.schema as pschema
import app.api.openapi as popenapi

router = APIRouter(
    prefix="/alerts",
    tags=["alerts"],
    responses=popenapi.combine(popenapi.ERR_401, popenapi.ERR_500),
)

def get_services(db: Session = Depends(get_db)) -> ServiceFactory:
    return ServiceFactory(db)

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=pschema.alert.AlertRead,
    summary="알림 생성",
    responses=popenapi.combine(
        popenapi.ERR_401,
        popenapi.ERR_400,
    ),
)
def create_alert(
    payload: pschema.alert.AlertCreate,
    svcs: ServiceFactory = Depends(get_services),
    user = Security(get_current_user),   # 로그인 필요 (user.id 사용)
):
    return svcs.alerts().create(user.id, payload)

@router.get(
    "",
    response_model=list[pschema.alert.AlertRead],
    summary="내 알림 목록",
)
def list_alerts(
    svcs: ServiceFactory = Depends(get_services),
    user = Security(get_current_user),
):
    return svcs.alerts().list(user.id)

@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="알림 삭제",
)
def delete_alert(
    alert_id: int,
    svcs: ServiceFactory = Depends(get_services),
    user = Security(get_current_user),
):
    svcs.alerts().delete(user.id, alert_id)
    return
