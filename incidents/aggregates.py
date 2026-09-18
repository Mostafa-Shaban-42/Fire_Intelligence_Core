from typing import List, Dict, Any
from shared.schemas import RiskFactorBreakdown

class IncidentAggregate:
    def __init__(self, incident_id: str):
        self.incident_id = incident_id
        self.evidence_list: List[Dict[str, Any]] = []

    def add_evidence(self, detection: Dict[str, Any]) -> None:
        self.evidence_list.append(detection)

    def calculate_aggregated_risk(self) -> float:
        if not self.evidence_list:
            return 0.0
        scores = [item.get("risk_score", 0.0) for item in self.evidence_list]
        return max(scores)