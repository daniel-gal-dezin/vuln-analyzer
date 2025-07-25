#!/usr/bin/env python3
"""vuln-analyzer command-line interface.

Usage examples
--------------
Scan one file with defaults:
    python -m cli analyze notes.cpp

Specify model and token budget:
    python -m cli analyze notes.cpp -m models/phi-4.Q4_1.gguf -t 768

After you `pip install .`, the console-script entry point `vuln-analyzer` will
be available automatically (setup.cfg/pyproject configuration required).
"""

import argparse
import sys
from pathlib import Path

from llm_engine import LLMEngine

# -------------------------------------------------------------
# helpers
# -------------------------------------------------------------

def _positive_int(value: str) -> int:
    """argparse type: positive integer"""
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("value must be > 0")
    return ivalue

# -------------------------------------------------------------
# CLI definition
# -------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="vuln-analyzer",
                                description="LLM-powered C/C++ vulnerability scanner")

    sub = p.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("analyze", help="scan source file(s)")
    scan.add_argument("files", metavar="FILE", nargs="+",
                      help="one or more C/C++ source files to analyze")
    scan.add_argument("-m", "--model", default="models/phi-4-Q4_1.gguf",
                      help="path to GGUF model (default: %(default)s)")
    scan.add_argument("-t", "--tokens", type=_positive_int, default=512,
                      help="max tokens generated per block (default: %(default)s)")
    scan.add_argument("-j", "--threads", type=_positive_int, default=8,
                      help="CPU threads for ggml (default: %(default)s)")
    scan.add_argument("--ctx", type=_positive_int, default=4096,
                      help="model context window (default: %(default)s)")
    scan.add_argument("-v", "--verbose", action="store_true",
                      help="print raw model output for debugging")
    scan.add_argument("--nosplit", action="store_true",
                      help="do not split file into chunks")
    return p

# -------------------------------------------------------------
# command handlers
# -------------------------------------------------------------

def cmd_analyze(args: argparse.Namespace) -> None:
    # Instantiate engine once and reuse for all files
    engine = LLMEngine(model_path=args.model, n_ctx=args.ctx, n_threads=args.threads,
                       debug=args.verbose)

    ok = True
    for file_path in args.files:
        path = Path(file_path)
        if not path.exists():
            print(f"❌  File not found: {file_path}", file=sys.stderr)
            ok = False
            continue

        print(f"\n🔍  Analyzing {file_path}")
        try:
            report = engine.analyze_file(str(path), max_tokens=args.tokens, nosplit=args.nosplit)
            print("\n=== SCAN REPORT ===\n")
            print(report)
            print("\n" + "="*60 + "\n")
        except Exception as exc:  # broad catch to keep CLI alive
            ok = False
            print(f"❌  Error scanning {file_path}: {exc}", file=sys.stderr)

    if not ok:
        sys.exit(1)

# -------------------------------------------------------------
# entry point
# -------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "analyze":
        cmd_analyze(args)
    else:
        parser.error(f"Unknown command {args.command}")


if __name__ == "__main__":
    main() 