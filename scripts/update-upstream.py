#!/usr/bin/env python3
"""Update the pinned weekly release; no third-party Python dependencies."""

import argparse
from datetime import date
import json
from pathlib import Path
import re
import subprocess

REPOSITORY = "TheGoodDoktor/8BitAnalysers"
TAG = re.compile(r"weekly-(\d{4}-\d{2}-\d{2})")
PIN = re.compile(r"^(version: &upstream-version )(weekly-\d{4}-\d{2}-\d{2})$", re.MULTILINE)


def release_date(tag):
    match = TAG.fullmatch(tag)
    if not match:
        raise ValueError(f"Unsupported release tag: {tag!r}")
    return date.fromisoformat(match[1])


def update_recipe(recipe, releases):
    pins = list(PIN.finditer(recipe))
    if len(pins) != 1:
        raise ValueError("Expected exactly one pinned weekly version anchor")
    current = pins[0][2]
    current_date = release_date(current)
    candidates = [r["tag_name"] for r in releases
                  if not r["draft"] and not r["prerelease"]
                  and TAG.fullmatch(r["tag_name"])]
    if not candidates:
        raise ValueError("No published weekly releases found")
    latest = max(candidates, key=release_date)
    changed = release_date(latest) > current_date
    if changed:
        recipe = PIN.sub(lambda match: match[1] + latest, recipe)
    return recipe, {"current": current, "latest": latest,
                    "needs_update": str(changed).lower()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipe", type=Path, default=Path("snap/snapcraft.yaml"))
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    # Paginate: API ordering is not a guarantee of the newest weekly tag.
    result = subprocess.run(
        ["gh", "api", "--paginate", "--slurp",
         f"repos/{REPOSITORY}/releases?per_page=100"],
        check=True, text=True, stdout=subprocess.PIPE)
    releases = [release for page in json.loads(result.stdout) for release in page]
    recipe, outputs = update_recipe(args.recipe.read_text(), releases)
    if args.write and outputs["needs_update"] == "true":
        args.recipe.write_text(recipe)
    lines = "".join(f"{key}={value}\n" for key, value in outputs.items())
    print(lines, end="")
    if args.github_output:
        with args.github_output.open("a") as output:
            output.write(lines)


if __name__ == "__main__":
    main()
