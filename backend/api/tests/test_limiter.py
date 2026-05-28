from app.limiter import ConversionLimiter


def test_limiter_allows_active_slot_when_available():
    limiter = ConversionLimiter(max_active=2, max_pending=10)

    assert limiter.reserve_slot() == "PROCESSING"
    assert limiter.active_count == 1


def test_limiter_uses_pending_when_active_slots_are_full():
    limiter = ConversionLimiter(max_active=1, max_pending=10)

    assert limiter.reserve_slot() == "PROCESSING"
    assert limiter.reserve_slot() == "PENDING"
    assert limiter.pending_count == 1


def test_limiter_rejects_when_pending_queue_is_full():
    limiter = ConversionLimiter(max_active=1, max_pending=1)

    assert limiter.reserve_slot() == "PROCESSING"
    assert limiter.reserve_slot() == "PENDING"
    assert limiter.reserve_slot() is None


def test_limiter_release_promotes_pending_conversion():
    limiter = ConversionLimiter(max_active=1, max_pending=2)
    limiter.reserve_slot()
    limiter.reserve_slot()

    assert limiter.release_active() is True
    assert limiter.active_count == 1
    assert limiter.pending_count == 0
