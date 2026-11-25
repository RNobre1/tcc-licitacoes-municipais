from datetime import UTC, datetime

from ingestion.models import RawRecord
from ingestion.raw_records import latest_copies


def test_latest_copies_empty_returns_empty():
    assert latest_copies([]) == []


def test_latest_copies_keeps_newest_by_fetched_at_and_id():
    t1 = datetime(2026, 11, 1, 10, 0, 0, tzinfo=UTC)
    t2 = datetime(2026, 11, 1, 12, 0, 0, tzinfo=UTC)

    # Same endpoint and params
    r1 = RawRecord(id=1, endpoint="/api/test", params={"page": 1}, fetched_at=t1, payload={"v": 1})
    r2 = RawRecord(id=2, endpoint="/api/test", params={"page": 1}, fetched_at=t2, payload={"v": 2})

    deduped = latest_copies([r1, r2])
    assert len(deduped) == 1
    assert deduped[0].id == 2
    assert deduped[0].payload == {"v": 2}

    # Reverse order in input
    deduped_rev = latest_copies([r2, r1])
    assert len(deduped_rev) == 1
    assert deduped_rev[0].id == 2


def test_latest_copies_differentiates_params_and_endpoints():
    t1 = datetime(2026, 11, 1, 10, 0, 0, tzinfo=UTC)
    r1 = RawRecord(id=1, endpoint="/api/test", params={"page": 1}, fetched_at=t1, payload={})
    r2 = RawRecord(id=2, endpoint="/api/test", params={"page": 2}, fetched_at=t1, payload={})
    r3 = RawRecord(id=3, endpoint="/api/other", params={"page": 1}, fetched_at=t1, payload={})

    deduped = latest_copies([r1, r2, r3])
    assert len(deduped) == 3


def test_latest_copies_uses_id_to_break_fetched_at_ties():
    fetched_at = datetime(2026, 11, 1, 12, 0, 0, tzinfo=UTC)
    older_id = RawRecord(
        id=10,
        endpoint="/api/test",
        params={"page": 1},
        fetched_at=fetched_at,
        payload={"version": "lower id"},
    )
    newer_id = RawRecord(
        id=11,
        endpoint="/api/test",
        params={"page": 1},
        fetched_at=fetched_at,
        payload={"version": "higher id"},
    )

    assert [record.id for record in latest_copies([older_id, newer_id])] == [11]
    assert [record.id for record in latest_copies([newer_id, older_id])] == [11]


def test_latest_copies_canonicalizes_nested_param_key_order():
    fetched_at_older = datetime(2026, 11, 1, 10, 0, 0, tzinfo=UTC)
    fetched_at_newer = datetime(2026, 11, 1, 12, 0, 0, tzinfo=UTC)
    older = RawRecord(
        id=20,
        endpoint="/api/test",
        params={"page": 1, "filters": {"state": "PA", "year": 2026}},
        fetched_at=fetched_at_older,
        payload={"version": "older"},
    )
    newer = RawRecord(
        id=21,
        endpoint="/api/test",
        params={"filters": {"year": 2026, "state": "PA"}, "page": 1},
        fetched_at=fetched_at_newer,
        payload={"version": "newer"},
    )

    deduplicated = latest_copies([older, newer])

    assert len(deduplicated) == 1
    assert deduplicated[0].id == 21
