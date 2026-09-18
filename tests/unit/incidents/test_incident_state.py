import pytest
from incidents.incident_state import IncidentStateMachine
from incidents.exceptions import InvalidStateTransitionError
from shared.enums import IncidentState

def test_valid_incident_state_transitions():
    sm = IncidentStateMachine()
    assert sm.current_state == IncidentState.DETECTED
    
    new_state = sm.transition_to(IncidentState.VALIDATING)
    assert new_state == IncidentState.VALIDATING

def test_invalid_incident_state_transition():
    sm = IncidentStateMachine()
    # Expect the specific custom exception raised by your state machine
    with pytest.raises((ValueError, InvalidStateTransitionError)):
        sm.transition_to(IncidentState.RESOLVED)  # Cannot jump from DETECTED directly to RESOLVED