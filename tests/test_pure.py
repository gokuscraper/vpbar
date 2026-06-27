"""Pure function tests — no I/O, no mocking needed."""

import pytest

from vpbar.image import _parse_hex
from vpbar.transcribe import _seconds_to_srt_time
from vpbar.scrubber import calculate_loop_count
from vpbar.chapters import parse_chapters
from vpbar.llm import parse_llm_json
from vpbar.config import merge_with_style
from vpbar.srt import parse_srt


class TestParseHex:
    def test_rgb(self):
        assert _parse_hex("FF0000") == (255, 0, 0)

    def test_green(self):
        assert _parse_hex("00FF00") == (0, 255, 0)

    def test_blue(self):
        assert _parse_hex("0000FF") == (0, 0, 255)

    def test_with_hash(self):
        assert _parse_hex("#FFFFFF") == (255, 255, 255)

    def test_black(self):
        assert _parse_hex("000000") == (0, 0, 0)

    def test_invalid_chars(self):
        with pytest.raises(ValueError, match="Invalid hex color"):
            _parse_hex("GGGGGG")

    def test_too_short(self):
        with pytest.raises(ValueError, match="must be 6 hex digits"):
            _parse_hex("FFF")

    def test_too_long(self):
        with pytest.raises(ValueError, match="must be 6 hex digits"):
            _parse_hex("FFFFFFFF")

    def test_empty(self):
        with pytest.raises(ValueError, match="must be 6 hex digits"):
            _parse_hex("")


class TestSecondsToSrtTime:
    def test_zero(self):
        assert _seconds_to_srt_time(0) == "00:00:00,000"

    def test_one_second(self):
        assert _seconds_to_srt_time(1) == "00:00:01,000"

    def test_one_minute(self):
        assert _seconds_to_srt_time(60) == "00:01:00,000"

    def test_one_hour(self):
        assert _seconds_to_srt_time(3600) == "01:00:00,000"

    def test_complex(self):
        assert _seconds_to_srt_time(3725.123) == "01:02:05,123"

    def test_rounding(self):
        assert _seconds_to_srt_time(0.001) == "00:00:00,001"

    def test_no_decimal(self):
        assert _seconds_to_srt_time(5) == "00:00:05,000"


class TestCalculateLoopCount:
    def test_exact(self):
        assert calculate_loop_count(5, 15) == 2

    def test_overflow(self):
        assert calculate_loop_count(10, 25) == 2

    def test_under_one(self):
        assert calculate_loop_count(5, 4) == 0

    def test_exact_one(self):
        assert calculate_loop_count(10, 10) == 0

    def test_zero_duration_fallback(self):
        assert calculate_loop_count(0, 10) == 100

    def test_negative_duration_fallback(self):
        assert calculate_loop_count(-1, 10) == 100

    def test_zero_video(self):
        assert calculate_loop_count(5, 0) == 0

    def test_large_values(self):
        assert calculate_loop_count(2, 1000) == 499


class TestParseChapters:
    def test_simple(self):
        result = parse_chapters("0-6:Intro,6-11:结尾")
        assert result == [
            {"start": 0, "end": 6, "label": "Intro"},
            {"start": 6, "end": 11, "label": "结尾"},
        ]

    def test_none(self):
        assert parse_chapters(None) is None

    def test_empty_string(self):
        assert parse_chapters("") is None

    def test_single_chapter(self):
        result = parse_chapters("0-10:Intro")
        assert result == [{"start": 0, "end": 10, "label": "Intro"}]

    def test_float_timestamps(self):
        result = parse_chapters("0.5-6.3:Part1")
        assert result == [{"start": 0.5, "end": 6.3, "label": "Part1"}]

    def test_commas_in_label_unsupported(self):
        result = parse_chapters('0-5:A,B')
        assert result is not None
        assert len(result) == 1


