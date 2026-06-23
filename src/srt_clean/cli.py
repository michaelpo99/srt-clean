from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .models import CLIError, EXIT_CLI_ERROR, EXIT_OK, ProfileError, SRTCleanError, SRTParseError
from .parser import parse_srt_file
from .profile import list_builtin_profiles, load_profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="srt-clean",
        description="Rule-based SRT subtitle cleaner for ASR output.",
    )
    parser.add_argument("input", nargs="?", help="Input .srt path")
    parser.add_argument("--profile", help="Built-in profile name or YAML path")
    parser.add_argument("--mode", choices=["report", "clean", "apply"], default="clean")
    parser.add_argument(
        "--level",
        choices=["conservative", "moderate", "aggressive"],
        default="moderate",
    )
    parser.add_argument("--output", help="Explicit cleaned SRT output path")
    parser.add_argument("--report-output", help="Explicit report output path")
    parser.add_argument("--decisions", help="Decisions YAML for apply mode")
    parser.add_argument("--force", action="store_true", help="Overwrite existing outputs")
    parser.add_argument("--check", action="store_true", help="Validate input and profile only")
    parser.add_argument(
        "--list-profiles", action="store_true", help="List built-in profiles and exit"
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Not supported in P0. Preserve original input files instead.",
    )
    return parser


def run_check(input_path: str, profile_name: str) -> int:
    path = Path(input_path)
    if not path.exists():
        raise CLIError(f"input file not found: {path}")
    if path.suffix.lower() != ".srt":
        raise CLIError(f"input file must be .srt: {path}")

    profile = load_profile(profile_name)
    cues = parse_srt_file(path)
    print(f"check ok: input={path} profile={profile.profile} cues={len(cues)}")
    return EXIT_OK


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.in_place:
        raise CLIError("--in-place is not supported in P0")
    if args.list_profiles:
        for name in list_builtin_profiles():
            print(name)
        return EXIT_OK
    if args.check:
        if not args.profile:
            available = ", ".join(list_builtin_profiles())
            raise CLIError(f"--profile is required for P0. Available profiles: {available}")
        if not args.input:
            raise CLIError("input .srt is required with --check")
        return run_check(args.input, args.profile)

    raise CLIError(
        "clean/report/apply pipeline is not implemented in Batch A yet. "
        "Use --help, --list-profiles, or --check."
    )


def main(argv: list[str] | None = None) -> int:
    try:
        return run(argv)
    except (CLIError, SRTParseError, ProfileError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code
    except SRTCleanError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_CLI_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
