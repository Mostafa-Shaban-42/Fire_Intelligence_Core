from typing import List, Dict, Set

class IncidentCorrelator:
    def __init__(self):
        self._camera_groups: Dict[str, Set[str]] = {}

    def register_spatial_group(self, group_id: str, camera_ids: List[str]):
        self._camera_groups[group_id] = set(camera_ids)

    def find_correlated_incident(self, active_cameras: List[str]) -> bool:
        active_set = set(active_cameras)
        for group in self._camera_groups.values():
            if len(group.intersection(active_set)) > 1:
                return True
        return False