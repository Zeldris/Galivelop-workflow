"""The waits of the tests, scaled by one factor (B37): a slow runner (the CI on macOS) raises
GW_TEST_TIMEOUT_SCALE instead of each test growing its own limit. Default 1; a value that is not a number > 0 fails
closed. Every `timeout=<number>`, deadline or polling loop of a test goes through here: tests/test_waits.py lists the
literal ones outside this file.

Imported as `import waits` (`unittest discover -s tests` puts tests/ on sys.path; tests/ is not a package)."""
import os
import time

VAR = "GW_TEST_TIMEOUT_SCALE"


def scale():
    raw = os.environ.get(VAR, "").strip()
    if not raw:
        return 1.0
    try:
        value = float(raw)
    except ValueError:
        value = 0.0
    if not value > 0 or value == float("inf"):
        raise ValueError(f"{VAR}={raw!r} is not a number > 0; unset it or run: export {VAR}=1")
    return value


def timeout(seconds):
    """`seconds` times the factor: for communicate(timeout=…), wait(timeout=…), a watchdog."""
    return seconds * scale()


def wait_for(predicate, seconds=20, interval=0.1):
    """Polls `predicate` every `interval` s for up to timeout(seconds); returns its last value (assert on it)."""
    deadline = time.monotonic() + timeout(seconds)
    while not predicate():
        if time.monotonic() >= deadline:
            return predicate()
        time.sleep(interval)
    return True
