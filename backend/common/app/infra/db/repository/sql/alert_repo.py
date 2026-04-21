from typing import Sequence
from datetime import datetime
from sqlalchemy.orm import Session as DbSession
from sqlalchemy import update, insert, select, and_, or_, asc, desc, func, case
from app.core.constants import AlertStatus, AlertSort
from app.domain import AlertDTO
from app.infra.db.model import AlertModel, AlertTypeModel, ExchangeInstrumentModel, ExchangeModel, UserModel
from app.infra.db.repository.protocol.alert_repo import AlertRepo

a = AlertModel
at = AlertTypeModel
e = ExchangeModel
ei = ExchangeInstrumentModel
u = UserModel

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
    ) -> int | None:
        
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

        return self._db.execute(stmt).scalar()

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
                a.timeframe.label("timeframe"),
                a.period.label("period"),
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

    def get_alert_snapshot_by_id(
        self,
        *,
        alert_id: int,
        user_id: int | None = None,
        deleted_is_null: bool = True,
    ) -> AlertDTO.AlertSnapshot | None:
        stmt = (
            select(
                a.id.label("alert_id"),
                a.user_id.label("user_id"),
                a.status.label("status"),

                a.alert_type_id.label("alert_type_id"),
                at.code.label("alert_type_code"),
                at.scope.label("scope"),
                at.indicator.label("indicator"),
                at.direction.label("direction"),
                at.form_type.label("form_type"),

                a.exchange_instrument_id.label("exchange_instrument_id"),
                e.code.label("exchange_code"),
                ei.exchange_symbol.label("exchange_symbol"),

                a.timeframe.label("timeframe"),
                a.period.label("period"),
                a.params.label("params"),

                a.throttle_seconds.label("throttle_seconds"),
                a.valid_from.label("valid_from"),
                a.valid_to.label("valid_to"),
                a.is_once.label("is_once"),
                a.last_fired_at.label("last_fired_at"),
            )
            .select_from(a)
            .join(at, at.id == a.alert_type_id)
            .join(ei, ei.id == a.exchange_instrument_id)
            .join(e, e.id == ei.exchange_id)
            .where(
                a.id == alert_id,
                
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

        if deleted_is_null:
            stmt = stmt.where(a.deleted_at.is_(None))

        row = self._db.execute(stmt).mappings().one_or_none()

        return AlertDTO.AlertSnapshot(**row) if row else None

    def list_type_by_filter(
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
    

    def list_alert_snapshot_by_status(
        self,
        *,
        status: AlertStatus | None,
        deleted_is_null: bool = True, 
        archived_only: bool = False,
        asc_order: bool = False,
        limit: int, 
        offset: int
    ) -> Sequence[AlertDTO.AlertSnapshot]:
        stmt = (
            select(
                a.id.label("alert_id"),
                a.user_id.label("user_id"),
                a.status.label("status"),

                a.alert_type_id.label("alert_type_id"),
                at.code.label("alert_type_code"),
                at.scope.label("scope"),
                at.indicator.label("indicator"),
                at.direction.label("direction"),
                at.form_type.label("form_type"),

                a.exchange_instrument_id.label("exchange_instrument_id"),
                e.code.label("exchange_code"),
                ei.exchange_symbol.label("exchange_symbol"),

                a.timeframe.label("timeframe"),
                a.period.label("period"),
                a.params.label("params"),
                a.throttle_seconds.label("throttle_seconds"),
                a.valid_from.label("valid_from"),
                a.valid_to.label("valid_to"),
                a.is_once.label("is_once"),
                a.last_fired_at.label("last_fired_at"),
            )
            .select_from(a)
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
        deleted_is_null: bool = True,
        archived_only: bool = False,
        limit: int,
        offset: int,
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
                a.timeframe.label("timeframe"),
                a.period.label("period"),
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
            .offset(offset)
        )

        if deleted_is_null:
            stmt = stmt.where(a.deleted_at.is_(None))

        if archived_only:
            stmt = stmt.where(a.status == AlertStatus.ARCHIVED)
        elif status:
            stmt = stmt.where(a.status == status)
        else:
            stmt = stmt.where(a.status != AlertStatus.ARCHIVED)

        if sort == AlertSort.RECENT_UPDATED:
            stmt = stmt.order_by(a.updated_at.desc(), a.id.desc())

        elif sort == AlertSort.RECENT_CREATED:
            stmt = stmt.order_by(a.created_at.desc(), a.id.desc())

        elif sort == AlertSort.MARKET_ASC:
            stmt = stmt.order_by(exchange_instrument.c.exchange_symbol.asc(), a.id.desc())

        elif sort == AlertSort.STATUS:
            stmt = stmt.order_by(
                a.status.asc(),
                a.updated_at.desc(),
                a.id.desc(),
            )

        else:
            stmt = stmt.order_by(a.updated_at.desc(), a.id.desc())

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
                timeframe=row.timeframe,
                period=row.period,
                params=row.params,
                throttle_seconds=row.throttle_seconds,
                valid_from=row.valid_from,
                valid_to=row.valid_to,
                is_once=row.is_once,
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
        
