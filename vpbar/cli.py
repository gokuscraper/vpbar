"""CLI entry point with subcommand dispatch."""

import argparse
import importlib.metadata
import logging
import sys
from pathlib import Path

from vpbar.chapters import parse_chapters
from vpbar.config import load_styles, merge_with_style
from vpbar.gif import convert_video_to_gif
from vpbar.progress import add_progress_bar

logger = logging.getLogger("vpbar")


# ── Helpers ──────────────────────────────────────────────────────────────

def _get_version() -> str:
    try:
        return importlib.metadata.version("vpbar")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"


def _setup_logging(args: argparse.Namespace) -> None:
    if args.quiet:
        level = logging.WARNING
    elif args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level, format="%(message)s", stream=sys.stderr)


# ── Custom argument types ────────────────────────────────────────────────

def hex_color(s: str) -> str:
    s = s.lstrip("#")
    if len(s) != 6 or not all(c in "0123456789ABCDEFabcdef" for c in s):
        raise argparse.ArgumentTypeError(f"invalid hex color value: '{s}'")
    return s.upper()


def gradient_list(s: str) -> list[str]:
    colors = [hex_color(c.strip()) for c in s.split(",")]
    if len(colors) < 2:
        raise argparse.ArgumentTypeError("gradient requires at least 2 colors")
    return colors


def existing_file(s: str) -> str:
    if not Path(s).exists():
        raise argparse.ArgumentTypeError(f"file not found: '{s}'")
    return s


# ── Parser construction ──────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vpbar",
        description="Video Progress Bar CLI — Add progress bars to videos and convert to GIF.",
    )
    parser.add_argument(
        "--version", action="version",
        version=f"vpbar {_get_version()}",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Verbose output (debug level)",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Suppress non-error output",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # ── transcribe ──────────────────────────────────────────────────
    p = sub.add_parser("transcribe", help="Transcribe video audio to SRT")
    p.add_argument("input", type=existing_file, help="Input video file")
    p.add_argument("-o", "--output", type=str, default=None,
                   help="Output SRT path (default: input.srt)")
    p.add_argument("--engine", choices=["whisper", "funasr"], default="whisper",
                   help="Transcription engine (default: whisper)")
    p.add_argument("--model", type=str, default="large-v3-turbo",
                   help="Whisper model size (whisper engine)")
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto",
                   help="Device to run on")
    p.add_argument("--compute-type", choices=["default", "float16", "int8"],
                   default="default", help="Compute type")

    # ── chapters ────────────────────────────────────────────────────
    p = sub.add_parser("chapters", help="Chapter operations")
    sub2 = p.add_subparsers(dest="action", required=True)
    p2 = sub2.add_parser("generate", help="Generate chapters from SRT using AI")
    p2.add_argument("--srt", type=existing_file, required=True,
                    help="SRT subtitle file path")
    p2.add_argument("-o", "--output", type=str, default=None,
                    help="Save chapters to file")
    p2.add_argument("--min-chapters", type=int, default=2,
                    help="Minimum chapters")
    p2.add_argument("--max-chapters", type=int, default=4,
                    help="Maximum chapters")
    p2.add_argument("--max-label-length", type=int, default=7,
                    help="Max label characters")

    # ── progress ────────────────────────────────────────────────────
    p = sub.add_parser("progress", help="Progress bar operations")
    sub2 = p.add_subparsers(dest="action", required=True)
    p2 = sub2.add_parser("add", help="Add progress bar to video")

    io = p2.add_argument_group("Input/Output")
    io.add_argument("input", type=existing_file, help="Input video file")
    io.add_argument("-o", "--output", type=str, default=None,
                    help="Output video path (default: input_with_progress.ext)")

    style = p2.add_argument_group("Style Options")
    style.add_argument("--style", type=str, default=None,
                       help="Style name from styles.json")
    style.add_argument("-p", "--position", choices=["top", "middle", "bottom"],
                       default=None, help="Progress bar position")
    style.add_argument("--height", type=int, default=None,
                       help="Progress bar height")
    style.add_argument("--bg-color", type=hex_color, default=None,
                       help="Background hex color")
    style.add_argument("--fg-color", type=hex_color, default=None,
                       help="Foreground hex color")
    style.add_argument("--bg-alpha", type=float, default=None,
                       help="Background opacity 0-1")
    style.add_argument("--fg-alpha", type=float, default=None,
                       help="Foreground opacity 0-1")
    style.add_argument("--corner-radius", type=int, default=None,
                       help="Corner radius in pixels")

    ch = p2.add_argument_group("Chapter Options")
    ch.add_argument("--chapters", type=str, default=None,
                    help="Chapters: '0-6:Intro,6-11:结尾'")
    ch.add_argument("--divider-width", type=int, default=3,
                    help="Divider line width")
    ch.add_argument("--divider-height-ratio", type=float, default=0.8,
                    help="Divider height ratio (0-1)")
    ch.add_argument("--gradient", type=gradient_list, default=None,
                    help="Gradient colors: 'FF0000,00FF00,0000FF'")
    ch.add_argument("--srt", type=str, default=None,
                    help="SRT subtitle file for auto-chaptering")
    ch.add_argument("--transcribe", type=str, default=None, const="large-v3-turbo",
                    nargs="?",
                    help="Transcribe first (optional: model size, default: large-v3-turbo)")
    ch.add_argument("--engine", choices=["whisper", "funasr"], default="whisper",
                    help="Transcription engine for --transcribe")

    adv = p2.add_argument_group("Advanced Options")
    adv.add_argument("--segment-interval", type=int, default=0,
                     help="Segment interval in seconds (0=auto)")
    adv.add_argument("--scrubber-image", type=existing_file, default=None,
                     help="Path to scrubber GIF")

    # ── gif ─────────────────────────────────────────────────────────
    p = sub.add_parser("gif", help="GIF operations")
    sub2 = p.add_subparsers(dest="action", required=True)
    p2 = sub2.add_parser("convert", help="Convert video to GIF")
    p2.add_argument("input", type=existing_file, help="Input video file")
    p2.add_argument("output", type=str, help="Output GIF file")
    p2.add_argument("--height", type=int, default=60, help="GIF height")
    p2.add_argument("--green-screen", action="store_true",
                    help="Remove green screen")
    p2.add_argument("--green-threshold", type=int, default=150,
                    help="Green threshold (0-255)")

    return parser


