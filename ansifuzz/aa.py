#!/usr/bin/env python3
"""
aa — Ansible ad-hoc runner with fuzzy search.

Usage:
  aa                                        fully interactive
  aa -i dev                                 inventory picker pre-filled with "dev"
  aa -l web                                 target picker pre-filled with "web"
  aa -m ansible.builtin.ping               skip module picker
  aa -l db -m ansible.builtin.command -a "cmd=uptime"
  aa -r                                     review mode: --check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ansifuzz.core import (
    find_inventory_files,
    fzf_select,
    get_default_inventory,
    load_config,
    parse_inventory_hosts,
    run_command,
)

_SENTINEL = "__FUZZY__"

COMMON_MODULES = [
    "ansible.builtin.ping",
    "ansible.builtin.command",
    "ansible.builtin.shell",
    "ansible.builtin.raw",
    "ansible.builtin.script",
    "ansible.builtin.copy",
    "ansible.builtin.fetch",
    "ansible.builtin.file",
    "ansible.builtin.template",
    "ansible.builtin.lineinfile",
    "ansible.builtin.blockinfile",
    "ansible.builtin.replace",
    "ansible.builtin.stat",
    "ansible.builtin.find",
    "ansible.builtin.get_url",
    "ansible.builtin.uri",
    "ansible.builtin.package",
    "ansible.builtin.apt",
    "ansible.builtin.dnf",
    "ansible.builtin.yum",
    "ansible.builtin.service",
    "ansible.builtin.systemd",
    "ansible.builtin.user",
    "ansible.builtin.group",
    "ansible.builtin.cron",
    "ansible.builtin.mount",
    "ansible.builtin.sysctl",
    "ansible.builtin.hostname",
    "ansible.builtin.setup",
    "ansible.builtin.reboot",
    "ansible.builtin.wait_for",
    "ansible.builtin.wait_for_connection",
    "ansible.builtin.debug",
    "ansible.builtin.assert",
    "ansible.builtin.fail",
    "community.general.ufw",
    "community.general.modprobe",
    "community.general.timezone",
    "community.crypto.openssh_keypair",
    "community.docker.docker_container",
    "community.docker.docker_image",
]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aa",
        description="Ansible ad-hoc runner with fuzzy search.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "fzf keybindings:\n"
            "  Enter    confirm selection\n"
            "  Esc      cancel / skip optional step\n"
            "  Tab      multi-select (target picker)"
        ),
    )
    p.add_argument("-i", "--inventory", nargs="?", const=_SENTINEL, default=None,
                   metavar="QUERY",
                   help="Inventory picker, optionally pre-filled with QUERY. "
                        "Overrides config default_inventory.")
    p.add_argument("-l", "--limit", nargs="?", const=_SENTINEL, default=None,
                   metavar="QUERY",
                   help="Target picker over hosts/groups, optionally pre-filled. "
                        "Defaults to 'all' when omitted.")
    p.add_argument("-m", "--module", default=None,
                   help="Ansible module name (skips picker).")
    p.add_argument("-a", "--args", default=None, metavar="ARGS",
                   help='Module arguments, e.g. -a "cmd=uptime".')
    p.add_argument("-r", "--review", action="store_true",
                   help="Review mode: passes --check to ansible.")
    return p


def resolve_inventory(cli_value: str | None, config: dict) -> str | None:
    if cli_value is not None:
        query = "" if cli_value == _SENTINEL else cli_value
        candidates = find_inventory_files()
        if not candidates:
            print("[aa] No inventory files found in current directory.", file=sys.stderr)
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

    default = get_default_inventory(config)
    if default:
        if Path(default).exists():
            return default
        print(f"[aa] WARNING: default_inventory '{default}' not found, opening picker.",
              file=sys.stderr)

    candidates = find_inventory_files()
    if not candidates:
        print("[aa] No inventory files found.", file=sys.stderr)
        return None
    if len(candidates) == 1:
        return candidates[0]
    selected = fzf_select(
        candidates,
        prompt="Inventory ❯ ",
        header="Select inventory  [Enter=confirm  Esc=abort]",
    )
    return selected[0] if selected else None


def resolve_target(cli_value: str | None, inventory: str | None) -> str:
    if cli_value is None:
        return "all"

    query = "" if cli_value == _SENTINEL else cli_value

    if not inventory:
        return query if query else "all"

    hosts = parse_inventory_hosts(inventory)
    if not hosts:
        return query if query else "all"

    selected = fzf_select(
        hosts,
        prompt="Target ❯ ",
        header="Select host(s)/group(s)  [Tab=multi-select  Enter=confirm  Esc=use 'all']",
        multi=True,
        initial_query=query,
    )
    return ":".join(selected) if selected else "all"


def resolve_module(cli_value: str | None) -> str | None:
    if cli_value:
        return cli_value
    selected = fzf_select(
        COMMON_MODULES,
        prompt="Module ❯ ",
        header="Select module  [Enter=confirm  Esc=abort]",
    )
    return selected[0] if selected else None


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = load_config()

    inventory = resolve_inventory(args.inventory, config)
    if not inventory:
        print("[aa] No inventory selected. Aborting.", file=sys.stderr)
        sys.exit(1)

    target = resolve_target(args.limit, inventory)

    module = resolve_module(args.module)
    if not module:
        print("[aa] No module selected. Aborting.", file=sys.stderr)
        sys.exit(1)

    cmd = ["ansible", target, "-i", inventory, "-m", module]
    if args.args:
        cmd += ["-a", args.args]
    if args.review:
        cmd.append("--check")

    sys.exit(run_command(cmd))


if __name__ == "__main__":
    main()
