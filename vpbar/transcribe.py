"""Video transcription engines: Whisper and FunASR."""

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


MODELS_DIR = Path(__file__).parent.parent / "models"


def _safe_cache_dir(subdir: str) -> str:
    """Return an ASCII-only cache path since some C++ libs (sentencepiece)
    cannot handle non-ASCII paths on Windows."""
    path = str(MODELS_DIR / subdir)
    try:
        path.encode("ascii")
        return path
    except UnicodeEncodeError:
        fallback = os.path.join(tempfile.gettempdir(), "deveco", "models", subdir)
        os.makedirs(fallback, exist_ok=True)
        print(f"Note: project path contains non-ASCII chars, using fallback cache: {fallback}")
        return fallback


def _extract_audio(video_path: str) -> str | None:
    audio_path = os.path.join(tempfile.gettempdir(), "deveco", f"{Path(video_path).stem}_audio.wav")
    Path(audio_path).parent.mkdir(parents=True, exist_ok=True)
    print(f"Extracting audio from: {video_path}")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path,
             "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
             audio_path],
            capture_output=True, check=True
        )
        return audio_path
    except subprocess.CalledProcessError as e:
        print(f"Failed to extract audio: {e.stderr.decode('utf-8', errors='replace')}", file=__import__('sys').stderr)
        return None
    except FileNotFoundError:
        print("ffmpeg not found. Please ensure FFmpeg is installed.", file=__import__('sys').stderr)
        return None


def _write_srt(srt_path: str, entries: list[dict]) -> str:
    Path(srt_path).parent.mkdir(parents=True, exist_ok=True)
    with open(srt_path, 'w', encoding='utf-8') as f:
        for i, entry in enumerate(entries, 1):
            f.write(f"{i}\n")
            f.write(f"{_seconds_to_srt_time(entry['start'])} --> {_seconds_to_srt_time(entry['end'])}\n")
            f.write(f"{entry['text']}\n\n")
    print(f"Transcription saved: {srt_path} ({len(entries)} entries)")
    return srt_path


def _transcribe_whisper(
    audio_path: str,
    srt_path: str,
    model_size: str,
    device: str,
    compute_type: str,
) -> str | None:
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        print(f"faster-whisper not installed ({e}). Run: pip install faster-whisper", file=__import__('sys').stderr)
        return None

    if compute_type == "default":
        compute_type = "float16" if device == "cuda" else "default"

    print(f"Loading Whisper model: {model_size} (device={device}, compute_type={compute_type})")
    model_dir = _safe_cache_dir(model_size)
    os.makedirs(model_dir, exist_ok=True)
    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type, download_root=model_dir)
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
    return _write_srt(srt_path, entries)


