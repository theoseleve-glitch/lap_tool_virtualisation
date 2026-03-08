from types import SimpleNamespace

import pytest

from trackreco_platform.domain.enums import LayoutStatus, ReviewActionType, ReviewStatus
from trackreco_platform.services.permissions import Actor
from trackreco_platform.services.review_workflow import ALLOWED_REVIEW_TRANSITIONS, WorkflowError, apply_review_action


class FakeDB:
    def __init__(self):
        self.records = []

    def add(self, obj):
        self.records.append(obj)


def test_review_state_machine_invariants():
    assert (ReviewStatus.IN_REVIEW, ReviewActionType.APPROVE) in ALLOWED_REVIEW_TRANSITIONS
    assert (ReviewStatus.APPROVED, ReviewActionType.APPROVE) not in ALLOWED_REVIEW_TRANSITIONS


def test_approve_transition_sets_validated_status():
    db = FakeDB()
    version = SimpleNamespace(id="lv1", review_status=ReviewStatus.IN_REVIEW, status=LayoutStatus.DRAFT)
    actor = Actor(email="reviewer@example.com", role="reviewer")

    apply_review_action(db, layout_version=version, action=ReviewActionType.APPROVE, notes="ok", actor=actor, correlation_id="cid")

    assert version.review_status == ReviewStatus.APPROVED
    assert version.status == LayoutStatus.VALIDATED
    assert len(db.records) == 2


def test_invalid_transition_raises():
    db = FakeDB()
    version = SimpleNamespace(id="lv1", review_status=ReviewStatus.REJECTED, status=LayoutStatus.DRAFT)
    actor = Actor(email="reviewer@example.com", role="reviewer")

    with pytest.raises(WorkflowError):
        apply_review_action(db, layout_version=version, action=ReviewActionType.APPROVE, notes=None, actor=actor, correlation_id="cid")
