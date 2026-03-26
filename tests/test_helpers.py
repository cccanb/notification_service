from app.worker.helpers import compute_retry_delay


def test_delay_increases_with_attempts():
    delays = [compute_retry_delay(i, jitter=0.0) for i in range(4)]
    assert all(d >= 0 for d in delays)


def test_delay_respects_cap():
    cap = 5.0
    for attempt in range(10):
        delay = compute_retry_delay(attempt, cap=cap, jitter=0.0)
        assert delay <= cap, f"delay {delay} exceeded cap {cap} at attempt {attempt}"


def test_delay_is_non_negative():
    for attempt in range(5):
        for _ in range(20):
            delay = compute_retry_delay(attempt)
            assert delay >= 0, f"negative delay {delay} at attempt {attempt}"
