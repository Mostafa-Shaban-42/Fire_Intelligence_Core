import pytest
from temporal.smoothing.temporal_smoothing import TemporalSmoother


def test_temporal_smoother_hysteresis():
    smoother = TemporalSmoother(
        window_size=3,
        ema_alpha=0.5,
        activation_threshold=0.60,
        deactivation_threshold=0.30
    )
    
    track_id = 101
    
    # Low confidence -> Not active
    conf1 = smoother.update_track_confidence(track_id, 0.40)
    assert not smoother.is_stably_active(track_id)
    
    # High confidence sequence -> Triggers active state
    smoother.update_track_confidence(track_id, 0.80)
    smoother.update_track_confidence(track_id, 0.85)
    assert smoother.is_stably_active(track_id)
    
    # Drops below deactivation threshold -> Clears active state
    smoother.update_track_confidence(track_id, 0.10)
    smoother.update_track_confidence(track_id, 0.10)
    assert not smoother.is_stably_active(track_id)