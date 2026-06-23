from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .actions import resolve_actions
from .decisions import build_decisions_document, write_decisions_file
from .models import CLIError, EXIT_GENERAL_ERROR, EXIT_OK, ProfileError, SRTCleanError, SRTParseError
from .normalize import normalize_cues
from .parser import parse_srt_file
from .profile import list_builtin_profiles, load_profile
from .report import build_report_text
from .rules import evaluate_rules
from .writer import write_srt_file


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


def default_clean_output_path(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}.cleaned.srt")


def default_report_output_path(input_path: Path, *, mode: str) -> Path:
    suffix = ".apply-report.txt" if mode == "apply" else ".clean-report.txt"
    return input_path.with_name(f"{input_path.stem}{suffix}")


def default_decisions_output_path(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}.clean-decisions.yml")


def ensure_output_paths(paths: list[Path], *, force: bool) -> None:
    if force:
        return
    for path in paths:
        if path.exists():
            raise CLIError(
                f"output already exists: {path}. Use --force or set --output / --report-output."
            )


def run_pipeline(args: argparse.Namespace) -> int:
    if args.mode == "apply":
        raise CLIError("--mode apply is not implemented yet")
    if not args.profile:
        available = ", ".join(list_builtin_profiles())
        raise CLIError(f"--profile is required for P0. Available profiles: {available}")
    if not args.input:
        raise CLIError("input .srt is required")

    input_path = Path(args.input)
    if not input_path.exists():
        raise CLIError(f"input file not found: {input_path}")
    if input_path.suffix.lower() != ".srt":
        raise CLIError(f"input file must be .srt: {input_path}")

    profile = load_profile(args.profile)
    cues = parse_srt_file(input_path)
    normalized = normalize_cues(cues, profile.text_normalization)
    matches = evaluate_rules(cues, normalized, profile)
    result = resolve_actions(
        cues=cues,
        normalized_cues=normalized,
        profile=profile,
        matches=matches,
        mode=args.mode,
        level=args.level,
    )

    report_path = Path(args.report_output) if args.report_output else default_report_output_path(
        input_path, mode=args.mode
    )
    if args.mode == "clean":
        clean_path = Path(args.output) if args.output else default_clean_output_path(input_path)
        ensure_output_paths([clean_path, report_path], force=args.force)
        write_srt_file(clean_path, result.cleaned_cues)
    else:
        clean_path = None
        decisions_path = default_decisions_output_path(input_path)
        ensure_output_paths([report_path, decisions_path], force=args.force)
        decisions_document = build_decisions_document(
            input_path=input_path,
            profile_name=profile.profile,
            decisions=result.decisions,
        )
        write_decisions_file(decisions_path, decisions_document)

    report_text = build_report_text(
        source_path=input_path,
        profile_name=profile.profile,
        mode=args.mode,
        level=args.level,
        total_cues=len(cues),
        cleaned_cues=result.cleaned_cues,
        decisions=result.decisions,
    )
    report_path.write_text(report_text, encoding="utf-8")

    if clean_path is not None:
        print(f"wrote cleaned srt: {clean_path}")
    print(f"wrote report: {report_path}")
    if args.mode == "report":
        print(f"wrote decisions: {default_decisions_output_path(input_path)}")
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
    return run_pipeline(args)


def main(argv: list[str] | None = None) -> int:
    try:
        return run(argv)
    except (CLIError, SRTParseError, ProfileError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code
    except SRTCleanError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_GENERAL_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
