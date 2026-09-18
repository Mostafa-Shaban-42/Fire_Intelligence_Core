from incidents.aggregates import IncidentAggregate

def test_aggregate_risk():
    agg = IncidentAggregate("INC-1")
    agg.add_evidence({"risk_score": 40.0})
    agg.add_evidence({"risk_score": 85.0})
    assert agg.calculate_aggregated_risk() == 85.0