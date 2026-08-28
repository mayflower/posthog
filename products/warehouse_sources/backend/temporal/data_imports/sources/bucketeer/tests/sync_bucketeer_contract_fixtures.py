#!/usr/bin/env python3
"""Sync or check the Bucketeer contract fixtures against a sibling Bucketeer checkout.

Bucketeer owns the analytics export contract; this source consumes it. Keeping a copy of
Bucketeer's canonical fixtures here means a change to a Bucketeer response shape fails a
cheap local check rather than a production sync.

Reads only the local filesystem: no network, no credentials, no running services.

    python sync_bucketeer_contract_fixtures.py --bucketeer ../bucketeer --check
    python sync_bucketeer_contract_fixtures.py --bucketeer ../bucketeer
"""

from __future__ import annotations

import sys
import json
import argparse
import subprocess
from pathlib import Path

# Bucketeer's canonical fixture directory, relative to a Bucketeer checkout root.
SOURCE_DIR = Path("test/fixtures/analytics_export_v1")
FIXTURES = (
    "context.json",
    "feature_flags_page_1.json",
    "feature_flags_page_2.json",
    "segments.json",
    "experiments.json",
    "goals.json",
    "audit_logs.json",
    "code_references.json",
)
MANIFEST = "MANIFEST.json"

HERE = Path(__file__).resolve().parent
DEST_DIR = HERE / "fixtures"


def emit(message: str, *, error: bool = False) -> None:
    """This is a developer CLI, so its report goes to the terminal."""
    print(message, file=sys.stderr if error else sys.stdout)  # noqa: T201


def normalized(path: Path) -> object:
    """Parsed JSON, so formatting differences alone never report as drift."""
    return json.loads(path.read_text())


def bucketeer_commit(root: Path) -> str:
    """The Bucketeer commit the fixtures were copied from, recorded in the manifest.

    Best effort: a checkout without git history still syncs, it just cannot say from
    which commit.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucketeer", required=True, help="path to a Bucketeer checkout")
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift and exit non-zero instead of updating the fixtures",
    )
    args = parser.parse_args()

    source_dir = Path(args.bucketeer).expanduser().resolve() / SOURCE_DIR
    if not source_dir.is_dir():
        emit(f"error: {source_dir} does not exist. Is --bucketeer a Bucketeer checkout?", error=True)
        return 2

    DEST_DIR.mkdir(parents=True, exist_ok=True)
    drift: list[str] = []

    for name in FIXTURES:
        source = source_dir / name
        if not source.is_file():
            drift.append(f"{name}: missing from the Bucketeer checkout")
            continue
        dest = DEST_DIR / name

        if args.check:
            if not dest.is_file():
                drift.append(f"{name}: missing here")
                continue
            if normalized(source) != normalized(dest):
                drift.append(f"{name}: differs from Bucketeer")
            continue

        dest.write_text(source.read_text())

    if args.check:
        if drift:
            emit("Bucketeer contract fixtures are out of date:", error=True)
            for line in drift:
                emit(f"  - {line}", error=True)
            emit(
                "\nRe-run without --check to update, then review what changed in the "
                "Bucketeer contract before relying on it.",
                error=True,
            )
            return 1
        emit(f"Bucketeer contract fixtures are up to date ({len(FIXTURES)} files).")
        return 0

    (DEST_DIR / MANIFEST).write_text(
        json.dumps(
            {
                "source": "bucketeer/test/fixtures/analytics_export_v1",
                "bucketeer_commit": bucketeer_commit(Path(args.bucketeer).expanduser().resolve()),
                "files": list(FIXTURES),
            },
            indent=2,
        )
        + "\n"
    )
    emit(f"Updated {len(FIXTURES)} Bucketeer contract fixtures in {DEST_DIR}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
