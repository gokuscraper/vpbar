from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--integration", action="store_true", default=False,
        help="run integration tests (ffmpeg required)",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: tests that run ffmpeg with real media files (opt-in with --integration)",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--integration"):
        skip = pytest.mark.skip(reason="use --integration to run")
        for item in items:
            if item.get_closest_marker("integration"):
                item.add_marker(skip)


@pytest.fixture
def sample_srt(tmp_path):
    content = (
        "1\n"
        "00:00:00,000 --> 00:00:05,000\n"
        "Hello everyone\n\n"
        "2\n"
        "00:00:05,000 --> 00:00:10,000\n"
        "Welcome to this video\n\n"
        "3\n"
        "00:00:10,000 --> 00:00:15,000\n"
        "Today we will talk about testing\n"
    )
    path = tmp_path / "test.srt"
    path.write_text(content, encoding="utf-8")
    return str(path)


@pytest.fixture
def sample_video(tmp_path):
    path = tmp_path / "test.mp4"
    path.write_text("fake video content")
    return str(path)


@pytest.fixture
def fixtures() -> Path:
    """Directory containing real fixture media files."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def test_video(fixtures) -> str:
    """test.mp4 — 175s, has audio, primary integration test video."""
    return str(fixtures / "test.mp4")


@pytest.fixture
def green_video(fixtures) -> str:
    """green.mp4 — 10s, green screen only, no audio."""
    return str(fixtures / "green.mp4")
