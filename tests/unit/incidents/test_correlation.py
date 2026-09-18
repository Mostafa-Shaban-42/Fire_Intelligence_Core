from incidents.correlation import IncidentCorrelator

def test_spatial_correlation():
    corr = IncidentCorrelator()
    corr.register_spatial_group("g1", ["c1", "c2"])
    assert corr.find_correlated_incident(["c1", "c2"]) is True