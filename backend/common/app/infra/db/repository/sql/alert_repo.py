from typing import Sequence, cast
from datetime import datetime
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.engine import CursorResult
from sqlalchemy import update, insert, select, and_, or_, asc, desc, func, case

from app.core.util.datetime import utcnow, get_days_ago
from app.core.constants import UserStatus, AlertStatus, AlertSort, AlertEventStatus, AlertDeliveryStatus
from app.domain import AlertDTO
from app.infra.db.model import (
    AlertModel, 
    AlertTypeModel, 
    AlertEventModel,
    AlertDeliveryModel, 
    ExchangeInstrumentModel, 
    ExchangeModel, 
    UserModel,
    UserChannelModel,
    ChannelProviderModel,
)
from app.infra.db.repository.protocol.sql.alert_repo import AlertRepo
from app.infra.db.utils import to_row_dict

a = AlertModel
at = AlertTypeModel
ae = AlertEventModel
ad = AlertDeliveryModel
e = ExchangeModel
ei = ExchangeInstrumentModel
u = UserModel
uc = UserChannelModel
cp = ChannelProviderModel

class SqlAlertRepo(AlertRepo):
    def __init__(self, db: DbSession) -> None:
        self._db = db

    def get_alert_summary(
        self,
        *,
        user_id: int,
        deleted_is_null: bool = True,
    ) -> AlertDTO.AlertSummary:
        stmt = (
            select(
                func.count(a.id).label("total_count"),
                func.coalesce(
                    func.sum(case((a.status == AlertStatus.ACTIVE, 1), else_=0)),
                    0
                ).label("active_count"),
                func.coalesce(
                    func.sum(case((a.status == AlertStatus.PAUSED, 1), else_=0)),
                    0
                ).label("paused_count"),
            )
            .select_from(u)
            .outerjoin(
                a,
                and_(
                    a.user_id == u.id,
                    a.status != AlertStatus.ARCHIVED,
                ),
            )
            .where(u.id == user_id)
            .group_by(u.id)
        )

        if deleted_is_null:
            stmt = stmt.where(a.deleted_at.is_(None))

        row = self._db.execute(stmt).mappings().one()
        return AlertDTO.AlertSummary(**row)

    def get_alert_cnt(
        self, 
        *, 
        user_id: int, 
        status: AlertStatus | None = None,
        archived_only: bool = False,
        deleted_is_null: bool = True,
    ) -> int:
        
        stmt = select(func.count(a.id)).where(
            a.user_id == user_id,
        )

        if archived_only:
            stmt = stmt.where(a.status == AlertStatus.ARCHIVED)
        elif status:
            stmt = stmt.where(a.status == status)
        else:
            stmt = stmt.where(a.status != AlertStatus.ARCHIVED)

        if deleted_is_null:
            stmt = stmt.where(a.deleted_at.is_(None))

        result = self._db.execute(stmt).scalar()

        return result if result else 0

    def get_by_id(
        self,
        alert_id: int,
        user_id: int,
        deleted_is_null: bool = True,
    ) -> AlertDTO.Alert | None:
        stmt = (
            select(a).where(
                a.id == alert_id,
                a.user_id == user_id,
            )
        )
        if deleted_is_null:
            stmt = stmt.where(a.deleted_at.is_(None))

        row = self._db.execute(stmt).scalar_one_or_none()

        return row.to_dto() if row else None

    def get_type_by_id(
        self,
        alert_type_id: int,
        is_active: bool, 
        deleted_is_null: bool = True,
    ) -> AlertDTO.AlertType | None:
        stmt = (
            select(at).where(
                at.id == alert_type_id,
                at.is_active.is_(is_active),
            )
        )
        if deleted_is_null:
            stmt = stmt.where(at.deleted_at.is_(None))

        row = self._db.execute(stmt).scalar_one_or_none()

        return row.to_dto() if row else None

    def get_alert_by_filter(
        self,
        *,
        user_id: int,
        alert_id: int,
        deleted_is_null: bool = True,
    ) -> AlertDTO.AlertSimple | None:

        exchange_instrument = (
            select(
                ei.id.label("ei_id"),
                ei.exchange_symbol.label("exchange_symbol"),
                ei.is_active.label("ei_is_active"),
                ei.exchange_id.label("exchange_id"),
            )
            .select_from(ei)
            .where(
                ei.deleted_at.is_(None),
            )
            .subquery()
        )

        exchange = (
            select(
                e.id.label("e_id"),
                e.code.label("exchange_code"),
                e.name.label("exchange_name"),
                e.is_active.label("e_is_active"),
            )
            .select_from(e)
            .where(
                e.deleted_at.is_(None),
            )
            .subquery()
        )

        stmt = (
            select(
                a.id.label("id"),
                a.alert_type_id.label("alert_type_id"),
                a.name.label("name"),
                a.status.label("status"),
                a.timezone.label("timezone"),
                a.params.label("params"),
                a.throttle_seconds.label("throttle_seconds"),
                a.is_once.label("is_once"),
                a.valid_from.label("valid_from"),
                a.valid_to.label("valid_to"),
                a.updated_at.label("updated_at"),

                exchange_instrument.c.ei_id.label("exchange_instrument_id"),
                exchange_instrument.c.exchange_symbol.label("exchange_symbol"),
                exchange_instrument.c.ei_is_active.label("ei_is_active"),

                exchange.c.exchange_code.label("exchange_code"),
                exchange.c.exchange_name.label("exchange_name"),
                exchange.c.e_is_active.label("e_is_active"),
            )
            .select_from(a)
            .join(
                exchange_instrument,
                exchange_instrument.c.ei_id == a.exchange_instrument_id,
            )
            .join(
                exchange,
                exchange.c.e_id == exchange_instrument.c.exchange_id,
            )
            .where(
                a.id == alert_id,
                a.user_id == user_id,
            )
        )

        if deleted_is_null:
            stmt = stmt.where(a.deleted_at.is_(None))

        row = self._db.execute(stmt).mappings().one_or_none()

        if row is None:
            return None

        return AlertDTO.AlertSimple(**row)

    def get_alert_snapshot_by_filter(
        self,
        *,
        alert_id: int,
        user_id: int | None = None,
        status: AlertStatus | None,
        archived_only: bool = False,
        deleted_is_null: bool = True,
    ) -> AlertDTO.AlertSnapshot | None:
        stmt = (
            select(
                a.id.label("alert_id"),
                a.name.label("alert_name"),
                a.user_id.label("user_id"),

                a.status.label("status"),

                a.alert_type_id.label("alert_type_id"),
                at.code.label("alert_type_code"),
                at.name.label("alert_type_name"),

                at.scope.label("scope"),
                at.indicator.label("indicator"),
                at.direction.label("direction"),
                at.form_type.label("form_type"),

                a.exchange_instrument_id.label("exchange_instrument_id"),
                e.code.label("exchange_code"),
                e.name.label("exchange_name"),
                ei.exchange_symbol.label("exchange_symbol"),

                a.params.label("params"),
                at.param_schema.label("param_schema"),

                a.throttle_seconds.label("throttle_seconds"),
                a.valid_from.label("valid_from"),
                a.valid_to.label("valid_to"),
                a.is_once.label("is_once"),
                a.last_fired_at.label("last_fired_at"),
            )
            .select_from(a)
            .join(u, u.id == a.user_id)
            .join(at, at.id == a.alert_type_id)
            .join(ei, ei.id == a.exchange_instrument_id)
            .join(e, e.id == ei.exchange_id)
            .where(
                a.id == alert_id,
                
                u.status == UserStatus.ACTIVE, 
                u.deleted_at.is_(None), 

                at.is_active.is_(True),
                at.deleted_at.is_(None),
                e.is_active.is_(True),
                e.deleted_at.is_(None),
                ei.is_active.is_(True),
                ei.deleted_at.is_(None),
            )
        )

        if user_id is not None:
            stmt = stmt.where(a.user_id == user_id)

        if archived_only:
            stmt = stmt.where(a.status == AlertStatus.ARCHIVED)
        elif status:
            stmt = stmt.where(a.status == status)
        else:
            stmt = stmt.where(a.status != AlertStatus.ARCHIVED)

        if deleted_is_null:
            stmt = stmt.where(a.deleted_at.is_(None))

        row = self._db.execute(stmt).mappings().one_or_none()

        return AlertDTO.AlertSnapshot(**row) if row else None

    def list_alert_type_by_filter(
        self, 
        *, 
        search: str | None, 
        is_active: bool, 
        deleted_is_null: bool = True, 
        asc_order: bool = False,
        limit: int, 
        offset: int
    ) -> Sequence[AlertDTO.AlertType]: 
        stmt = (
            select(at)
            .where(
                at.is_active.is_(is_active)
            )
            .limit(limit)
            .offset(offset)
        )

        if deleted_is_null:
            stmt = stmt.where(at.deleted_at.is_(None))

        if search:
            stmt = stmt.where(
                or_(
                    at.name.ilike(f"%{search}%"),
                )
            )

        if asc_order:
            stmt = stmt.order_by(at.sort_order.asc())
        else:
            stmt = stmt.order_by(at.sort_order.desc())

        rows = self._db.execute(stmt).scalars().all()
        return [row.to_dto() for row in rows]
    
    

    def list_alert_event_by_filter(
        self,
        *,
        user_id: int,
        status: AlertEventStatus | None,
        cursor: AlertDTO.AlertLogListCursor | None,
        limit: int,
    ) -> Sequence[AlertDTO.AlertEvent]:
        stmt = (
            select(ae)
            .select_from(ae)
            .join(a, a.id == ae.alert_id)
            .join(u, u.id == a.user_id)
            .where(
                u.id == user_id,
                ae.detected_at >= get_days_ago(utcnow(), 7),
            )
            .order_by(ae.detected_at.desc(), ae.id.desc())
            .limit(limit)
        )

        stmt = self.apply_alert_event_cursor(
            stmt,
            cursor=cursor,
            alert_event=ae
        )

        if status:
            stmt = stmt.where(ae.status == status)
        else:
            # TODO: 현재 사용처가 적기때문에 옵션 분기는 추후에
            stmt = stmt.where(
                ae.status != AlertEventStatus.PENDING,
                ae.status != AlertEventStatus.QUEUED,
            )

        rows = self._db.execute(stmt).scalars().all()
        return [row.to_dto() for row in rows]

    def list_alert_event_by_status(
        self,
        *,
        status: AlertEventStatus | None,
        limit: int, 
        offset: int
    ) -> Sequence[AlertDTO.AlertEvent]:
        stmt = (
            select(ae)
            .select_from(ae)
            .join(a, a.id == ae.alert_id)
            .order_by(ae.detected_at.asc(), ae.id.asc())
            .limit(limit)
            .offset(offset)
        )

        if status:
            stmt = stmt.where(ae.status == status)

        rows = self._db.execute(stmt).scalars().all()
        return [row.to_dto() for row in rows]

    def list_alert_event_from_ids(
        self,
        *,
        alert_event_ids: Sequence[int],
        status: AlertEventStatus,
    ) -> Sequence[AlertDTO.AlertEvent]:

        stmt = (
            select(ae)
            .where(
                ae.id.in_(alert_event_ids),
                ae.status == status,
            )
            .order_by(ae.id.asc())
        )

        rows = self._db.execute(stmt).scalars().all()
        return [row.to_dto() for row in rows]

    def list_alert_delivery_from_ids(
        self,
        *,
        alert_event_ids: Sequence[int],
        status: AlertDeliveryStatus,
    ) -> Sequence[AlertDTO.AlertDelivery]:
        stmt = (
            select(ad)
            .where(
                ad.alert_event_id.in_(alert_event_ids),
                ad.status == status,
            )
            .order_by(ad.id.asc())
        )

        rows = self._db.execute(stmt).scalars().all()
        return [row.to_dto() for row in rows]

    def list_alert_delivery_targets(
        self,
        *,
        alert_delivery_ids: Sequence[int],
        status: AlertDeliveryStatus,
    ) -> Sequence[AlertDTO.AlertDeliveryTarget]:
        stmt = (
            select(
                ad.id.label("alert_delivery_id"),
                ad.alert_event_id.label("alert_event_id"),
                ad.user_channel_id.label("user_channel_id"),
                ad.status.label("delivery_status"),

                ae.alert_id.label("alert_id"),
                ae.exchange_instrument_id.label("exchange_instrument_id"),
                ae.trigger_value.label("trigger_value"),
                ae.context.label("context"),
                ae.detected_at.label("detected_at"),

                uc.channel_provider_id.label("channel_provider_id"),
                uc.address.label("address"),
                uc.config.label("channel_config"),

                cp.code.label("channel_provider_code"),
            )
            .select_from(ad)
            .join(ae, ae.id == ad.alert_event_id)
            .join(uc, uc.id == ad.user_channel_id)
            .join(cp, cp.id == uc.channel_provider_id)
            .where(
                ad.id.in_(alert_delivery_ids),
                ad.status == status,
                uc.is_active.is_(True),
                uc.deleted_at.is_(None),
                uc.address.is_not(None),
                cp.is_active.is_(True),
            )
            .order_by(ad.id.asc())
        )

        rows = self._db.execute(stmt).mappings().all()
        return [AlertDTO.AlertDeliveryTarget(**row) for row in rows]

    def list_user_channel_by_filter(
        self,
        *,
        alert_event_ids: Sequence[int],
        status: AlertEventStatus,
    ) -> Sequence[AlertDTO.AlertEventChannel]:
        stmt = (
            select(
                ae.id.label("alert_event_id"),
                ae.alert_id.label("alert_id"),
                a.user_id.label("user_id"),
                uc.id.label("user_channel_id"),
                uc.channel_provider_id.label("channel_provider_id"),
                cp.code.label("channel_provider_code"),
                uc.address.label("address"),
                uc.config.label("config"),
            )
            .select_from(ae)
            .join(a, a.id == ae.alert_id)
            .join(uc, uc.user_id == a.user_id)
            .join(cp, cp.id == uc.channel_provider_id)
            .where(
                ae.id.in_(alert_event_ids),
                ae.status == status,

                uc.is_active.is_(True),
                uc.deleted_at.is_(None),
                uc.address.is_not(None),
                cp.is_active.is_(True),

            )
            .order_by(ae.id.asc(), uc.id.asc())
        )

        rows = self._db.execute(stmt).mappings().all()
        return [AlertDTO.AlertEventChannel(**row) for row in rows]

    def list_alert_snapshot_by_status(
        self,
        *,
        status: AlertStatus | None,
        archived_only: bool = False,
        deleted_is_null: bool = True, 
        asc_order: bool = False,
        limit: int, 
        offset: int
    ) -> Sequence[AlertDTO.AlertSnapshot]:
        stmt = (
            select(
                a.id.label("alert_id"),
                a.name.label("alert_name"),
                a.user_id.label("user_id"),
                a.status.label("status"),

                a.alert_type_id.label("alert_type_id"),
                at.code.label("alert_type_code"),
                at.name.label("alert_type_name"),

                at.scope.label("scope"),
                at.indicator.label("indicator"),
                at.direction.label("direction"),
                at.form_type.label("form_type"),

                a.exchange_instrument_id.label("exchange_instrument_id"),
                e.code.label("exchange_code"),
                e.name.label("exchange_name"),
                ei.exchange_symbol.label("exchange_symbol"),

                a.params.label("params"),
                at.param_schema.label("param_schema"),

                a.throttle_seconds.label("throttle_seconds"),
                a.valid_from.label("valid_from"),
                a.valid_to.label("valid_to"),
                a.is_once.label("is_once"),
                a.last_fired_at.label("last_fired_at"),
            )
            .select_from(a)
            .join(u, u.id == a.user_id)
            .join(at, at.id == a.alert_type_id)
            .join(ei, ei.id == a.exchange_instrument_id)
            .join(e, e.id == ei.exchange_id)
            .limit(limit)
            .offset(offset)
        )

        if archived_only:
            stmt = stmt.where(a.status == AlertStatus.ARCHIVED)
        elif status:
            stmt = stmt.where(a.status == status)
        else:
            stmt = stmt.where(a.status != AlertStatus.ARCHIVED)

        if deleted_is_null:
            stmt = stmt.where(a.deleted_at.is_(None))

        # TODO: 현재 사용처 제한으로 고정
        stmt = stmt.where(
            u.status == UserStatus.ACTIVE, 
            u.deleted_at.is_(None), 

            at.is_active.is_(True),
            at.deleted_at.is_(None),
            e.is_active.is_(True),
            e.deleted_at.is_(None),
            ei.is_active.is_(True),
            ei.deleted_at.is_(None),
        )

        if asc_order:
            stmt = stmt.order_by(a.id.asc())
        else:
            stmt = stmt.order_by(a.id.desc())

        rows = self._db.execute(stmt).mappings().all()
        return [
            AlertDTO.AlertSnapshot(**row)
            for row in rows
        ]

    def list_alert_by_filter(
        self,
        *,
        user_id: int,
        status: AlertStatus | None,
        sort: AlertSort | None,
        cursor: AlertDTO.AlertListCursor | None,
        limit: int,
        archived_only: bool = False,
        deleted_is_null: bool = True,
    ) -> Sequence[AlertDTO.AlertSimple]:
        
        exchange_instrument = (
            select(
                ei.id.label("ei_id"),
                ei.exchange_symbol.label("exchange_symbol"),
                ei.is_active.label("ei_is_active"),
                ei.exchange_id.label("exchange_id"),
            )
            .select_from(ei)
            .where(
                # is_active는 false도 허용(사용자 화면에서 구분)
                ei.deleted_at.is_(None),
            )
            .subquery()
        )

        exchange = (
            select(
                e.id.label("e_id"),
                e.code.label("exchange_code"),
                e.name.label("exchange_name"),
                e.is_active.label("e_is_active"),
            )
            .select_from(e)
            .where(
                e.deleted_at.is_(None),
            )
            .subquery()
        )

        stmt = (
            select(
                a.id.label("id"),
                a.alert_type_id.label("alert_type_id"),
                a.name.label("name"),
                a.status.label("status"),
                a.timezone.label("timezone"),

                a.params.label("params"),
                a.throttle_seconds.label("throttle_seconds"),
                a.is_once.label("is_once"),
                a.valid_from.label("valid_from"),
                a.valid_to.label("valid_to"),
                a.created_at.label("created_at"),
                a.updated_at.label("updated_at"),

                exchange_instrument.c.ei_id.label("exchange_instrument_id"),
                exchange_instrument.c.exchange_symbol.label("exchange_symbol"),
                exchange_instrument.c.ei_is_active.label("ei_is_active"),

                exchange.c.exchange_code.label("exchange_code"),
                exchange.c.exchange_name.label("exchange_name"),
                exchange.c.e_is_active.label("e_is_active"),
            )
            .select_from(a)
            .join(
                exchange_instrument,
                and_(
                    exchange_instrument.c.ei_id == a.exchange_instrument_id,
                ),
            )
            .join(
                exchange,
                and_(
                    exchange.c.e_id == exchange_instrument.c.exchange_id,
                ),
            )
            .where(
                a.user_id == user_id,
            )
            .limit(limit)
        )

        if deleted_is_null:
            stmt = stmt.where(a.deleted_at.is_(None))

        if archived_only:
            stmt = stmt.where(a.status == AlertStatus.ARCHIVED)
        elif status:
            stmt = stmt.where(a.status == status)
        else:
            stmt = stmt.where(a.status != AlertStatus.ARCHIVED)
        
        stmt = self.apply_alert_cursor(
            stmt,
            cursor=cursor,
            sort=sort, 
            alert=a, 
            exchange_instrument=exchange_instrument
        )
        
        stmt = self.apply_alert_sort(
            stmt, 
            sort=sort, 
            alert=a, 
            exchange_instrument=exchange_instrument
        )

        rows = self._db.execute(stmt)
        return [
            AlertDTO.AlertSimple(**row)
            for row in rows.mappings().all() 
        ]


    def add_alert(self, row: AlertDTO.AlertCreate) -> AlertDTO.Alert:
        alert = a.from_create_dto(row)
        self._db.add(alert)
        self._db.flush()
        return alert.to_dto()

    def add_alert_deliveries(
        self,
        alert_deliveries: Sequence[AlertDTO.AlertDeliveryCreate],
        *,
        chunk_size: int = 1000,
    ) -> int:
        total = 0

        if not alert_deliveries:
            return total

        for i in range(0, len(alert_deliveries), chunk_size):
            chunk = alert_deliveries[i : i + chunk_size]
            values = [
                to_row_dict(delivery)
                for delivery in alert_deliveries
            ]

            stmt = insert(ad).values(values)

            result = cast(CursorResult, self._db.execute(stmt))

            total += int(result.rowcount or 0)

        return total

    
    def update_alert(
        self,
        row: AlertDTO.Alert,
        deleted_is_null: bool = True,
    ) -> None:
        stmt = (
            update(a)
            .where(
                a.id == row.id,
                a.user_id == row.user_id,
            )
            .values(
                alert_type_id=row.alert_type_id,
                exchange_instrument_id=row.exchange_instrument_id,
                name=row.name,
                status=row.status,
                timezone=row.timezone,

                params=row.params,

                is_once=row.is_once,
                throttle_seconds=row.throttle_seconds,
                
                valid_from=row.valid_from,
                valid_to=row.valid_to,
                updated_at=row.updated_at,
            )
        )

        if deleted_is_null:
            stmt = stmt.where(a.deleted_at.is_(None))

        self._db.execute(stmt)

    def update_alert_status(
        self,
        alert_id: int,
        user_id: int,
        status: AlertStatus,
        deleted_is_null: bool = True,
    ) -> None:
        stmt = (
            update(a)
            .where(
                a.id == alert_id,
                a.user_id == user_id,
            )
            .values(status=status)
        )

        if deleted_is_null:
            stmt = stmt.where(a.deleted_at.is_(None))
            
        self._db.execute(stmt)

    def update_alert_events_by_status(
        self,
        *,
        alert_event_ids: Sequence[int],
        from_status: AlertEventStatus,
        to_status: AlertEventStatus,
    ) -> None:
        stmt = (
            update(ae)
            .where(
                ae.id.in_(alert_event_ids),
                ae.status == from_status,
            )
            .values(
                status=to_status,
            )
        )

        self._db.execute(stmt)


    def update_alert_deliveries_status(
        self,
        *,
        send_results: Sequence[AlertDTO.AlertDeliverySendResult],
        from_status: AlertDeliveryStatus,
        to_status: AlertDeliveryStatus,
        sent_at: datetime | None = None,
    ) -> int:
        total = 0
        if not send_results:
            return total
        
        for result in send_results:
            values = {
                "status": to_status,
                "response_code": result.response_code,
                "response_body": result.response_body,
            }

            if sent_at is not None:
                values["sent_at"] = sent_at

            stmt = (
                update(ad)
                .where(
                    ad.id == result.alert_delivery_id,
                    ad.status == from_status,
                )
                .values(**values)
            )

            result = cast(CursorResult, self._db.execute(stmt))
            total += int(result.rowcount or 0)

        return total


    def delete_alert(
        self,
        alert_id: int,
        user_id: int,
        deleted_at: datetime,
        deleted_is_null: bool = True,
    ) -> None:
        stmt = (
            update(a)
            .where(
                a.id == alert_id,
                a.user_id == user_id,
            )
            .values(deleted_at=deleted_at)
        )
        
        if deleted_is_null:
            stmt = stmt.where(a.deleted_at.is_(None))

        self._db.execute(stmt)
        

    def apply_alert_cursor(
        self, stmt, *, sort, cursor, alert, exchange_instrument
    ):
        if cursor is None:
            return stmt

        cursor_id = cursor.alert_id

        if sort == AlertSort.RECENT_UPDATED:
            return stmt.where(
                or_(
                    alert.updated_at < cursor.updated_at,
                    and_(
                        alert.updated_at == cursor.updated_at,
                        alert.id < cursor_id,
                    ),
                )
            )

        if sort == AlertSort.RECENT_CREATED:
            return stmt.where(
                or_(
                    alert.created_at < cursor.created_at,
                    and_(
                        alert.created_at == cursor.created_at,
                        alert.id < cursor_id,
                    ),
                )
            )

        if sort == AlertSort.MARKET_ASC:
            return stmt.where(
                or_(
                    exchange_instrument.c.exchange_symbol > cursor.exchange_symbol,
                    and_(
                        exchange_instrument.c.exchange_symbol == cursor.exchange_symbol,
                        alert.id < cursor_id,
                    ),
                )
            )

        if sort == AlertSort.STATUS:
            return stmt.where(
                or_(
                    alert.status > cursor.status,
                    and_(
                        alert.status == cursor.status,
                        alert.updated_at < cursor.updated_at,
                    ),
                    and_(
                        alert.status == cursor.status,
                        alert.updated_at == cursor.updated_at,
                        alert.id < cursor_id,
                    ),
                )
            )

        return stmt.where(
            or_(
                alert.updated_at < cursor.updated_at,
                and_(
                    alert.updated_at == cursor.updated_at,
                    alert.id < cursor_id,
                ),
            )
        )
    
    def apply_alert_sort(
        self, stmt, *, sort, alert, exchange_instrument
    ):
        if sort == AlertSort.RECENT_CREATED:
            return stmt.order_by(
                alert.created_at.desc(),
                alert.id.desc(),
            )

        if sort == AlertSort.MARKET_ASC:
            return stmt.order_by(
                exchange_instrument.c.exchange_symbol.asc(),
                alert.id.desc(),
            )

        if sort == AlertSort.STATUS:
            return stmt.order_by(
                alert.status.asc(),
                alert.updated_at.desc(),
                alert.id.desc(),
            )

        return stmt.order_by(
            alert.updated_at.desc(),
            alert.id.desc(),
        )


    def apply_alert_event_cursor(self, stmt, *, cursor, alert_event):
        if cursor is None:
            return stmt

        cursor_id = cursor.alert_event_id

        return stmt.where(
            or_(
                alert_event.detected_at < cursor.cursor_at,
                and_(
                    alert_event.detected_at == cursor.cursor_at,
                    alert_event.id < cursor_id,
                ),
            )
        )
