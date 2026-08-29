# The sync script is what keeps the checked-in contract fixtures honest. If it can report
# success while leaving a stale copy in place, the gate it feeds is worthless, so its
# refusal path is worth covering.
import sys
import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent / "sync_bucketeer_contract_fixtures.py"
FIXTURES = Path(__file__).parent / "fixtures"


def run(bucketeer: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--bucketeer", str(bucketeer), *args],
        capture_output=True,
        text=True,
    )


@pytest.fixture
def complete_checkout(tmp_path: Path) -> Path:
    """A stand-in Bucketeer checkout holding every fixture we already have."""
    source = tmp_path / "test/fixtures/analytics_export_v1"
    source.mkdir(parents=True)
    for path in FIXTURES.glob("*.json"):
        if path.name != "MANIFEST.json":
            (source / path.name).write_text(path.read_text())
    return tmp_path


class TestSyncContractFixtures:
    def test_check_passes_against_a_complete_checkout(self, complete_checkout: Path) -> None:
        result = run(complete_checkout, "--check")
        assert result.returncode == 0, result.stderr

    def test_check_reports_drift(self, complete_checkout: Path) -> None:
        target = complete_checkout / "test/fixtures/analytics_export_v1/context.json"
        body = json.loads(target.read_text())
        body["contractVersion"] = "999"
        target.write_text(json.dumps(body))

        result = run(complete_checkout, "--check")
        assert result.returncode == 1
        assert "context.json" in result.stderr

    def test_check_ignores_formatting_only_differences(self, complete_checkout: Path) -> None:
        # Compared as parsed JSON, so a reformat must not read as a contract change.
        target = complete_checkout / "test/fixtures/analytics_export_v1/context.json"
        target.write_text(json.dumps(json.loads(target.read_text()), indent=8))

        assert run(complete_checkout, "--check").returncode == 0

    def test_update_refuses_a_checkout_missing_a_fixture(self, complete_checkout: Path) -> None:
        # Updating anyway would leave the stale copy in place and write a manifest
        # claiming it came from this commit, hiding the drift the script exists to catch.
        (complete_checkout / "test/fixtures/analytics_export_v1/goals.json").unlink()

        result = run(complete_checkout)
        assert result.returncode == 1
        assert "goals.json" in result.stderr
        # The manifest must not have been rewritten.
        manifest = json.loads((FIXTURES / "MANIFEST.json").read_text())
        assert "goals.json" in manifest["files"]

    def test_errors_on_a_path_that_is_not_a_bucketeer_checkout(self, tmp_path: Path) -> None:
        result = run(tmp_path)
        assert result.returncode == 2
        assert "does not exist" in result.stderr