def _get_audio_duration(audio_path: str) -> float:
    import json
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "json", audio_path],
            capture_output=True, text=True, check=True
        )
        return float(json.loads(r.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def _get_onnx_model_dir(cache_dir: str) -> str:
    """Return path to ONNX quantized model, auto-download if missing."""
    onnx_dir = os.path.join(cache_dir, "models", "iic", "SenseVoiceSmall-onnx")
    if not os.path.isdir(onnx_dir):
        print("Downloading ONNX quantized model from ModelScope...")
        try:
            from modelscope.hub.snapshot_download import snapshot_download
            snapshot_download("iic/SenseVoiceSmall-onnx", cache_dir=cache_dir)
        except Exception as e:
            print(f"Failed to download ONNX model: {e}", file=__import__('sys').stderr)
            return ""
    # Copy BPE model from PyTorch model directory if available
    pt_dir = os.path.join(cache_dir, "models", "iic", "SenseVoiceSmall")
    bpe_file = "chn_jpn_yue_eng_ko_spectok.bpe.model"
    if not os.path.isfile(os.path.join(onnx_dir, bpe_file)):
        src = os.path.join(pt_dir, bpe_file)
        if os.path.isfile(src):
            import shutil
            os.makedirs(onnx_dir, exist_ok=True)
            shutil.copy2(src, os.path.join(onnx_dir, bpe_file))
    return onnx_dir


_punc_model = None

def _add_punctuation(text: str) -> str:
    global _punc_model
    if _punc_model is None:
        from funasr import AutoModel
        _punc_model = AutoModel(model='ct-punc', device='cpu', disable_update=True)
    result = _punc_model.generate(input=text)
    return result[0]['text'] if result else text


def _split_text_by_punctuation(text: str, start: float, end: float) -> list[dict]:
    import re
    if not text.strip():
        return []
    text = _add_punctuation(text)
    # Split by sentence-ending punctuation
    parts = re.split(r'(?<=[。！？；.!?;])', text)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) <= 1:
        return [{"start": start, "end": end, "text": text}]
    dur = end - start
    total_chars = sum(len(p) for p in parts)
    if total_chars == 0:
        return [{"start": start, "end": end, "text": text}]
    entries = []
    acc = 0.0
    for i, p in enumerate(parts):
        weight = len(p) / total_chars
        if i == len(parts) - 1:
            seg_end = end
        else:
            seg_end = round(start + (acc + weight) * dur, 3)
        entries.append({"start": round(start + acc * dur, 3), "end": seg_end, "text": p})
        acc += weight
    return entries


def _split_text_by_duration(text: str, start: float, end: float, target_dur: float = 4.0) -> list[dict]:
    """Split text into roughly equal-time subtitles, targeting ~target_dur seconds each."""
    dur = end - start
    if dur <= target_dur * 1.2:
        return [{"start": start, "end": end, "text": text.strip()}] if text.strip() else []
    n = max(2, round(dur / target_dur))
    chunk_size = max(1, len(text) // n)
    parts = []
    pos = 0
    while pos < len(text):
        end_pos = pos + chunk_size
        if end_pos >= len(text):
            parts.append(text[pos:].strip())
            break
        # Try to break at a space or word boundary near chunk_size
        lookahead = text[end_pos:end_pos + 8]
        space_idx = -1
        for j, ch in enumerate(lookahead):
            if ch == ' ':
                space_idx = j
                break
        if space_idx >= 0:
            parts.append(text[pos:end_pos + space_idx].strip())
            pos = end_pos + space_idx + 1
        else:
            # Force break at chunk boundary
            parts.append(text[pos:end_pos].strip())
            pos = end_pos
    parts = [p for p in parts if p]
    if not parts:
        return [{"start": start, "end": end, "text": text.strip()}]
    chunk_dur = dur / len(parts)
    entries = []
    for i, p in enumerate(parts):
        seg_start = round(start + i * chunk_dur, 3)
        seg_end = round(start + (i + 1) * chunk_dur, 3) if i < len(parts) - 1 else end
        entries.append({"start": seg_start, "end": seg_end, "text": p})
    return entries


def _transcribe_funasr(
    audio_path: str,
    srt_path: str,
    device: str,
) -> str | None:
    try:
        from funasr import AutoModel
    except ImportError as e:
        print(f"funasr not installed ({e}). Run: pip install funasr", file=__import__('sys').stderr)
        return None

    funasr_cache = _safe_cache_dir("funasr")
    os.environ.setdefault("MODELSCOPE_CACHE", funasr_cache)
    device_str = "cuda:0" if device == "cuda" else "cpu"

    # Step 1: VAD for timestamps
    print("Running VAD (fsmn-vad) for speech segment timestamps...")
    try:
        vad_model = AutoModel(model="fsmn-vad", device=device_str)
        vad_result = vad_model.generate(input=audio_path)
    except Exception as e:
        print(f"VAD failed: {e}", file=__import__('sys').stderr)
        vad_segments = []
    else:
        vad_segments = []
        if vad_result and isinstance(vad_result, list):
            for item in vad_result:
                for seg in item.get("value", []):
                    if isinstance(seg, (list, tuple)) and len(seg) >= 2:
                        vad_segments.append((seg[0], seg[1]))
        if vad_segments:
            print(f"VAD detected {len(vad_segments)} speech segments")
        else:
            print("VAD detected no speech segments, will use full duration")

    # Step 2: ASR per VAD segment with ONNX quantized SenseVoiceSmall
    try:
        from funasr_onnx import SenseVoiceSmall as OnnxSenseVoice
        from funasr_onnx.utils.postprocess_utils import rich_transcription_postprocess
    except ImportError as e:
        print(f"funasr-onnx not installed ({e}). Run: pip install funasr-onnx", file=__import__('sys').stderr)
        return None

    onnx_model_dir = _get_onnx_model_dir(funasr_cache)
    if not os.path.isdir(onnx_model_dir):
        print(f"ONNX model not found at {onnx_model_dir}. Download models/iic/SenseVoiceSmall-onnx from ModelScope first.",
              file=__import__('sys').stderr)
        return None

    print("Loading ONNX quantized SenseVoiceSmall...")
    try:
        asr_model = OnnxSenseVoice(onnx_model_dir, batch_size=10, quantize=True)
    except Exception as e:
        print(f"Failed to load ONNX model: {e}", file=__import__('sys').stderr)
        return None

    temp_dir = os.path.join(tempfile.gettempdir(), "deveco", "segments")
    os.makedirs(temp_dir, exist_ok=True)

    entries = []
    if vad_segments:
        print(f"Extracting and transcribing {len(vad_segments)} segments...")
        for i, (start_ms, end_ms) in enumerate(vad_segments):
            seg_path = os.path.join(temp_dir, f"seg_{i:03d}.wav")
            dur_s = (end_ms - start_ms) / 1000.0
            subprocess.run(
                ["ffmpeg", "-y", "-ss", f"{start_ms/1000:.3f}", "-i", audio_path,
                 "-t", f"{dur_s:.3f}", "-vn", "-acodec", "pcm_s16le",
                 "-ar", "16000", "-ac", "1", seg_path],
                capture_output=True, check=True
            )
            result = asr_model([seg_path], language="auto", use_itn=True)
            text = rich_transcription_postprocess(result[0]) if result else ""
            if text.strip():
                entries.extend(_split_text_by_punctuation(text.strip(), start_ms / 1000.0, end_ms / 1000.0))
    else:
        print("No VAD segments, transcribing full audio...")
        result = asr_model([audio_path], language="auto", use_itn=True)
        text = rich_transcription_postprocess(result[0]) if result else ""
        if text.strip():
            audio_duration = _get_audio_duration(audio_path)
            entries.extend(_split_text_by_punctuation(text.strip(), 0.0, audio_duration))

    if not entries:
        print("No valid segments from FunASR", file=__import__('sys').stderr)
        return None

    print(f"Created {len(entries)} SRT entries")
    return _write_srt(srt_path, entries)


def video_to_srt(
    video_path: str,
    srt_path: str,
    model_size: str = "large-v3-turbo",
    device: str = "auto",
    compute_type: str = "default",
    engine: str = "whisper",
) -> str | None:
    if device == "auto":
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"

    audio_path = _extract_audio(video_path)
    if audio_path is None:
        return None

    if engine == "funasr":
        return _transcribe_funasr(audio_path, srt_path, device)
    return _transcribe_whisper(audio_path, srt_path, model_size, device, compute_type)
