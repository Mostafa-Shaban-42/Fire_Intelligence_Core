import pytest
from incidents.incident_state import IncidentStateMachine
from shared.enums import IncidentState
from incidents.exceptions import InvalidStateTransitionError

def test_valid_transitions():
    sm = IncidentStateMachine(IncidentState.DETECTED)
    assert sm.transition_to(IncidentState.VALIDATING) == IncidentState.VALIDATING

def test_invalid_transition_raises():
    sm = IncidentStateMachine(IncidentState.CLOSED)
    with pytest.raises(InvalidStateTransitionError):
        sm.transition_to(IncidentState.CONFIRMED)