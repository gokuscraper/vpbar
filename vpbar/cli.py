"""CLI entry point with subcommand dispatch."""

import argparse
import sys

from vpbar.config import load_config, load_styles, merge_with_style
from vpbar.chapters import parse_chapters
from vpbar.progress import add_progress_bar
from vpbar.gif import convert_video_to_gif


def build_progress_subparser(subparsers):
    parser = subparsers.add_parser("progress", help="Progress bar operations")
    sub = parser.add_subparsers(dest="action", required=True)
    add_parser = sub.add_parser("add", help="Add progress bar to video")
    add_parser.add_argument("input", type=str, help="Path to input video file")
    add_parser.add_argument("-o", "--output", type=str, default=None,
                            help="Output video path (default: input_with_progress.ext)")
    add_parser.add_argument("--style", type=str, default=None,
                            help="Style name from styles.json")
    add_parser.add_argument("-p", "--position", type=str, choices=["top", "middle", "bottom"],
                            default=None, help="Progress bar position")
    add_parser.add_argument("--height", type=int, default=None, help="Progress bar height")
    add_parser.add_argument("--bg-color", type=str, default=None, help="Background hex color")
    add_parser.add_argument("--fg-color", type=str, default=None, help="Foreground hex color")
    add_parser.add_argument("--bg-alpha", type=float, default=None, help="Background opacity 0-1")
    add_parser.add_argument("--fg-alpha", type=float, default=None, help="Foreground opacity 0-1")
    add_parser.add_argument("--segment-interval", type=int, default=1, help="Segment interval in seconds")
    add_parser.add_argument("--corner-radius", type=int, default=None, help="Corner radius in pixels")
    add_parser.add_argument("--chapters", type=str, default=None,
                            help="Chapters: '0-6:Intro,6-11:结尾'")
    add_parser.add_argument("--divider-width", type=int, default=3, help="Divider line width")
    add_parser.add_argument("--divider-height-ratio", type=float, default=0.8,
                            help="Divider height ratio")
    add_parser.add_argument("--gradient", type=str, default=None,
                            help="Gradient colors: 'FF0000,00FF00,0000FF'")
    add_parser.add_argument("--scrubber-image", type=str, default=None,
                            help="Path to scrubber GIF")
    return add_parser


def build_gif_subparser(subparsers):
    parser = subparsers.add_parser("gif", help="GIF operations")
    sub = parser.add_subparsers(dest="action", required=True)
    convert_parser = sub.add_parser("convert", help="Convert video to GIF")
    convert_parser.add_argument("input", type=str, help="Input video file")
    convert_parser.add_argument("output", type=str, help="Output GIF file")
    convert_parser.add_argument("--height", type=int, default=60, help="GIF height")
    convert_parser.add_argument("--green-screen", action="store_true", help="Remove green screen")
    convert_parser.add_argument("--green-threshold", type=int, default=150, help="Green threshold")
    return convert_parser


def main():
    parser = argparse.ArgumentParser(
        prog="vpbar",
        description="Video Progress Bar CLI Tool - Add progress bars to videos and convert to GIF."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_progress_subparser(subparsers)
    build_gif_subparser(subparsers)
    args = parser.parse_args()

    if args.command == "progress":
        if args.action == "add":
            styles_config = load_styles()
            style_name = args.style or styles_config.get("default_style", "默认")
            merged = merge_with_style(vars(args), style_name, styles_config)
            chapters = parse_chapters(args.chapters)
            gradient = None
            if args.gradient:
                gradient = [c.strip() for c in args.gradient.split(',')]
            elif "gradient" in merged:
                gradient = merged["gradient"]
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
                scrubber_image=args.scrubber_image
            )
            sys.exit(0 if success else 1)

    elif args.command == "gif":
        if args.action == "convert":
            success = convert_video_to_gif(
                input_path=args.input,
                output_path=args.output,
                height=args.height,
                green_screen=args.green_screen,
                green_threshold=args.green_threshold
            )
            sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
