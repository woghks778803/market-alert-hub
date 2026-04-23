import asyncio
import json
from typing import Any
from decimal import Decimal

from app.core.constants import (
    AlertStatus, 
    AlertScope, 
    AlertFormType, 
    IndicatorType,
    DirectionType, 
    CandleInterval, 
    ALERTS, 
    BUCKET, 
    SNAP
)

async def run_alert_price_loop(
    *,
    stop_event: asyncio.Event,
    ctx: Any,
) -> None:
    """
    1s candle pub/sub을 소비해서 가격 알림을 평가한다.

    역할:
    - RedisCandleStore의 1s candle publish 구독
    - candle payload 수신
    - price alert bucket 조회
    - alert snapshot 조회
    - 가격 조건 평가
    - alert event 적재
    """
    candle_store = ctx.svcs.candle_store
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
            
            # await evaluate_price_candle(
            #     ctx=ctx,
            #     candle=candle,
            #     prev_close=prev_close,
            #     price_close=price_close
            # )

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
    ) -> None:
        """
        1s candle 기준 가격 알림 평가

        현재 처리:
        - 가격 도달: cross + both + threshold
        - 가격 이상: single + up + threshold
        - 가격 이하: single + down + threshold
        - 가격 돌파: cross + up + threshold
        - 가격 이탈: cross + down + threshold
        """

        exchange_code = candle.get("exchange_code")
        exchange_symbol = candle.get("exchange_symbol")

        if not exchange_code or not exchange_symbol:
            return

        # 첫 수신은 prev가 없어서 cross 평가 불가.
        # single은 평가할 수 있지만, 시작하자마자 기존 조건이 대량 발동될 수 있어서 일단 스킵 추천.
        if prev_close is None:
            return

        bucket_keys = build_price_eval_bucket_keys(
            exchange_code=str(exchange_code),
            exchange_symbol=str(exchange_symbol),
            prev_close=prev_close,
            price_close=price_close,
        )

        if not bucket_keys:
            return

        alert_ids = await ctx.svcs.alert_bucket.list_alert_id_many(
            bucket_keys=bucket_keys
        )

        if not alert_ids:
            return

        snapshots = await ctx.svcs.alert_snapshot.alert_mget(alert_ids)

        if not snapshots:
            return

        for alert in snapshots:
            if not _is_price_threshold_alert(alert):
                continue

            threshold = _get_decimal_param(alert, "threshold")
            if threshold is None:
                continue

            if not _is_same_market(
                alert=alert,
                exchange_code=str(exchange_code),
                exchange_symbol=str(exchange_symbol),
            ):
                continue

            triggered = _evaluate_price_threshold(
                alert=alert,
                prev_close=prev_close,
                price_close=price_close,
                threshold=threshold,
            )

            if not triggered:
                continue

            log.info(
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
                threshold,
            )

            # 다음 단계에서 여기서 Redis event 적재
            # await ctx.svcs.alert_event.event_add(...)


    def _is_price_threshold_alert(alert: dict[str, Any]) -> bool:
        return (
            alert.get("indicator") == IndicatorType.PRICE.value
            and alert.get("form_type") == AlertFormType.THRESHOLD.value
        )


    def _is_same_market(
        *,
        alert: dict[str, Any],
        exchange_code: str,
        exchange_symbol: str,
    ) -> bool:
        return (
            alert.get("exchange_code") == exchange_code
            and alert.get("exchange_symbol") == exchange_symbol
        )


    def _evaluate_price_threshold(
        *,
        alert: dict[str, Any],
        prev_close: Decimal,
        price_close: Decimal,
        threshold: Decimal,
    ) -> bool:
        scope = alert.get("scope")
        direction = alert.get("direction")

        if scope == AlertScope.SINGLE.value:
            if direction == DirectionType.UP.value:
                return price_close >= threshold

            if direction == DirectionType.DOWN.value:
                return price_close <= threshold

            if direction == DirectionType.REACH.value:
                return price_close == threshold

            return False

        if scope == AlertScope.CROSS.value:
            if direction == DirectionType.UP.value:
                return prev_close < threshold <= price_close

            if direction == DirectionType.DOWN.value:
                return prev_close > threshold >= price_close

            if direction == DirectionType.REACH.value:
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
            f"{base}:{AlertFormType.THRESHOLD.value}:{AlertScope.SINGLE.value}:{DirectionType.UP.value}"
        )
        keys.append(
            f"{base}:{AlertFormType.THRESHOLD.value}:{AlertScope.SINGLE.value}:{DirectionType.DOWN.value}"
        )

        # cross both = 가격 도달
        keys.append(
            f"{base}:{AlertFormType.THRESHOLD.value}:{AlertScope.CROSS.value}:{DirectionType.REACH.value}"
        )

        # 방향성 cross
        if price_close > prev_close:
            keys.append(
                f"{base}:{AlertFormType.THRESHOLD.value}:{AlertScope.CROSS.value}:{DirectionType.UP.value}"
            )
        elif price_close < prev_close:
            keys.append(
                f"{base}:{AlertFormType.THRESHOLD.value}:{AlertScope.CROSS.value}:{DirectionType.DOWN.value}"
            )

        return keys

