#!/usr/bin/env python3
"""Stage a minimal, verified static Pages bundle. PREVIEW ONLY, no deploy.

No networking, subprocesses or changes to the working repository.
The destination must not exist before execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = (
    "index.html",
    "predictions.json",
    "tips.json",
    "CNAME",
    "lab_forward/ledger.json",
    "lab_forward/experiment.json",
    "lab_forward/run_status.json",
    "lab_forward/RAPORT.md",
)
EXPECTED_DOMAIN = "rzotkiewka.pl"


def references(html: str) -> set[str]:
    """Discover literal local data references in the current page."""
    matches = re.findall(
        r"""['"](\./[A-Za-z0-9_./-]+\.(?:json|md|html))(?:\?[^'"]*)?['"]""",
        html,
    )
    return {item.removeprefix("./") for item in matches}


def validate(root: Path = ROOT) -> dict[str, str]:
    """Fail closed if the expected public bundle is missing or inconsistent."""
    records: dict[str, str] = {}
    for rel in PUBLIC_FILES:
        src = root / rel
        if src.is_symlink() or not src.is_file():
            raise ValueError(f"Missing or linked public source: {rel}")
        records[rel] = hashlib.sha256(src.read_bytes()).hexdigest()

    domain = (root / "CNAME").read_text(encoding="utf-8").strip()
    if domain != EXPECTED_DOMAIN:
        raise ValueError("CNAME does not match the recorded custom domain")
    html = (root / "index.html").read_text(encoding="utf-8")
    if "<html" not in html.lower():
        raise ValueError("index.html is not an HTML document")
    missing = references(html).difference(PUBLIC_FILES)
    if missing:
        raise ValueError("Page refers to unstaged files: " + ", ".join(sorted(missing)))

    for rel, required_key, required_type in (
        ("predictions.json", "forecasts", list),
        ("tips.json", "tips", list),
        ("lab_forward/ledger.json", "forecasts", list),
        ("lab_forward/experiment.json", "config", dict),
    ):
        payload = json.loads((root / rel).read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(
            payload.get(required_key), required_type
        ):
            raise ValueError(f"Invalid required JSON structure: {rel}")
    status = json.loads((root / "lab_forward/run_status.json").read_text(encoding="utf-8"))
    if not isinstance(status, dict) or status.get("schema") != 1:
        raise ValueError("Invalid LAB run status")
    return records


def stage(destination: Path, root: Path = ROOT) -> dict[str, str]:
    """Copy allowlisted files, never overwriting existing output."""
    records = validate(root)
    output = destination.expanduser().resolve(strict=False)
    source = root.resolve()
    if output == source or source in output.parents:
        raise ValueError("Destination must be outside the repository")
    if output.exists() or not output.parent.is_dir():
        raise ValueError("Destination must not exist and parent must exist")
    output.mkdir()
    for rel in PUBLIC_FILES:
        target = output / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / rel, target)
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != records[rel]:
            raise ValueError(f"Copy hash mismatch: {rel}")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="New output folder outside repo")
    args = parser.parse_args()
    manifest = stage(args.destination)
    print(f"PREVIEW ONLY: {len(manifest)} files copied and SHA-256 checked.")
    for name, checksum in sorted(manifest.items()):
        print(checksum, name)
    print("No Pages deployment, settings change, purchase, or LAB execution.")


if __name__ == "__main__":
    main()
