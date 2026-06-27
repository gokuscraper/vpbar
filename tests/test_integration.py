"""Integration tests — run ffmpeg with real media files."""

import shutil
import subprocess
from pathlib import Path

import pytest

from vpbar.cli import main

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not found"),
]


def _ffprobe_duration(path: str) -> str:
    result = subprocess.run(
        ["ffprobe", "-v", "error",
         "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1",
         path],
        capture_output=True, text=True,
    )
    return result.stdout.strip()


class TestProgressAdd:
    def test_basic(self, test_video, tmp_path):
        out = tmp_path / "out.mp4"
        rc = main(["progress", "add", test_video, "-o", str(out)])
        assert rc == 0
        assert out.exists()
        assert out.stat().st_size > 100_000
        dur = _ffprobe_duration(str(out))
        assert dur != ""

    def test_with_style(self, test_video, tmp_path):
        out = tmp_path / "out.mp4"
        rc = main([
            "progress", "add", test_video, "-o", str(out),
            "--bg-color", "000000", "--fg-color", "00FF00",
            "--corner-radius", "10", "--height", "30",
            "--position", "top",
        ])
        assert rc == 0
        assert out.exists()
        assert out.stat().st_size > 100_000

    def test_with_gradient(self, test_video, tmp_path):
        out = tmp_path / "out.mp4"
        rc = main([
            "progress", "add", test_video, "-o", str(out),
            "--gradient", "FF0000,00FF00,0000FF",
        ])
        assert rc == 0
        assert out.exists()
        assert out.stat().st_size > 100_000

    def test_with_chapters(self, test_video, tmp_path):
        out = tmp_path / "out.mp4"
        rc = main([
            "progress", "add", test_video, "-o", str(out),
            "--chapters", "0-60:Intro,60-120:Middle,120-175:End",
            "--divider-width", "2",
        ])
        assert rc == 0
        assert out.exists()
        assert out.stat().st_size > 100_000

    def test_with_scrubber(self, test_video, fixtures, tmp_path):
        out = tmp_path / "out.mp4"
        scrubber = fixtures / "scrubber.gif"
        rc = main([
            "progress", "add", test_video, "-o", str(out),
            "--scrubber-image", str(scrubber),
        ])
        assert rc == 0
        assert out.exists()
        assert out.stat().st_size > 100_000


class TestGifConvert:
    def test_basic(self, test_video, tmp_path):
        out = tmp_path / "out.gif"
        rc = main(["gif", "convert", test_video, str(out), "--height", "60"])
        assert rc == 0
        assert out.exists()
        assert out.stat().st_size > 1000
        from PIL import Image
        img = Image.open(str(out))
        assert img.n_frames >= 1

    def test_green_screen(self, green_video, tmp_path):
        out = tmp_path / "out.gif"
        rc = main([
            "gif", "convert", green_video, str(out),
            "--green-screen", "--green-threshold", "128",
        ])
        assert rc == 0
        assert out.exists()
        assert out.stat().st_size > 1000
        from PIL import Image
        img = Image.open(str(out))
        assert img.n_frames >= 1
