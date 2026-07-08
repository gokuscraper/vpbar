"""Memory usage test for Whisper vs FunASR transcription.

Usage:
    python tests/memtest.py                         # both engines
    python tests/memtest.py funasr-only              # FunASR only
    python tests/memtest.py whisper-only             # Whisper only
"""

import os
import sys
import time
import threading
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.chdir(str(Path(__file__).parent.parent))

try:
    import psutil
except ImportError:
    print("psutil not installed. Run: pip install psutil")
    sys.exit(1)


def _peak_mem_tracker(pid: int, interval: float = 0.05, stop_event=None) -> list[float]:
    proc = psutil.Process(pid)
    samples = []
    while not stop_event.is_set():
        try:
            mem = proc.memory_info().rss / (1024 * 1024)
            samples.append(mem)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            break
        time.sleep(interval)
    return samples


def _run_tracked(label: str, fn, *args, **kwargs):
    stop = threading.Event()
    samples = []
    tracker = threading.Thread(
        target=lambda: samples.extend(_peak_mem_tracker(os.getpid(), stop_event=stop)),
        daemon=True
    )
    tracker.start()
    try:
        t0 = time.time()
        result = fn(*args, **kwargs)
        elapsed = time.time() - t0
    finally:
        stop.set()
        tracker.join(timeout=3)

    if samples:
        baseline = min(samples[:10])
        peak = max(samples)
        delta = peak - baseline
    else:
        peak = delta = 0.0

    print(f"\n{'='*50}")
    print(f"  {label}")
    print(f"{'='*50}")
    print(f"  Time:       {elapsed:.1f}s")
    print(f"  Peak RSS:   {peak:.0f} MB")
    print(f"  Delta RSS:  {delta:.0f} MB")
    print(f"{'='*50}\n")
    return label, peak, elapsed, result


def test_whisper(size: str = "large-v3-turbo"):
    from vpbar.transcribe import _transcribe_whisper, _extract_audio
    fixture = Path("tests/fixtures/green.mp4")
    audio_path = _extract_audio(str(fixture))
    if audio_path is None:
        return ("FAIL: audio extraction", 0, 0, None)
    srt_path = os.path.join(tempfile.gettempdir(), "deveco", f"memtest_whisper_{size}.srt")
    return _run_tracked(f"Whisper {size}", _transcribe_whisper,
                        audio_path, srt_path, size, "cpu", "default")


def test_funasr():
    from vpbar.transcribe import _transcribe_funasr, _extract_audio
    fixture = Path("tests/fixtures/green.mp4")
    audio_path = _extract_audio(str(fixture))
    if audio_path is None:
        return ("FAIL: audio extraction", 0, 0, None)
    srt_path = os.path.join(tempfile.gettempdir(), "deveco", "memtest_funasr.srt")
    return _run_tracked("FunASR (VAD + ONNX quantized)", _transcribe_funasr,
                        audio_path, srt_path, "cpu")


if __name__ == "__main__":
    results = []
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode in ("all", "whisper-only"):
        print(">>> Testing Whisper large-v3-turbo...")
        results.append(test_whisper("large-v3-turbo"))

    if mode in ("all", "funasr-only"):
        print(">>> Testing FunASR...")
        results.append(test_funasr())

    print("\n" + "="*50)
    print("  SUMMARY")
    print("="*50)
    for label, peak, elapsed, _ in results:
        print(f"  {label}")
        print(f"    Time: {elapsed:.1f}s | Peak RSS: {peak:.0f} MB")
    print("="*50)
