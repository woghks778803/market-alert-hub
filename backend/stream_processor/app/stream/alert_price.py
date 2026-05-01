import logging
import asyncio
import json
from datetime import datetime
from typing import Any
from decimal import Decimal

from app.core.util.datetime import utcnow
from app.core.constants import (
    AlertStatus, 
    ConditionType, 
    AlertFormType, 
    IndicatorType,
    DirectionType, 
    CandleInterval, 
    ALERTS, 
    BUCKET, 
    SNAP
)

logger = logging.getLogger(__name__)

async def run_alert_price_loop(
    *,
    stop_event: asyncio.Event,
    ctx: Any,
) -> None:
    """
    1s candle pub/sub을 소비해서 가격 알림을 평가

    역할:
    - RedisCandleStore의 1s candle publish 구독
    - candle payload 수신
    - price alert bucket 조회
    - alert snapshot 조회
    - 가격 조건 평가
    - alert event 적재
    """
    alert_event = ctx.svcs.alert_event
    candle_store = ctx.svcs.candle_store
    cooldown = ctx.svcs.cooldown

    pubsub = await candle_store.subscribe(CandleInterval.SEC_1.value)

    last_close_by_symbol: dict[str, Decimal] = {}

    try:
        while not stop_event.is_set():
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )

            if not message:
                continue

            if message.get("type") != "pmessage":
                continue

            payload_raw = message.get("data")
            if not payload_raw:
                continue

            if isinstance(payload_raw, bytes):
                payload_raw = payload_raw.decode()

            try:
                candle = json.loads(payload_raw)
            except json.JSONDecodeError:
                continue

            if not isinstance(candle, dict):
                continue

            exchange_code = candle.get("exchange_code")
            exchange_symbol = candle.get("exchange_symbol")
            close_raw = candle.get("close")

            if not exchange_code or not exchange_symbol or close_raw is None:
                continue

            symbol_key = f"{exchange_code}:{exchange_symbol}"
            prev_close = last_close_by_symbol.get(symbol_key)
            price_close = Decimal(str(close_raw))
            
            events = await evaluate_price_candle(
                ctx=ctx,
                candle=candle,
                prev_close=prev_close,
                price_close=price_close
            )

            for event in events:
                alert_id = int(event["alert_id"])
                throttle_seconds = int(event.get("throttle_seconds") or 0)

                if throttle_seconds > 0:
                    acquired = await cooldown.acquire_alert_price(
                        alert_id=alert_id,
                        ttl_sec=throttle_seconds,
                    )

                    if not acquired:
                        continue

                await ctx.svcs.alert_event.add_event(event)

            last_close_by_symbol[symbol_key] = price_close

    except asyncio.CancelledError:
        raise

    finally:
        await pubsub.close()


async def evaluate_price_candle(
    *,
    ctx: Any,
    candle: dict[str, Any],
    prev_close: Decimal | None,
    price_close: Decimal,
) -> list[dict[str, Any]]:
    """
    1s candle 기준 가격 알림 평가

    현재 처리:
    - 가격 도달: cross + both + threshold
    - 가격 이상: single + up + threshold
    - 가격 이하: single + down + threshold
    - 가격 돌파: cross + up + threshold
    - 가격 이탈: cross + down + threshold
    """

    events: list[dict[str, Any]] = []
    exchange_code = candle.get("exchange_code")
    exchange_symbol = candle.get("exchange_symbol")

    if not exchange_code or not exchange_symbol:
        return events

    # 첫 수신은 prev가 없어서 cross 평가 불가.
    # single은 평가할 수 있지만, 시작하자마자 기존 조건이 대량 발동될 수 있어서 일단 스킵
    if prev_close is None:
        return events

    bucket_keys = build_price_eval_bucket_keys(
        exchange_code=str(exchange_code),
        exchange_symbol=str(exchange_symbol),
        prev_close=prev_close,
        price_close=price_close,
    )

    if not bucket_keys:
        return events

    alert_ids = await ctx.svcs.alert_bucket.list_alert_ids(
        bucket_keys=bucket_keys
    )

    # logger.info("alert_ids", alert_ids)
    if not alert_ids:
        return events

    snapshots = await ctx.svcs.alert_snapshot.mget_alert(alert_ids)

    if not snapshots:
        return events
        
    # logger.info("snapshots", snapshots)
    for alert in snapshots:
        if not (
            alert.get("indicator") == IndicatorType.PRICE.value
            and alert.get("form_type") == AlertFormType.THRESHOLD.value
        ):
            continue

        threshold = _get_decimal_param(alert, "threshold")
        if threshold is None:
            continue

        if not (
            alert.get("exchange_code") == exchange_code
            and alert.get("exchange_symbol") == exchange_symbol
        ):
            continue

        triggered = _evaluate_price_threshold(
            alert=alert,
            prev_close=prev_close,
            price_close=price_close,
            threshold=threshold,
        )

        now = utcnow()
        if not triggered:
            continue

        if not _can_fire_alert(alert=alert, now=now):
            continue

        throttle_seconds = alert.get("throttle_seconds")
        if throttle_seconds is None:
            continue
        
        throttle_seconds = int(throttle_seconds)
        if throttle_seconds <= 0:
            continue

        logger.info(
            "[ALERT_TRIGGERED] alert_id=%s type=%s scope=%s direction=%s "
            "exchange=%s symbol=%s prev=%s current=%s threshold=%s",
            alert.get("alert_id"),
            alert.get("alert_type_code"),
            alert.get("scope"),
            alert.get("direction"),
            exchange_code,
            exchange_symbol,
            prev_close,
            price_close,
            threshold
        )

        # print("alert", alert)

        event = _make_price_alert_event(
            alert=alert,
            candle=candle,
            prev_close=prev_close,
            price_close=price_close,
            threshold=threshold,
            detected_at=now,
            throttle_seconds=throttle_seconds,
        )

        events.append(event)

    # logger.info("result events: %s", events)
    return events

