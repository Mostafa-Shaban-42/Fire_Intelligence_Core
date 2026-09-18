# Detection and Decision Pipeline

## 1. Overview

The system processes evidence through a sequence of stages:

```text
Input
  |
  v
Validation
  |
  v
Perception
  |
  v
Temporal Processing
  |
  v
Sensor Fusion
  |
  v
Risk Assessment
  |
  v
Incident Lifecycle
  |
  +---------> Alert Engine
  |
  +---------> API / Dashboard
2. Input ValidationEvery detection must be validated before entering the decision pipeline.Required payload fields:camera_idframe_idtimestampdetection classconfidencebounding boxInvalid bounding boxes must be rejected immediately. Confidence values must be strictly bounded ($0.0 \le \text{confidence} \le 1.0$).3. Temporal ProcessingThe temporal layer receives detections from consecutive frames.Responsibilities:Target trackingPersistence calculationConfidence smoothingTrack agingDisappearance handlingThe temporal engine must not manufacture synthetic detections.4. Confidence SmoothingAn Exponential Moving Average (EMA) is applied:$$S_t = \alpha X_t + (1 - \alpha) S_{t-1}$$Where:$X_t$: Current frame raw confidence score$S_t$: Smoothed confidence score$\alpha$: Configurable smoothing factorThe value of $\alpha$ must be validated experimentally per camera zone.5. Sensor FusionSensor evidence is optional but corroborative.PlaintextVision Evidence
      +
Temperature Telemetry
      +
Smoke / Gas Telemetry
      |
      v
Corroboration Score
Sensor timestamps must be continuously verified. Stale data must be marked as UNAVAILABLE rather than silently treated as zero or valid.6. Risk AssessmentThe risk engine receives normalized evidence.Factors evaluated:Visual ConfidenceTemporal PersistenceSpatial Severity (Area Ratio)Sensor CorroborationDetection Class WeightOutput must contain both final_score and a detailed factor_breakdown for auditability.7. Incident CreationAn incident is created strictly when the configured activation policy is satisfied. The incident engine owns this decision. Alert channels must never create incidents independently.8. Incident LifecyclePlaintextDETECTED
   |
   v
VALIDATING
   |
   v
CONFIRMED
   |
   +----> ACKNOWLEDGED
   |
   v
ESCALATED
   |
   v
RESOLVED
   |
   v
CLOSED
Every transition is governed by explicit policy rules.9. Alert DispatchWhen an incident reaches an alertable state:PlaintextIncident Event
      |
      v
Alert Dispatcher
      |
      +----> Telegram Channel
      |
      +----> WhatsApp Cloud API
      |
      +----> Webhook
Each provider must enforce bounded timeouts, retries with backoff, failure state handling, and structured logs. Provider failures must not block the incident state machine.10. Failure HandlingCamera FailurePlaintextConnected ──> Connection Lost ──> Reconnect Attempt ──┬── Success ──> Connected
                                                     └── Failure ──> Backoff
Sensor FailureIf sensor telemetry exceeds TTL:PlaintextFresh ──> Stale ──> Unavailable
The risk engine explicitly drops stale sensor factors from its scoring calculation.Alert Provider FailurePlaintextDispatch ──┬── Success ──> Delivered
           ├── Timeout ──> Retry (Bounded)
           └── Failure ──> Failed Logged
11. Performance MetricsProduction metrics to continuously monitor:Frame processing latencyInference latencyTemporal processing latencyRisk calculation latencyAPI latencyAlert delivery latencyFrames per second (FPS)Dropped frames ratioActive cameras & active incidentsFalse positive & false negative rates12. ValidationA production deployment requires evaluation against a representative spatial-temporal dataset.Required verification metrics:PrecisionRecallF1 ScoreFalse Positive Rate (FPR)False Negative Rate (FNR)Detection latencyTime-to-confirmationAlert delivery latency