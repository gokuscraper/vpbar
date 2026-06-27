import pytest


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
