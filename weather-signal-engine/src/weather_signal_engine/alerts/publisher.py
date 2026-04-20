from weather_signal_engine.alerts.serializers import serialize_signal_event
from weather_signal_engine.models.signal_event import SignalEvent


class AlertPublisher:
    def publish(self, signal: SignalEvent) -> dict:
        return serialize_signal_event(signal)
