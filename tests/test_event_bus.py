from systems.event_bus import EventBus


def test_subscriber_receives_event():
    received = []
    EventBus.on("test", lambda data: received.append(data))
    EventBus.emit("test")
    assert len(received) == 1


def test_multiple_subscribers_all_notified():
    calls = []
    EventBus.on("hit", lambda d: calls.append("a"))
    EventBus.on("hit", lambda d: calls.append("b"))
    EventBus.emit("hit")
    assert calls == ["a", "b"]


def test_unsubscribe_stops_delivery():
    received = []

    def handler(data):
        received.append(data)

    EventBus.on("ev", handler)
    EventBus.off("ev", handler)
    EventBus.emit("ev")
    assert received == []


def test_emit_passes_data_unchanged():
    received = {}
    EventBus.on("ev", lambda d: received.update(d))
    EventBus.emit("ev", {"amount": 42, "name": "fire"})
    assert received == {"amount": 42, "name": "fire"}


def test_emit_unknown_event_no_crash():
    EventBus.emit("no_such_event", {"x": 1})


def test_clear_removes_all_listeners():
    received = []
    EventBus.on("ev", lambda d: received.append(d))
    EventBus.clear()
    EventBus.emit("ev")
    assert received == []
