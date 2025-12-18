import logging
from typing import Any, Mapping

from app.deps import get_services
from app.service.factory import ServiceFactory
from app.domain import UserDTO, EmailDTO, ValidationAppError

logger = logging.getLogger(__name__)

# ---- helpers --------------------------------------------------------------

def _as_list(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        return [v]
    # Sequence[str] 같은 형태도 허용
    try:
        return list(v)
    except Exception:
        return [str(v)]

def _dispatch_with_svcs(svcs: ServiceFactory, *, event_type: str, payload: Mapping[str, Any]):
    """
    OutboxService가 호출하는 실제 디스패처.
    - channel이 email일 때 EmailService로 라우팅
    - event_type에 따라 EmailService 메서드 매핑
    - 잘못된 payload면 예외 발생 → OutboxService가 재시도/FAILED 처리
    """
    logger.info("dispatch event_type=%s channel=%s keys=%s",
                event_type, list(payload.keys()))
    
    # 공통 필드
    user_id = payload.get("user_id")
    
    if not user_id:
        raise ValidationAppError("payload 'user_id' is required", target="payload.user_id")

    # --- 라우팅 ---
    if event_type in ("EMAIL_AUTH_CODE"):
        user_email_info = svcs.users.get_user_email_info(user_id=user_id)

        email_verification_id = payload.get("email_verification_id")
        if not email_verification_id:
            raise ValidationAppError("payload 'email_verification_id' is required", target="payload.email_verification_id")
        
        verify_token = payload.get("verify_token")
        if not verify_token:
            raise ValidationAppError("payload 'verify_token' is required", target="payload.verify_token")

        ses_result = svcs.emails.send_verify(
            user=user_email_info,
            verify_token=verify_token,
        )

        svcs.users.set_email_verification_sent(
            email_verification_id=email_verification_id
        )

        return ses_result


    # if event_type in ("user_signed_up", "user_welcome"):
    #     user_name = (payload.get("user_name")
    #                  or payload.get("name")
    #                  or "")
    #     dashboard_link = payload.get("dashboard_link", "")
    #     email_svc.send_welcome(
    #         to=to,
    #         user_name=user_name,
    #         dashboard_link=dashboard_link,
    #     )
    #     return


    # if event_type in ("alert_triggered", "price_alert"):
    #     email_svc.send_alert(
    #         to=to,
    #         user_name=payload.get("user_name", ""),
    #         exchange=payload.get("exchange", ""),
    #         symbol=payload.get("symbol", ""),
    #         condition=payload.get("condition", ""),
    #         current_price=payload.get("current_price", ""),
    #         currency=payload.get("currency", ""),
    #         alert_link=payload.get("alert_link", ""),
    #         settings_link=payload.get("settings_link", ""),
    #     )
    #     return

    # 알 수 없는 이벤트
    raise ValidationAppError(f"unsupported event_type={event_type}", target="event_type")

# ---- job entrypoint -------------------------------------------------------

def deliver_outbox_event(outbox_id: int) -> None:
    """
    RQ가 실행하는 잡 엔트리.
    OutboxService가 트랜잭션/상태 전이를 담당하고,
    실제 발송은 _dispatch_with_svcs가 EmailService로 위임한다.
    """
    svcs: ServiceFactory = get_services()

    svcs.outboxs.deliver_outbox(
        outbox_id=outbox_id,
        dispatch_fn=lambda event_type, payload: _dispatch_with_svcs(
            svcs, event_type=event_type, payload=payload
        ),
    )
