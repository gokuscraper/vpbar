"""CLI tests — argument parsing, dispatch, error handling."""

import argparse
import sys

import pytest

from vpbar.cli import (
    main,
    hex_color,
    gradient_list,
    existing_file,
    validate_options,
    _get_version,
)


class TestCustomTypes:
    def test_hex_color_ff0000(self):
        assert hex_color("FF0000") == "FF0000"

    def test_hex_color_lowercase(self):
        assert hex_color("ff0000") == "FF0000"

    def test_hex_color_with_hash(self):
        assert hex_color("#FF0000") == "FF0000"

    def test_hex_color_mixed_case(self):
        assert hex_color("#aA00fF") == "AA00FF"

    def test_hex_color_invalid(self):
        with pytest.raises(argparse.ArgumentTypeError, match="invalid hex color"):
            hex_color("notacolor")

    def test_hex_color_short(self):
        with pytest.raises(argparse.ArgumentTypeError, match="invalid hex color"):
            hex_color("FFF")

    def test_hex_color_5_chars(self):
        with pytest.raises(argparse.ArgumentTypeError, match="invalid hex color"):
            hex_color("FFFFF")

    def test_gradient_two_colors(self):
        assert gradient_list("FF0000,00FF00") == ["FF0000", "00FF00"]

    def test_gradient_three_colors(self):
        assert gradient_list("#FF0000,#00FF00,#0000FF") == ["FF0000", "00FF00", "0000FF"]

    def test_gradient_too_few(self):
        with pytest.raises(argparse.ArgumentTypeError, match="at least 2 colors"):
            gradient_list("FF0000")

    def test_gradient_invalid_color(self):
        with pytest.raises(argparse.ArgumentTypeError, match="invalid hex color"):
            gradient_list("FF0000,notacolor")

    def test_existing_file_ok(self, tmp_path):
        p = tmp_path / "exists.txt"
        p.write_text("hello")
        assert existing_file(str(p)) == str(p)

    def test_existing_file_not_found(self):
        with pytest.raises(argparse.ArgumentTypeError, match="file not found"):
            existing_file(r"C:\nonexistent_path_xyz\file.txt")


class TestHelpAndVersion:
    def test_help(self, capsys):
        with pytest.raises(SystemExit):
            main(["--help"])
        out = capsys.readouterr().out
        assert "transcribe" in out
        assert "chapters" in out
        assert "progress" in out
        assert "gif" in out
        assert "--version" in out
        assert "-v" in out or "--verbose" in out

    def test_version(self, capsys):
        with pytest.raises(SystemExit):
            main(["--version"])
        assert "vpbar 0.1.0" in capsys.readouterr().out

    def test_progress_add_help(self, capsys):
        with pytest.raises(SystemExit):
            main(["progress", "add", "--help"])
        out = capsys.readouterr().out
        assert "Style Options" in out
        assert "Chapter Options" in out
        assert "Advanced Options" in out

    def test_transcribe_help(self, capsys):
        with pytest.raises(SystemExit):
            main(["transcribe", "--help"])
        assert "--engine" in capsys.readouterr().out

    def test_gif_help(self, capsys):
        with pytest.raises(SystemExit):
            main(["gif", "convert", "--help"])
        assert "--green-screen" in capsys.readouterr().out

    def test_chapters_help(self, capsys):
        with pytest.raises(SystemExit):
            main(["chapters", "generate", "--help"])
        assert "--srt" in capsys.readouterr().out


class TestHandlers:
    def test_transcribe_success(self, mocker, sample_video):
        mock = mocker.patch("vpbar.transcribe.video_to_srt", return_value=True)
        rc = main(["transcribe", sample_video, "-o", sample_video + ".srt",
                    "--model", "tiny", "--device", "cpu"])
        assert rc == 0
        mock.assert_called_once_with(
            video_path=sample_video,
            srt_path=sample_video + ".srt",
            model_size="tiny",
            device="cpu",
            compute_type="default",
            engine="whisper",
        )

    def test_transcribe_failure(self, mocker, sample_video):
        mocker.patch("vpbar.transcribe.video_to_srt", return_value=False)
        rc = main(["transcribe", sample_video])
        assert rc == 1

    def test_chapters_success_stdout(self, mocker, sample_srt):
        mock = mocker.patch(
            "vpbar.chapters.generate_chapters_from_srt",
            return_value="0-5:A,5-10:B",
        )
        rc = main(["chapters", "generate", "--srt", sample_srt,
                    "--min-chapters", "2", "--max-chapters", "3"])
        assert rc == 0
        mock.assert_called_once_with(
            srt_path=sample_srt, min_chapters=2,
            max_chapters=3, max_label_length=7,
        )

    def test_chapters_success_to_file(self, mocker, tmp_path, sample_srt):
        mocker.patch(
            "vpbar.chapters.generate_chapters_from_srt",
            return_value="0-5:A,5-10:B",
        )
        out = tmp_path / "out.txt"
        rc = main(["chapters", "generate", "--srt", sample_srt,
                    "-o", str(out)])
        assert rc == 0
        assert out.read_text(encoding="utf-8") == "0-5:A,5-10:B"

    def test_chapters_failure(self, mocker, sample_srt):
        mocker.patch("vpbar.chapters.generate_chapters_from_srt", return_value=None)
        rc = main(["chapters", "generate", "--srt", sample_srt])
        assert rc == 1

    def test_gif_success(self, mocker, sample_video, tmp_path):
        mock = mocker.patch("vpbar.cli.convert_video_to_gif", return_value=True)
        out = tmp_path / "out.gif"
        rc = main(["gif", "convert", sample_video, str(out)])
        assert rc == 0
        mock.assert_called_once_with(
            input_path=sample_video,
            output_path=str(out),
            height=60,
            green_screen=False,
            green_threshold=150,
        )

    def test_gif_failure(self, mocker, sample_video, tmp_path):
        mocker.patch("vpbar.cli.convert_video_to_gif", return_value=False)
        out = tmp_path / "out.gif"
        rc = main(["gif", "convert", sample_video, str(out)])
        assert rc == 1

    def test_progress_add_success(self, mocker, sample_video):
        mock = mocker.patch("vpbar.cli.add_progress_bar", return_value=True)
        rc = main(["progress", "add", sample_video,
                    "--style", "默认", "--height", "50"])
        assert rc == 0
        assert mock.called

    def test_progress_add_failure(self, mocker, sample_video):
        mocker.patch("vpbar.cli.add_progress_bar", return_value=False)
        rc = main(["progress", "add", sample_video])
        assert rc == 1


