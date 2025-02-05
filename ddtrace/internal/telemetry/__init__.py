"""
Instrumentation Telemetry API.
This is normally started automatically by ``ddtrace-run`` when the
``DD_INSTRUMENTATION_TELEMETRY_ENABLED`` variable is set.
To start the service manually, invoke the ``enable`` method::
    from ddtrace.internal.telemetry import telemetry_lifecycle_writer
    telemetry_lifecycle_writer.enable()
"""
from .writer import TelemetryLogsMetricsWriter
from .writer import TelemetryWriter


telemetry_metrics_writer = TelemetryLogsMetricsWriter()
telemetry_lifecycle_writer = TelemetryWriter()

__all__ = ["telemetry_lifecycle_writer"]
