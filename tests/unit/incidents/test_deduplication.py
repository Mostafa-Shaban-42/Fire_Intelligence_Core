from incidents.deduplication import IncidentDeduplicator

def test_deduplication_window():
    dedup = IncidentDeduplicator(time_window_seconds=5.0)
    assert dedup.is_duplicate("cam1", "z1") is False
    assert dedup.is_duplicate("cam1", "z1") is True