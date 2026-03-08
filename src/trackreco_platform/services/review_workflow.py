from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from trackreco_platform.domain.enums import LayoutStatus, PublishAction, ReviewActionType, ReviewStatus
from trackreco_platform.domain.models import AuditEvent, Layout, LayoutVersion, PublishHistory, ReviewAction
from trackreco_platform.services.permissions import Actor


@dataclass(frozen=True)
class ReviewTransition:
    from_state: ReviewStatus
    action: ReviewActionType
    to_state: ReviewStatus


ALLOWED_REVIEW_TRANSITIONS = {
    (ReviewStatus.DRAFT, ReviewActionType.SUBMIT_FOR_REVIEW): ReviewStatus.IN_REVIEW,
    (ReviewStatus.CHANGES_REQUESTED, ReviewActionType.SUBMIT_FOR_REVIEW): ReviewStatus.IN_REVIEW,
    (ReviewStatus.IN_REVIEW, ReviewActionType.APPROVE): ReviewStatus.APPROVED,
    (ReviewStatus.IN_REVIEW, ReviewActionType.REJECT): ReviewStatus.REJECTED,
    (ReviewStatus.IN_REVIEW, ReviewActionType.REQUEST_CHANGES): ReviewStatus.CHANGES_REQUESTED,
}


class WorkflowError(ValueError):
    pass


def _record_audit(db: Session, *, event_type: str, entity_type: str, entity_id: str, actor: Actor, correlation_id: str, payload: dict):
    db.add(
        AuditEvent(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            correlation_id=correlation_id,
            payload=payload,
            created_by=actor.email,
            updated_by=actor.email,
        )
    )


def apply_review_action(db: Session, *, layout_version: LayoutVersion, action: ReviewActionType, notes: str | None, actor: Actor, correlation_id: str) -> LayoutVersion:
    key = (layout_version.review_status, action)
    if key not in ALLOWED_REVIEW_TRANSITIONS:
        raise WorkflowError(f"Invalid transition: {layout_version.review_status.value} -> {action.value}")

    next_state = ALLOWED_REVIEW_TRANSITIONS[key]
    layout_version.review_status = next_state
    if next_state == ReviewStatus.APPROVED:
        layout_version.status = LayoutStatus.VALIDATED

    db.add(
        ReviewAction(
            layout_version_id=layout_version.id,
            action=action,
            notes=notes,
            created_by=actor.email,
            updated_by=actor.email,
        )
    )
    _record_audit(
        db,
        event_type="review.action",
        entity_type="layout_version",
        entity_id=layout_version.id,
        actor=actor,
        correlation_id=correlation_id,
        payload={"action": action.value, "from": key[0].value, "to": next_state.value, "notes": notes},
    )
    return layout_version


def publish_layout_version(db: Session, *, layout: Layout, target_version: LayoutVersion, actor: Actor, reason: str | None, correlation_id: str) -> PublishHistory:
    if target_version.review_status != ReviewStatus.APPROVED:
        raise WorkflowError("Only approved versions can be published")

    previous_id = layout.active_version_id
    action = PublishAction.ROLLBACK if previous_id and previous_id != target_version.id else PublishAction.PUBLISH

    layout.active_version_id = target_version.id
    target_version.status = LayoutStatus.PUBLISHED

    history = PublishHistory(
        layout_version_id=target_version.id,
        previous_layout_version_id=previous_id,
        action=action,
        reason=reason,
        created_by=actor.email,
        updated_by=actor.email,
    )
    db.add(history)
    _record_audit(
        db,
        event_type="layout.publish",
        entity_type="layout",
        entity_id=layout.id,
        actor=actor,
        correlation_id=correlation_id,
        payload={
            "published_version_id": target_version.id,
            "previous_version_id": previous_id,
            "action": action.value,
            "reason": reason,
            "published_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return history


def unpublish_layout(db: Session, *, layout: Layout, actor: Actor, reason: str | None, correlation_id: str) -> PublishHistory:
    if not layout.active_version_id:
        raise WorkflowError("No active version to unpublish")

    active_id = layout.active_version_id
    layout.active_version_id = None
    history = PublishHistory(
        layout_version_id=active_id,
        previous_layout_version_id=active_id,
        action=PublishAction.UNPUBLISH,
        reason=reason,
        created_by=actor.email,
        updated_by=actor.email,
    )
    db.add(history)
    _record_audit(
        db,
        event_type="layout.unpublish",
        entity_type="layout",
        entity_id=layout.id,
        actor=actor,
        correlation_id=correlation_id,
        payload={"unpublished_version_id": active_id, "reason": reason},
    )
    return history


def publish_history_for_layout(db: Session, layout_id: str) -> list[PublishHistory]:
    return db.scalars(
        select(PublishHistory)
        .join(LayoutVersion, LayoutVersion.id == PublishHistory.layout_version_id)
        .where(LayoutVersion.layout_id == layout_id)
        .order_by(PublishHistory.created_at.desc())
    ).all()
