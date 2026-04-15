#!/usr/bin/env python3
"""
ap — Ansible Playbook runner with fuzzy search.

Usage:
  ap                              fully interactive (all pickers)
  ap -i dev                       inventory picker pre-filled with "dev"
  ap -l 0007                      limit picker pre-filled with "0007"
  ap -p nginx                     playbook picker pre-filled with "nginx"
  ap -t config                    tags picker pre-filled with "config"
  ap -r                           review mode: --check --diff
  ap -i dev -l web -p nginx -t config -r   full example
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from ansifuzz.core import (
    find_inventory_files,
    find_playbooks,
    fzf_select,
    get_default_inventory,
    get_playbook_dir,
    load_config,
    parse_inventory_hosts,
    run_command,
)

_SENTINEL = "__FUZZY__"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ap",
        description="Ansible Playbook runner with fuzzy search.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "All flags open a fuzzy picker; an optional value pre-fills the query.\n\n"
            "fzf keybindings:\n"
            "  Enter    confirm selection\n"
            "  Esc      cancel / skip optional step\n"
            "  Tab      multi-select (limit + tags pickers)"
        ),
    )
    p.add_argument("-i", "--inventory", nargs="?", const=_SENTINEL, default=None,
                   metavar="QUERY",
                   help="Inventory picker, optionally pre-filled with QUERY. "
                        "Overrides config default_inventory.")
    p.add_argument("-l", "--limit", nargs="?", const=_SENTINEL, default=None,
                   metavar="QUERY",
                   help="Limit picker over hosts/groups, optionally pre-filled.")
    p.add_argument("-p", "--playbook", nargs="?", const=_SENTINEL, default=None,
                   metavar="QUERY",
                   help="Playbook picker, optionally pre-filled.")
    p.add_argument("-t", "--tags", nargs="?", const=_SENTINEL, default=None,
                   metavar="QUERY",
                   help="Tags picker (parsed from chosen playbook), optionally pre-filled.")
    p.add_argument("-r", "--review", action="store_true",
                   help="Review mode: passes --check --diff to ansible-playbook.")
    return p


# ---------------------------------------------------------------------------
# Resolvers
# ---------------------------------------------------------------------------

def resolve_inventory(cli_value: str | None, config: dict) -> str | None:
    """
    Resolution order:
    1. -i QUERY  → fuzzy picker pre-filled with QUERY
    2. -i        → fuzzy picker (empty query)
    3. No -i     → use config default_inventory if it exists, else fuzzy picker
    """
    if cli_value is not None:
        # -i was passed (with or without a value): always open picker
        query = "" if cli_value == _SENTINEL else cli_value
        candidates = find_inventory_files()
        if not candidates:
            print("[ap] No inventory files found in current directory.", file=sys.stderr)
            return None
        if len(candidates) == 1 and not query:
            return candidates[0]
        selected = fzf_select(
            candidates,
            prompt="Inventory ❯ ",
            header="Select inventory  [Enter=confirm  Esc=abort]",
            initial_query=query,
        )
        return selected[0] if selected else None

    # No -i flag: try config default
    default = get_default_inventory(config)
    if default:
        if Path(default).exists():
            return default
        print(f"[ap] WARNING: default_inventory '{default}' not found, opening picker.",
              file=sys.stderr)

    # Fall back to picker
    candidates = find_inventory_files()
    if not candidates:
        print("[ap] No inventory files found in current directory.", file=sys.stderr)
        return None
    if len(candidates) == 1:
        return candidates[0]
    selected = fzf_select(
        candidates,
        prompt="Inventory ❯ ",
        header="Select inventory  [Enter=confirm  Esc=abort]",
    )
    return selected[0] if selected else None


def resolve_playbook(cli_value: str | None, config: dict) -> str | None:
    query = "" if (cli_value is None or cli_value == _SENTINEL) else cli_value

    candidates = find_playbooks(get_playbook_dir(config))
    if not candidates:
        print("[ap] No playbooks found.", file=sys.stderr)
        return None
    if len(candidates) == 1 and cli_value is None:
        return candidates[0]

    selected = fzf_select(
        candidates,
        prompt="Playbook ❯ ",
        header="Select playbook  [Enter=confirm  Esc=abort]",
        initial_query=query,
    )
    return selected[0] if selected else None


def resolve_limit(cli_value: str | None, inventory: str | None) -> str | None:
    if cli_value is None:
        return None

    query = "" if cli_value == _SENTINEL else cli_value

    if not inventory:
        print("[ap] Cannot open limit picker: no inventory.", file=sys.stderr)
        return query if query else None

    hosts = parse_inventory_hosts(inventory)
    if not hosts:
        print("[ap] No hosts/groups found in inventory.", file=sys.stderr)
        return query if query else None

    selected = fzf_select(
        hosts,
        prompt="Limit ❯ ",
        header="Select host(s)/group(s)  [Tab=multi-select  Enter=confirm  Esc=skip]",
        multi=True,
        initial_query=query,
    )
    return ":".join(selected) if selected else None


def parse_tags_from_playbook(playbook_path: str) -> list[str]:
    """Extract unique sorted tags from a playbook by scanning for 'tags:' entries."""
    tags: set[str] = set()
    tag_pattern = re.compile(r"^\s*tags\s*:", re.IGNORECASE)
    value_pattern = re.compile(r"['\"]?(\w[\w.-]*)['\"]?")

    try:
        with open(playbook_path) as fh:
            lines = fh.readlines()
    except OSError:
        return []

    for i, line in enumerate(lines):
        if not tag_pattern.match(line):
            continue

        # Inline list: tags: [foo, bar]
        inline = re.search(r"\[([^\]]+)\]", line)
        if inline:
            for m in value_pattern.finditer(inline.group(1)):
                tags.add(m.group(1))
            continue

        # Inline scalar: tags: foo
        scalar = re.search(r"tags\s*:\s*(\S+)", line, re.IGNORECASE)
        if scalar:
            tags.add(scalar.group(1).strip("'\""))
            continue

        # Block list: following lines starting with "- "
        for subsequent in lines[i + 1:]:
            stripped = subsequent.strip()
            if not stripped.startswith("-"):
                break
            m = value_pattern.search(stripped[1:])
            if m:
                tags.add(m.group(1))

    return sorted(tags)


def resolve_tags(cli_value: str | None, playbook: str | None) -> str | None:
    if cli_value is None:
        return None

    query = "" if cli_value == _SENTINEL else cli_value
    tag_list = parse_tags_from_playbook(playbook) if playbook else []

    if not tag_list:
        if query:
            print(f"[ap] No tags found in playbook, using literal: {query}", file=sys.stderr)
            return query
        print("[ap] No tags found in playbook, skipping --tags.", file=sys.stderr)
        return None

    selected = fzf_select(
        tag_list,
        prompt="Tags ❯ ",
        header="Select tag(s)  [Tab=multi-select  Enter=confirm  Esc=skip]",
        multi=True,
        initial_query=query,
    )
    return ",".join(selected) if selected else None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = load_config()

    inventory = resolve_inventory(args.inventory, config)
    if not inventory:
        print("[ap] No inventory selected. Aborting.", file=sys.stderr)
        sys.exit(1)

    playbook = resolve_playbook(args.playbook, config)
    if not playbook:
        print("[ap] No playbook selected. Aborting.", file=sys.stderr)
        sys.exit(1)

    limit = resolve_limit(args.limit, inventory)
    tags = resolve_tags(args.tags, playbook)

    cmd = ["ansible-playbook", "-i", inventory]
    if limit:
        cmd += ["-l", limit]
    if tags:
        cmd += ["--tags", tags]
    if args.review:
        cmd += ["--check", "--diff"]
    cmd.append(playbook)

    sys.exit(run_command(cmd))


if __name__ == "__main__":
    main()
