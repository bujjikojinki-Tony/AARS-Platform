from weather_signal_engine.models.signal_event import SignalEvent


def serialize_signal_event(signal: SignalEvent) -> dict:
    return signal.model_dump()
