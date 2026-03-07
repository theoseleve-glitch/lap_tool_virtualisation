from trackreco.core.dedupe import pair_score
from trackreco.models import CandidateRecord
from trackreco.rules.decision import classify_cluster


def _cand(**kw):
    base = dict(
        candidate_id="c1",
        venue_name_raw="A",
        venue_name_normalized="a",
        country="France",
        subdivision=None,
        locality=None,
        postal_code=None,
        address_raw=None,
        source_type="ffsa",
        source_url="https://example.com",
        source_record_id="1",
        source_confidence_tier=1,
        source_evidence_snippet="outdoor kart",
        website="https://a.com",
        phone=None,
        email=None,
        lat=48.0,
        lon=2.0,
        geometry_source=None,
        osm_id=None,
        osm_type=None,
        osm_tags={},
        outdoor_status="confirmed_outdoor",
        karting_relevance_status="confirmed_kart_track",
        operating_status="probably_active",
        recurring_venue_status="permanent",
        mixed_mode_flag=False,
        ni_flag=False,
        evidence_ids=["ev1"],
    )
    base.update(kw)
    return CandidateRecord(**base)


def test_pair_score_high_for_same_name_and_site():
    a = _cand(candidate_id="a1")
    b = _cand(candidate_id="a2", source_type="abkc", source_confidence_tier=1)
    score, reasons = pair_score(a, b)
    assert score >= 0.75
    assert "name_exact" in reasons


def test_decision_rejects_temporary():
    a = _cand(recurring_venue_status="temporary_or_event_only")
    status, entity, meta = classify_cluster([a], "v1")
    assert status == "reject"
    assert entity is None
    assert "temporary_event_only" in meta["reason_codes"]