# ── Post-parse validation ────────────────────────────────────────────────

def validate_options(args: argparse.Namespace) -> None:
    if args.command == "progress" and args.action == "add":
        for name in ("bg_alpha", "fg_alpha"):
            val = getattr(args, name, None)
            if val is not None and not (0 <= val <= 1):
                raise argparse.ArgumentTypeError(
                    f"--{name.replace('_', '-')} must be between 0 and 1")
        if not (0 < args.divider_height_ratio <= 1):
            raise argparse.ArgumentTypeError(
                "--divider-height-ratio must be between 0 and 1")
        if args.segment_interval < 0:
            raise argparse.ArgumentTypeError(
                "--segment-interval must be >= 0")
        if args.corner_radius is not None and args.corner_radius < 0:
            raise argparse.ArgumentTypeError(
                "--corner-radius must be >= 0")
        if args.srt is not None and not Path(args.srt).exists():
            raise argparse.ArgumentTypeError(
                f"SRT file not found: '{args.srt}'")

    elif args.command == "gif" and args.action == "convert":
        if not (0 <= args.green_threshold <= 255):
            raise argparse.ArgumentTypeError(
                "--green-threshold must be between 0 and 255")
        if args.height <= 0:
            raise argparse.ArgumentTypeError("--height must be positive")


# ── Command handlers ─────────────────────────────────────────────────────

def handle_transcribe(args: argparse.Namespace) -> int:
    from vpbar.transcribe import video_to_srt

    output = args.output or str(Path(args.input).with_suffix(".srt"))
    logger.info("Transcribing %s -> %s", args.input, output)
    success = video_to_srt(
        video_path=args.input,
        srt_path=output,
        model_size=args.model,
        device=args.device,
        compute_type=args.compute_type,
        engine=args.engine,
    )
    return 0 if success else 1


def handle_chapters(args: argparse.Namespace) -> int:
    from vpbar.chapters import generate_chapters_from_srt

    result = generate_chapters_from_srt(
        srt_path=args.srt,
        min_chapters=args.min_chapters,
        max_chapters=args.max_chapters,
        max_label_length=args.max_label_length,
    )
    if result is None:
        logger.error("Failed to generate chapters")
        return 1
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        logger.info("Chapters saved to: %s", args.output)
    else:
        print(result)
    return 0


def handle_progress(args: argparse.Namespace) -> int:
    styles_config = load_styles()
    style_name = args.style or styles_config.get("default_style", "默认")
    merged = merge_with_style(vars(args), style_name, styles_config)

    if args.transcribe:
        from vpbar.transcribe import video_to_srt
        temp_srt = str(Path(args.input).with_suffix(".srt"))
        video_to_srt(
            video_path=args.input,
            srt_path=temp_srt,
            model_size=args.transcribe,
            engine=args.engine,
        )
        args.srt = temp_srt

    chapters_str = args.chapters
    if chapters_str is None and args.srt:
        from vpbar.chapters import generate_chapters_from_srt
        result = generate_chapters_from_srt(srt_path=args.srt)
        if result:
            chapters_str = result
            logger.info("Auto-generated chapters: %s", result)
        else:
            logger.warning("Failed to auto-generate chapters, proceeding without")

    chapters = parse_chapters(chapters_str)
    gradient = args.gradient or merged.get("gradient")

    success = add_progress_bar(
        input_path=args.input,
        output_path=args.output,
        position=merged.get("position", "bottom"),
        height=merged.get("height", 5),
        bg_color=merged.get("bg_color", "808080"),
        fg_color=merged.get("fg_color", "FF0000"),
        bg_alpha=merged.get("bg_alpha", 1.0),
        fg_alpha=merged.get("fg_alpha", 1.0),
        segment_interval=args.segment_interval,
        corner_radius=merged.get("corner_radius", 0),
        chapters=chapters,
        divider_width=args.divider_width,
        divider_height_ratio=args.divider_height_ratio,
        gradient=gradient,
        scrubber_image=args.scrubber_image,
    )
    return 0 if success else 1


def handle_gif(args: argparse.Namespace) -> int:
    logger.info("Converting %s -> %s", args.input, args.output)
    success = convert_video_to_gif(
        input_path=args.input,
        output_path=args.output,
        height=args.height,
        green_screen=args.green_screen,
        green_threshold=args.green_threshold,
    )
    return 0 if success else 1


# ── Dispatch table ───────────────────────────────────────────────────────

COMMANDS = {
    "transcribe": handle_transcribe,
    "chapters": handle_chapters,
    "progress": handle_progress,
    "gif": handle_gif,
}


# ── Entry points ─────────────────────────────────────────────────────────

def _real_main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args)
    validate_options(args)
    handler = COMMANDS[args.command]
    return handler(args)


def main(argv: list[str] | None = None) -> int:
    try:
        return _real_main(argv)
    except argparse.ArgumentTypeError as e:
        logger.error(str(e))
        return 2
    except KeyboardInterrupt:
        logger.error("\nInterrupted by user")
        return 130
    except Exception:
        logger.exception("unexpected error")
        return 1


if __name__ == "__main__":
    sys.exit(main())
