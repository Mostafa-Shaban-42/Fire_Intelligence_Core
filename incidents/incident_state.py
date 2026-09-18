import logging
from shared.enums import IncidentState
from incidents.exceptions import InvalidStateTransitionError

logger = logging.getLogger(__name__)

class IncidentStateMachine:
    VALID_TRANSITIONS = {
        IncidentState.DETECTED: {IncidentState.VALIDATING, IncidentState.CLOSED},
        IncidentState.VALIDATING: {IncidentState.CONFIRMED, IncidentState.RESOLVED, IncidentState.CLOSED},
        IncidentState.CONFIRMED: {IncidentState.ESCALATED, IncidentState.ACKNOWLEDGED, IncidentState.RESOLVED},
        IncidentState.ESCALATED: {IncidentState.ACKNOWLEDGED, IncidentState.RESOLVED},
        IncidentState.ACKNOWLEDGED: {IncidentState.RESOLVED, IncidentState.CLOSED},
        IncidentState.RESOLVED: {IncidentState.CLOSED},
        IncidentState.CLOSED: set(),
    }

    def __init__(self, current_state: IncidentState = IncidentState.DETECTED):
        self._current_state = current_state

    @property
    def current_state(self) -> IncidentState:
        return self._current_state

    def transition_to(self, target_state: IncidentState) -> IncidentState:
        if target_state == self._current_state:
            return self._current_state

        allowed_targets = self.VALID_TRANSITIONS.get(self._current_state, set())
        if target_state not in allowed_targets:
            error_msg = f"Invalid state transition: {self._current_state.value} -> {target_state.value}"
            logger.error(error_msg)
            raise InvalidStateTransitionError(error_msg)

        logger.info(f"Incident state transitioned: {self._current_state.value} -> {target_state.value}")
        self._current_state = target_state
        return self._current_state