class TestErrorHandling:
    def test_missing_input_file(self):
        with pytest.raises(SystemExit) as exc:
            main(["transcribe", "nonexistent.mp4"])
        assert exc.value.code == 2

    def test_missing_srt_file(self):
        with pytest.raises(SystemExit) as exc:
            main(["chapters", "generate", "--srt", "nonexistent.srt"])
        assert exc.value.code == 2

    def test_missing_gif_input(self):
        with pytest.raises(SystemExit) as exc:
            main(["gif", "convert", "nonexistent.mp4", "out.gif"])
        assert exc.value.code == 2

    def test_missing_progress_input(self):
        with pytest.raises(SystemExit) as exc:
            main(["progress", "add", "nonexistent.mp4"])
        assert exc.value.code == 2

    def test_unknown_command(self):
        with pytest.raises(SystemExit) as exc:
            main(["unknowncmd"])
        assert exc.value.code == 2

    def test_no_command(self):
        with pytest.raises(SystemExit) as exc:
            main([])
        assert exc.value.code == 2

    def test_keyboard_interrupt(self, mocker, sample_video):
        mocker.patch("vpbar.transcribe.video_to_srt", side_effect=KeyboardInterrupt)
        rc = main(["transcribe", sample_video])
        assert rc == 130

    def test_unexpected_error(self, mocker, sample_video):
        mocker.patch("vpbar.transcribe.video_to_srt", side_effect=RuntimeError("boom"))
        rc = main(["transcribe", sample_video])
        assert rc == 1


class TestValidateOptions:
    def _make_args(self, **kwargs):
        defaults = dict(
            command="progress", action="add",
            bg_alpha=None, fg_alpha=None,
            divider_height_ratio=0.8,
            segment_interval=0, corner_radius=None,
            srt=None, scrubber_image=None,
        )
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)

    def test_bg_alpha_invalid(self):
        args = self._make_args(bg_alpha=1.5)
        with pytest.raises(argparse.ArgumentTypeError, match="bg-alpha"):
            validate_options(args)

    def test_fg_alpha_invalid(self):
        args = self._make_args(fg_alpha=-0.1)
        with pytest.raises(argparse.ArgumentTypeError, match="fg-alpha"):
            validate_options(args)

    def test_divider_height_ratio_zero(self):
        args = self._make_args(divider_height_ratio=0)
        with pytest.raises(argparse.ArgumentTypeError, match="divider-height-ratio"):
            validate_options(args)

    def test_divider_height_ratio_over_one(self):
        args = self._make_args(divider_height_ratio=1.5)
        with pytest.raises(argparse.ArgumentTypeError, match="divider-height-ratio"):
            validate_options(args)

    def test_segment_interval_negative(self):
        args = self._make_args(segment_interval=-1)
        with pytest.raises(argparse.ArgumentTypeError, match="segment-interval"):
            validate_options(args)

    def test_corner_radius_negative(self):
        args = self._make_args(corner_radius=-5)
        with pytest.raises(argparse.ArgumentTypeError, match="corner-radius"):
            validate_options(args)

    def test_srt_not_found(self):
        args = self._make_args(srt="nonexistent.srt")
        with pytest.raises(argparse.ArgumentTypeError, match="SRT file not found"):
            validate_options(args)

    def test_gif_green_threshold_invalid(self):
        args = argparse.Namespace(
            command="gif", action="convert",
            green_threshold=300, height=60,
        )
        with pytest.raises(argparse.ArgumentTypeError, match="green-threshold"):
            validate_options(args)

    def test_gif_height_non_positive(self):
        args = argparse.Namespace(
            command="gif", action="convert",
            green_threshold=128, height=0,
        )
        with pytest.raises(argparse.ArgumentTypeError, match="height"):
            validate_options(args)


class TestVersion:
    def test_get_version(self):
        v = _get_version()
        assert isinstance(v, str)
        assert v == "0.1.0"
