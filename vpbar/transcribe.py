"""Video transcription using faster-whisper."""

import os
import subprocess
import tempfile
from pathlib import Path


def _seconds_to_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def video_to_srt(
    video_path: str,
    srt_path: str,
    model_size: str = "large-v3-turbo",
    device: str = "auto",
) -> str | None:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("faster-whisper not installed. Run: pip install faster-whisper", file=__import__('sys').stderr)
        return None

    print(f"Extracting audio from: {video_path}")
    audio_path = os.path.join(tempfile.gettempdir(), "deveco", f"{Path(video_path).stem}_audio.wav")
    Path(audio_path).parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path,
             "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
             audio_path],
            capture_output=True, check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to extract audio: {e.stderr.decode('utf-8', errors='replace')}", file=__import__('sys').stderr)
        return None
    except FileNotFoundError:
        print("ffmpeg not found. Please ensure FFmpeg is installed.", file=__import__('sys').stderr)
        return None

    compute_type = "default"
    if device == "auto":
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"

    if device == "cuda":
        compute_type = "float16"

    print(f"Loading Whisper model: {model_size} (device={device})")
    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
    except Exception as e:
        print(f"Failed to load Whisper model: {e}", file=__import__('sys').stderr)
        return None

    print("Transcribing...")
    try:
        segments, info = model.transcribe(audio_path, language="zh", beam_size=5)
    except Exception as e:
        print(f"Transcription failed: {e}", file=__import__('sys').stderr)
        return None

    print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")

    entries = []
    for segment in segments:
        if segment.text.strip():
            entries.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })

    Path(srt_path).parent.mkdir(parents=True, exist_ok=True)
    with open(srt_path, 'w', encoding='utf-8') as f:
        for i, entry in enumerate(entries, 1):
            f.write(f"{i}\n")
            f.write(f"{_seconds_to_srt_time(entry['start'])} --> {_seconds_to_srt_time(entry['end'])}\n")
            f.write(f"{entry['text']}\n\n")

    print(f"Transcription saved: {srt_path} ({len(entries)} entries)")
    return srt_path
