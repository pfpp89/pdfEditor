import json

import pytest

from pdf_editor import lifecycle
from pdf_editor.lifecycle import ClientTracker
from pdf_editor.server import create_app


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return FakeClock()


def advance(tracker, clock, seconds, step=1.0):
    """Move time forward the way the 1-second watcher would see it."""
    exited = False
    for _ in range(int(seconds / step)):
        clock.now += step
        exited = tracker.should_exit() or exited
    return exited


def make(clock):
    return ClientTracker(grace=8, stale=180, startup=120, clock=clock)


def test_exits_shortly_after_last_window_closes(clock):
    tracker = make(clock)
    tracker.beat("a")
    assert not advance(tracker, clock, 30)
    tracker.bye("a")
    assert not advance(tracker, clock, 5)
    assert advance(tracker, clock, 5)


def test_reload_within_grace_keeps_running(clock):
    tracker = make(clock)
    tracker.beat("a")
    tracker.bye("a")          # page unloads...
    advance(tracker, clock, 2)
    tracker.beat("b")         # ...and the reloaded page reconnects
    assert not advance(tracker, clock, 60, step=1)


def test_waits_for_every_window(clock):
    tracker = make(clock)
    tracker.beat("a")
    tracker.beat("b")
    tracker.bye("a")
    assert not advance(tracker, clock, 20)  # window "b" is still open
    tracker.bye("b")
    assert advance(tracker, clock, 10)


def test_silent_window_dropped_after_stale_timeout(clock):
    tracker = make(clock)
    tracker.beat("a")         # then the browser crashes: no goodbye, no more beats
    assert not advance(tracker, clock, 170)
    assert advance(tracker, clock, 30)


def test_no_window_ever_connects(clock):
    tracker = make(clock)
    assert not advance(tracker, clock, 110)
    assert advance(tracker, clock, 20)


def test_computer_sleep_does_not_stop_the_editor(clock):
    tracker = make(clock)
    tracker.beat("a")
    clock.now += 3600         # laptop lid closed for an hour: the watcher didn't run
    assert not tracker.should_exit()
    tracker.beat("a")         # the page wakes up and beats again
    assert not advance(tracker, clock, 60)


def test_heartbeat_and_bye_endpoints():
    tracker = ClientTracker()
    client = create_app("tok", 5000, tracker).test_client()
    headers = {"Host": "127.0.0.1:5000", "X-Token": "tok"}
    assert client.get("/api/ping", headers=headers).status_code == 200
    assert client.post("/api/heartbeat", json={"id": "x"}, headers=headers).status_code == 200
    assert "x" in tracker._clients
    # sendBeacon can't set headers: the token comes in the query string.
    res = client.post("/api/bye?t=tok", data=json.dumps({"id": "x"}),
                      headers={"Host": "127.0.0.1:5000"}, content_type="application/json")
    assert res.status_code == 204
    assert "x" not in tracker._clients
    assert client.post("/api/heartbeat", json={}, headers=headers).status_code == 400
    assert client.post("/api/heartbeat", json={"id": "x"},
                       headers={"Host": "127.0.0.1:5000"}).status_code == 403


def test_instance_file(tmp_path, monkeypatch):
    monkeypatch.setattr(lifecycle, "state_dir", lambda: str(tmp_path))
    assert lifecycle.find_running_instance() is None
    lifecycle.register_instance(1, "tok")         # nothing listens on port 1
    assert lifecycle.find_running_instance() is None
    lifecycle.unregister_instance("other")        # not ours: kept
    assert (tmp_path / "instance.json").exists()
    lifecycle.unregister_instance("tok")
    assert not (tmp_path / "instance.json").exists()


def test_instance_lock_is_exclusive(tmp_path, monkeypatch):
    monkeypatch.setattr(lifecycle, "state_dir", lambda: str(tmp_path))
    first = lifecycle.acquire_instance_lock()
    assert first is not None
    assert lifecycle.acquire_instance_lock() is None  # a second editor can't take it
    first.close()                                      # released when the editor exits
    again = lifecycle.acquire_instance_lock()
    assert again is not None
    again.close()


def test_language_setting_survives_restart(tmp_path, monkeypatch):
    monkeypatch.setattr(lifecycle, "state_dir", lambda: str(tmp_path))
    headers = {"Host": "127.0.0.1:5000", "X-Token": "tok"}
    client = create_app("tok", 5000).test_client()
    assert client.get("/api/settings", headers=headers).get_json() == {}
    assert client.post("/api/settings", json={"lang": "pt-PT"}, headers=headers).status_code == 200
    assert client.post("/api/settings", json={"lang": "xx"}, headers=headers).status_code == 400
    # A new server (next start, different port) still knows the choice.
    other = create_app("tok2", 6000).test_client()
    res = other.get("/api/settings", headers={"Host": "127.0.0.1:6000", "X-Token": "tok2"})
    assert res.get_json() == {"lang": "pt-PT"}
