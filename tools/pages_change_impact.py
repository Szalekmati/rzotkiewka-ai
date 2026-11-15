#!/usr/bin/env python3
"""Offline, read-only classification of a FUTURE GitHub Pages publication policy.

Never deploys, modifies files or configuration, uses network, or executes
subprocesses. Output is informational only, never a release approval.
Run: python -m tools.pages_change_impact index.html tips.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import PurePosixPath

from tools.prepare_pages_bundle import PUBLIC_FILES

LAB_OBSERVATIONS = frozenset((
    "lab_forward/run_status.json", "lab_forward/RAPORT.md",
))
ESSENTIAL_PUBLIC = frozenset(PUBLIC_FILES) - LAB_OBSERVATIONS
BUILD_INPUTS = frozenset(("tools/prepare_pages_bundle.py",))
NONPUBLIC_PREFIXES = ("tests/", "docs/", "tools/")


def _checked_paths(paths):
    if not isinstance(paths, (list, tuple)) or not paths:
        raise ValueError("Supply at least one changed file")
    cleaned = set()
    for path in paths:
        if (not isinstance(path, str) or not path or path != path.strip()
                or "\\" in path or "\x00" in path or path.startswith("/")
                or any(part in ("", ".", "..") for part in path.split("/"))
                or PurePosixPath(path).is_absolute()):
            raise ValueError(f"Invalid repository-relative path: {path!r}")
        cleaned.add(path)
    return sorted(cleaned)


def classify(paths, *, allow_stale_lab=False):
    """Classify candidate updates; unknown changes require review (fail-closed).

    Normal mode preserves LAB snapshot freshness. Opt-in simulation can consider
    skipping status-only commits ONLY if the operator accepts stale public data.
    """
    checked = _checked_paths(paths)
    essential = [p for p in checked if p in ESSENTIAL_PUBLIC]
    observations = [p for p in checked if p in LAB_OBSERVATIONS]
    build_inputs = [p for p in checked if p in BUILD_INPUTS]
    technical = [p for p in checked if p.startswith(NONPUBLIC_PREFIXES)]
    unknown = [p for p in checked if p not in ESSENTIAL_PUBLIC
               and p not in LAB_OBSERVATIONS and p not in BUILD_INPUTS
               and not p.startswith(NONPUBLIC_PREFIXES)]
    if unknown:
        decision = "REVIEW_UNKNOWN"
    elif essential or build_inputs:
        decision = "PUBLISH_CANDIDATE"
    elif observations and not allow_stale_lab:
        decision = "PUBLISH_CANDIDATE"
    elif observations:
        decision = "SKIP_CANDIDATE_STALE_LAB"
    else:
        decision = "SKIP_CANDIDATE_TECHNICAL"

    return {
        "mode": "DRY_RUN_ONLY",
        "decision": decision,
        "allow_stale_lab": bool(allow_stale_lab),
        "changed_files": checked,
        "essential_public": essential,
        "build_inputs": build_inputs,
        "lab_observations": observations,
        "technical_only": technical,
        "unknown": unknown,
        "caveat": (
            "Current branch-based GitHub Pages may still build after any main push; "
            "this classifier does not control it. A future skipped LAB observation "
            "means the published LAB snapshot can be stale even while scheduled LAB "
            "runs succeed. Unknown paths must be reviewed manually."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-stale-lab", action="store_true",
        help="SIMULATION ONLY: permit skipped LAB-status-only publications",
    )
    parser.add_argument("paths", nargs="+", help="Changed repository-relative paths")
    args = parser.parse_args()
    try:
        result = classify(args.paths, allow_stale_lab=args.allow_stale_lab)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