def _make_price_alert_event(
    *,
    alert: dict[str, Any],
    candle: dict[str, Any],
    prev_close: Decimal | None,
    price_close: Decimal,
    threshold: Decimal,
    detected_at: datetime,
    throttle_seconds: int,
) -> dict[str, Any]:
    alert_id = int(alert["alert_id"])
    exchange_code = str(alert["exchange_code"])
    exchange_symbol = str(alert["exchange_symbol"])
    bucket_key = str(alert["bucket_key"])

    detected_ts = int(detected_at.timestamp())
    bucket_ts = detected_ts - (detected_ts % throttle_seconds)

    return {
        "alert_id": alert_id,
        "exchange_instrument_id": alert.get("exchange_instrument_id"),
        "detected_at": detected_at,
        "trigger_value": price_close,
        "dedup_key": f"{bucket_key}:{alert_id}:{bucket_ts}",
        "bucket_key": bucket_key,
        "context": {
            # "source": "",
            "alert_name": alert.get("alert_name"),
            "exchange_code": exchange_code,
            "exchange_symbol": exchange_symbol,
            "alert_type_id": alert.get("alert_type_id"),
            "alert_type_code": alert.get("alert_type_code"),
            "alert_type_name": alert.get("alert_type_name"),
            "params": alert.get("params"),
            "param_schema": alert.get("param_schema"),
            "scope": alert.get("scope"),
            "indicator": alert.get("indicator"),
            "direction": alert.get("direction"),
            "form_type": alert.get("form_type"),
            "threshold": str(threshold), # 제거 대상
            "prev_close": str(prev_close) if prev_close is not None else None,
            "price_close": str(price_close),
            "candle": candle,
        },
        "throttle_seconds": throttle_seconds,
        "is_once": alert.get("is_once"),
    }

def _can_fire_alert(
    *,
    alert: dict[str, Any],
    now: datetime,
) -> bool:
    valid_from = alert.get("valid_from")
    valid_to = alert.get("valid_to")
    last_fired_at = alert.get("last_fired_at")

    if valid_from is not None and now < valid_from:
        return False

    if valid_to is not None and now > valid_to:
        return False

    if alert.get("is_once") is True and last_fired_at is not None:
        return False

    return True

def _evaluate_price_threshold(
    *,
    alert: dict[str, Any],
    prev_close: Decimal,
    price_close: Decimal,
    threshold: Decimal,
) -> bool:
    scope = alert.get("scope")
    direction = alert.get("direction")

    if scope == ConditionType.SINGLE.value:
        if direction == DirectionType.UP.value:
            return price_close >= threshold

        if direction == DirectionType.DOWN.value:
            return price_close <= threshold

        if direction == DirectionType.BOTH.value:
            return price_close == threshold

        return False

    if scope == ConditionType.CROSS.value:
        if direction == DirectionType.UP.value:
            return prev_close < threshold <= price_close

        if direction == DirectionType.DOWN.value:
            return prev_close > threshold >= price_close

        if direction == DirectionType.BOTH.value:
            low = min(prev_close, price_close)
            high = max(prev_close, price_close)
            return low <= threshold <= high

        return False

    return False


def _get_decimal_param(alert: dict[str, Any], key: str) -> Decimal | None:
    params = alert.get("params")

    if not isinstance(params, dict):
        return None

    raw = params.get(key)

    if raw is None:
        return None

    try:
        return Decimal(str(raw))
    except (InvalidOperation, ValueError):
        return None


def build_price_eval_bucket_keys(
    *,
    exchange_code: str,
    exchange_symbol: str,
    prev_close: Decimal,
    price_close: Decimal,
) -> list[str]:
    keys: list[str] = []

    base = f"{IndicatorType.PRICE.value}:{exchange_code}:{exchange_symbol}"

    # single 조건은 현재 상태 조건이라 상승/하락과 무관하게 둘 다 후보로 본다.
    keys.append(
        f"{base}:{AlertFormType.THRESHOLD.value}:{ConditionType.SINGLE.value}:{DirectionType.UP.value}"
    )
    keys.append(
        f"{base}:{AlertFormType.THRESHOLD.value}:{ConditionType.SINGLE.value}:{DirectionType.DOWN.value}"
    )

    # cross both = 가격 도달
    keys.append(
        f"{base}:{AlertFormType.THRESHOLD.value}:{ConditionType.CROSS.value}:{DirectionType.BOTH.value}"
    )

    # 방향성 cross
    if price_close > prev_close:
        keys.append(
            f"{base}:{AlertFormType.THRESHOLD.value}:{ConditionType.CROSS.value}:{DirectionType.UP.value}"
        )
    elif price_close < prev_close:
        keys.append(
            f"{base}:{AlertFormType.THRESHOLD.value}:{ConditionType.CROSS.value}:{DirectionType.DOWN.value}"
        )

    return keys

