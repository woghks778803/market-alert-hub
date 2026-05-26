from app.domain import OutboxDTO
from app.infra.db.model import OutboxModel

def to_outbox_where_mapping(outbox_filter: OutboxDTO.OutboxFilter):
    wheres = []

    if outbox_filter.id is not None:
        wheres.append(OutboxModel.id == outbox_filter.id)
    elif outbox_filter.ids:
        wheres.append(OutboxModel.id.in_(outbox_filter.ids))  # [] 방지

    if outbox_filter.next_run_at is not None:
        wheres.append(OutboxModel.next_run_at < outbox_filter.next_run_at)
    if outbox_filter.status is not None:
        wheres.append(OutboxModel.status == outbox_filter.status)

    return wheres

def to_outbox_values_mapping(outbox_update: OutboxDTO.OutboxUpdate):
    values = {}

    values[OutboxModel.sent_at] = outbox_update.sent_at

    if outbox_update.status is not None:
        values[OutboxModel.status] = outbox_update.status
    if outbox_update.attempts is not None:
        values[OutboxModel.attempts] = outbox_update.attempts
    if outbox_update.next_run_at is not None:
        values[OutboxModel.next_run_at] = outbox_update.next_run_at

    return values