"""Pruebas unitarias de la infraestructura en memoria."""
import threading
import time

import pytest

from app.errors import ApiError
from app.infra import IdempotencyStore


def test_idempotency_runs_action_once_for_concurrent_same_key():
    store = IdempotencyStore(ttl_s=60)
    calls = []
    results = []
    barrier = threading.Barrier(8)

    def action():
        calls.append(1)
        time.sleep(0.05)
        return 201, {"ok": True}

    def worker():
        barrier.wait()
        results.append(store.run("misma-clave", "huella", action))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert len(calls) == 1
    assert results == [(201, {"ok": True})] * 8


def test_idempotency_rejects_same_key_with_different_fingerprint():
    store = IdempotencyStore(ttl_s=60)
    assert store.run("clave", "huella-1", lambda: (200, {"ok": 1})) == (200, {"ok": 1})

    with pytest.raises(ApiError) as exc_info:
        store.run("clave", "huella-2", lambda: (200, {"ok": 2}))

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "IDEMPOTENCY_KEY_REUSED"


def test_idempotency_allows_different_keys_concurrently():
    store = IdempotencyStore(ttl_s=60)
    barrier = threading.Barrier(2)
    active = []
    max_active = [0]
    lock = threading.Lock()

    def make_action(label):
        def action():
            with lock:
                active.append(label)
                max_active[0] = max(max_active[0], len(active))
            barrier.wait(timeout=5)
            with lock:
                active.remove(label)
            return 200, {"label": label}
        return action

    results = []
    threads = [
        threading.Thread(target=lambda: results.append(
            store.run("clave-a", "fp-a", make_action("a"))
        )),
        threading.Thread(target=lambda: results.append(
            store.run("clave-b", "fp-b", make_action("b"))
        )),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert max_active[0] == 2
    assert {payload["label"] for _, payload in results} == {"a", "b"}