class TestParseLlmJson:
    def test_valid(self):
        data = '[{"start":0,"end":10,"label":"Intro"}]'
        assert parse_llm_json(data) == [{"start": 0, "end": 10, "label": "Intro"}]

    def test_multiple(self):
        data = (
            '[{"start":0,"end":5,"label":"A"},'
            '{"start":5,"end":10,"label":"B"}]'
        )
        result = parse_llm_json(data)
        assert len(result) == 2
        assert result[0]["label"] == "A"
        assert result[1]["label"] == "B"

    def test_with_markdown_fence(self):
        data = '```json\n[{"start":0,"end":10,"label":"Intro"}]\n```'
        assert parse_llm_json(data) == [{"start": 0, "end": 10, "label": "Intro"}]

    def test_with_markdown_no_lang(self):
        data = '```\n[{"start":0,"end":10,"label":"Intro"}]\n```'
        assert parse_llm_json(data) == [{"start": 0, "end": 10, "label": "Intro"}]

    def test_not_json(self):
        assert parse_llm_json("not json at all") is None

    def test_not_a_list(self):
        assert parse_llm_json('{"key": "value"}') is None

    def test_missing_keys(self):
        assert parse_llm_json('[{"start":0,"end":10}]') is None

    def test_bad_types(self):
        assert parse_llm_json('[{"start":"a","end":10,"label":"X"}]') is None

    def test_start_gte_end(self):
        assert parse_llm_json('[{"start":10,"end":5,"label":"X"}]') is None


class TestMergeWithStyle:
    @pytest.fixture
    def styles(self):
        return {
            "styles": {
                "默认": {
                    "height": 50, "bg_color": "808080", "fg_color": "FF0000",
                    "bg_alpha": 1.0, "fg_alpha": 1.0, "position": "bottom",
                    "corner_radius": 0,
                },
            },
            "default_style": "默认",
        }

    def test_cli_overrides_style(self, styles):
        result = merge_with_style({"height": 100}, "默认", styles)
        assert result["height"] == 100

    def test_style_fills_default(self, styles):
        result = merge_with_style({}, "默认", styles)
        assert result["height"] == 50
        assert result["bg_color"] == "808080"

    def test_cli_none_uses_style(self, styles):
        result = merge_with_style({"height": None}, "默认", styles)
        assert result["height"] == 50

    def test_missing_style_uses_hard_defaults(self):
        result = merge_with_style({}, "不存在", {"styles": {}, "default_style": "不存在"})
        assert result["height"] == 50
        assert result["position"] == "bottom"

    def test_gradient_from_cli(self, styles):
        result = merge_with_style({"gradient": ["FF0000", "00FF00"]}, "默认", styles)
        assert result["gradient"] == ["FF0000", "00FF00"]

    def test_gradient_from_style(self, styles):
        styles["styles"]["默认"]["gradient"] = ["0000FF", "FF0000"]
        result = merge_with_style({"gradient": None}, "默认", styles)
        assert result["gradient"] == ["0000FF", "FF0000"]

    def test_no_gradient(self, styles):
        result = merge_with_style({}, "默认", styles)
        assert "gradient" not in result


class TestParseSrt:
    def test_valid(self, sample_srt):
        entries, duration = parse_srt(sample_srt)
        assert len(entries) == 3
        assert duration == 15.0
        assert entries[0]["text"] == "Hello everyone"
        assert entries[0]["start_sec"] == 0.0
        assert entries[0]["end_sec"] == 5.0

    def test_empty(self, tmp_path):
        path = tmp_path / "empty.srt"
        path.write_text("")
        with pytest.raises(ValueError, match="No valid SRT entries"):
            parse_srt(str(path))

    def test_garbage(self, tmp_path):
        path = tmp_path / "garbage.srt"
        path.write_text("this is not srt content\nat all\n")
        with pytest.raises(ValueError, match="No valid SRT entries"):
            parse_srt(str(path))

    def test_comma_vs_dot(self, sample_srt):
        path = sample_srt
        content = open(path, encoding="utf-8-sig").read().replace(",", ".")
        path2 = path.replace(".srt", "_dot.srt")
        with open(path2, "w", encoding="utf-8") as f:
            f.write(content)
        entries, duration = parse_srt(path2)
        assert len(entries) == 3
