import os
import tempfile
import time

_BENCHMARK_FILE_SIZE_BYTES = 64 * 1024 * 1024  # 64MB
_CHUNK_SIZE_BYTES = 1024 * 1024  # 1MB

# Reference points (GB/s) roughly bracketing "definitely fine" and
# "definitely too slow to bother" sequential read speeds for I-16's
# streaming tier -- SATA SSD ~0.3GB/s at the low end, a fast NVMe
# ~3GB/s+ at the high end. Not calibrated against real streaming
# inference throughput -- no llama.cpp-direct provider exists yet to
# measure that against (ADR-0021 defers the execution path); an
# honestly-labeled proxy, not a validated prediction.
_MIN_VIABLE_GB_S = 0.3
_FULLY_VIABLE_GB_S = 3.0


def benchmark_ssd_read_speed_gb_s() -> float | None:
    """
    Real, best-effort sequential read throughput measurement (I-16):
    writes a 64MB temp file, then times reading it back sequentially.

    Honest limitation: on a modern OS this measures whatever storage
    path is actually fastest right now -- often the OS page cache
    right after the file was just written, not guaranteed cold-disk
    I/O (reliably dropping the page cache needs privileges this
    doesn't assume it has). Treated as an optimistic upper-bound proxy,
    the same "conservative but real, not lab-grade" calibration
    approach already used for the KV-cache memory formula (ADR-0017).

    Returns `None` (not a guess) if the benchmark itself fails for any
    reason -- no writable temp dir, permission error, etc.
    """

    path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False) as handle:
            path = handle.name
            chunk = os.urandom(_CHUNK_SIZE_BYTES)
            written = 0

            while written < _BENCHMARK_FILE_SIZE_BYTES:
                handle.write(chunk)
                written += len(chunk)

            handle.flush()
            os.fsync(handle.fileno())

        start = time.perf_counter()

        with open(path, "rb") as handle:
            while handle.read(_CHUNK_SIZE_BYTES):
                pass

        elapsed = time.perf_counter() - start

        if elapsed <= 0:
            return None

        return (_BENCHMARK_FILE_SIZE_BYTES / (1024**3)) / elapsed
    except OSError:
        return None
    finally:
        if path is not None:
            try:
                os.unlink(path)
            except OSError:
                pass


def streaming_viability(read_speed_gb_s: float | None) -> float:
    """
    Normalizes a measured read speed to a 0.0-1.0 "streaming
    viability" score. `None` (benchmark unavailable/failed) scores
    0.0 -- absence of evidence means "don't offer this," the safe
    direction for a feature that's opt-in and off by default anyway.
    """

    if read_speed_gb_s is None or read_speed_gb_s <= _MIN_VIABLE_GB_S:
        return 0.0

    if read_speed_gb_s >= _FULLY_VIABLE_GB_S:
        return 1.0

    return (read_speed_gb_s - _MIN_VIABLE_GB_S) / (
        _FULLY_VIABLE_GB_S - _MIN_VIABLE_GB_S
    )
