#!/usr/bin/env python3
"""Reproducible, filtered, manifest-driven packager for AI review."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import sys
import time
import zipfile
from pathlib import Path

DEFAULT_INCLUDES = [
    "README.md",
    "PROJECT_DOCUMENTATION.md",
    "PRO_DOCS.md",
    "Makefile",
    "docs/**",
    "official_docs/**",
    "scripts/**",
    "config/**",
    "agents/**",
    "strategies/**",
    "user_data/learning_log.csv",
    "user_data/ml_trades_book.csv",
    "user_data/verified_strategies/**",
]
DEFAULT_EXCLUDES = [
    ".git/**",
    ".github/**",
    ".venv/**",
    "__pycache__/**",
    "*.pyc",
    "*.pyo",
    "*.log",
    "*.tmp",
    "*.bak",
    "*.DS_Store",
    "runs/**",
    "data/**",
    "user_data/data/**",
    "user_data/logs/**",
    "user_data/hyperopt_results/**",
    "config/agent_config.yaml",
]
DEFAULT_MAX_MB = 20
DEFAULT_OUTPUT = "hf_battle_ai_review_package.zip"
REPRO_TS = (2025, 1, 1, 0, 0, 0)


def _match_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pat) for pat in patterns)


def iter_candidates(root: Path, includes: list[str]) -> list[Path]:
    files: list[Path] = []
    for pat in includes:
        for p in root.glob(pat):
            if p.is_file():
                files.append(p)
            elif p.is_dir():
                files.extend(q for q in p.rglob("*") if q.is_file())
    return sorted(set(files), key=lambda p: str(p).lower())


def make_zip(
    output: Path,
    root: Path,
    includes: list[str],
    excludes: list[str],
    max_mb: int,
    dry_run: bool,
    reproducible: bool,
) -> dict:
    root = root.resolve()
    selected = []
    skipped = []
    candidates = iter_candidates(root, includes)
    for f in candidates:
        rel = f.relative_to(root).as_posix()
        if _match_any(rel, excludes):
            skipped.append({"path": rel, "reason": "excluded"})
            continue
        size = f.stat().st_size
        if size == 0:
            skipped.append({"path": rel, "reason": "zero-bytes"})
            continue
        if max_mb and size > max_mb * 1024 * 1024:
            skipped.append({"path": rel, "reason": f">{max_mb}MB"})
            continue
        selected.append((f, rel, size))
    manifest = []
    if dry_run:
        return {
            "would_include": [{"path": r, "size": s} for _, r, s in selected],
            "skipped": skipped,
            "output": str(output),
        }
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f, rel, size in selected:
            data = f.read_bytes()
            sha = hashlib.sha1(data).hexdigest()
            if reproducible:
                info = zipfile.ZipInfo(rel, date_time=REPRO_TS)
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, data)
            else:
                zf.writestr(rel, data, compress_type=zipfile.ZIP_DEFLATED)
            manifest.append({"path": rel, "size": size, "sha1": sha})
        man_data = json.dumps(
            {
                "created_utc": int(time.time()),
                "root": str(root),
                "count": len(manifest),
                "max_mb": max_mb,
                "includes": includes,
                "excludes": excludes,
                "files": manifest,
            },
            indent=2,
        ).encode()
        if reproducible:
            info = zipfile.ZipInfo("manifest.json", date_time=REPRO_TS)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, man_data)
        else:
            zf.writestr("manifest.json", man_data, compress_type=zipfile.ZIP_DEFLATED)
    return {"included": manifest, "skipped": skipped, "output": str(output)}


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="Package project for AI review")
    ap.add_argument("--root", default=".", help="Project root")
    ap.add_argument("-o", "--output", default=DEFAULT_OUTPUT, help="Output zip path")
    ap.add_argument("--include", action="append", default=[], help="Extra include glob")
    ap.add_argument("--exclude", action="append", default=[], help="Extra exclude glob")
    ap.add_argument(
        "--max-mb", type=int, default=DEFAULT_MAX_MB, help="Max file size to include"
    )
    ap.add_argument(
        "--dry-run", action="store_true", help="Only list what would be included"
    )
    ap.add_argument("--reproducible", action="store_true", help="Use fixed timestamps")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    root = Path(args.root)
    includes = DEFAULT_INCLUDES + args.include
    excludes = DEFAULT_EXCLUDES + args.exclude
    result = make_zip(
        output=Path(args.output),
        root=root,
        includes=includes,
        excludes=excludes,
        max_mb=args.max_mb,
        dry_run=args.dry_run,
        reproducible=args.reproducible,
    )
    print(json.dumps(result, indent=2)[:20000])


if __name__ == "__main__":
    sys.exit(main())
