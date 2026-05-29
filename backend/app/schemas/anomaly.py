from backend.app.schemas.telemetry import TelemetryEventRead


class AnomalyRead(TelemetryEventRead):
    reasons: list[str]


def anomaly_from_telemetry(event: object, reasons: list[str]) -> AnomalyRead:
    telemetry = TelemetryEventRead.model_validate(event)
    return AnomalyRead(**telemetry.model_dump(), reasons=reasons)
