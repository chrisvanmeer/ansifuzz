"""Core utilities shared by ap and aa commands."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import yaml


CONFIG_DIR = Path.home() / ".config" / "ansifuzz"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """Load configuration from ~/.config/ansifuzz/config.yaml."""
    if not CONFIG_FILE.exists():
        return {}
    with CONFIG_FILE.open() as fh:
        data = yaml.safe_load(fh) or {}
    return data


def get_default_inventory(config: dict) -> Optional[str]:
    return config.get("default_inventory")


def get_playbook_dir(config: dict) -> Path:
    return Path(config.get("playbook_dir", "playbooks"))


# ---------------------------------------------------------------------------
# fzf
# ---------------------------------------------------------------------------

def _require_fzf() -> None:
    result = subprocess.run(["which", "fzf"], capture_output=True)
    if result.returncode != 0:
        print(
            "ERROR: 'fzf' not found.\n"
            "  sudo apt install fzf   (Debian/Ubuntu)\n"
            "  brew install fzf       (macOS)\n"
            "  sudo dnf install fzf   (Fedora/RHEL)",
            file=sys.stderr,
        )
        sys.exit(1)


def fzf_select(
    choices: list[str],
    prompt: str = "> ",
    multi: bool = False,
    header: Optional[str] = None,
    initial_query: str = "",
    bind: Optional[list[str]] = None,
) -> list[str]:
    """Run fzf and return selected items. Empty list = cancelled."""
    _require_fzf()

    if not choices:
        return []

    cmd = [
        "fzf",
        f"--prompt={prompt}",
        "--ansi",
        "--height=50%",
        "--min-height=10",
        "--border=rounded",
        "--layout=reverse",
        "--info=inline",
    ]

    if multi:
        cmd += ["--multi", "--marker=●"]

    if header:
        cmd += ["--header", header]

    if initial_query:
        cmd += ["--query", initial_query]

    for b in (bind or []):
        cmd += ["--bind", b]

    proc = subprocess.run(
        cmd,
        input="\n".join(choices),
        text=True,
        stdout=subprocess.PIPE,
    )

    if proc.returncode not in (0, 130):
        return []

    return [line for line in proc.stdout.strip().splitlines() if line]


# ---------------------------------------------------------------------------
# Inventory detection + parsing
# ---------------------------------------------------------------------------

def find_inventory_files(search_dir: Path = Path(".")) -> list[str]:
    """Find files matching *inventory* (any extension) in search_dir."""
    pattern = re.compile(r"inventory", re.IGNORECASE)
    return [
        str(p.relative_to(search_dir))
        for p in sorted(search_dir.iterdir())
        if p.is_file() and pattern.search(p.name)
    ]


def _is_yaml_inventory(path: Path) -> bool:
    """Heuristic: .yml/.yaml extension, or first non-comment line starts with 'all:'."""
    if path.suffix.lower() in (".yml", ".yaml"):
        return True
    try:
        with path.open() as fh:
            for line in fh:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    return stripped.startswith("all:")
    except OSError:
        pass
    return False


def _parse_yaml_inventory(path: Path) -> list[str]:
    """
    Parse an Ansible YAML inventory file.
    Returns groups first (sorted), then individual hosts (sorted).
    """
    try:
        with path.open() as fh:
            data = yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:
        print(f"WARNING: Could not parse YAML inventory {path}: {exc}", file=sys.stderr)
        return []

    hosts: set[str] = set()
    groups: set[str] = set()

    def _walk(node: object, in_hosts: bool = False) -> None:
        if not isinstance(node, dict):
            return
        for key, value in node.items():
            if key == "hosts":
                if isinstance(value, dict):
                    hosts.update(str(h) for h in value if h is not None)
                _walk(value, in_hosts=True)
            elif key == "children":
                if isinstance(value, dict):
                    groups.update(str(g) for g in value if g is not None)
                _walk(value)
            elif key in ("vars",):
                continue
            elif in_hosts:
                # host entry with variables dict
                pass
            else:
                if key not in ("all",):
                    groups.add(str(key))
                _walk(value)

    _walk(data)
    return sorted(groups) + sorted(hosts - groups)


def _parse_ini_inventory(path: Path) -> list[str]:
    """
    Parse an INI-style Ansible inventory file.
    Returns groups first (sorted), then individual hosts (sorted).
    """
    hosts: set[str] = set()
    groups: set[str] = set()
    current_section_type = "hosts"

    with path.open() as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith(("#", ";")):
                continue

            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
                if ":" in section:
                    group_name, meta = section.split(":", 1)
                    groups.add(group_name.strip())
                    current_section_type = meta.strip()
                else:
                    groups.add(section.strip())
                    current_section_type = "hosts"
                continue

            if current_section_type == "vars":
                continue

            token = line.split()[0]
            if current_section_type == "children":
                groups.add(token)
            else:
                hosts.add(token)

    return sorted(groups) + sorted(hosts - groups)


def parse_inventory_hosts(inventory_path: str) -> list[str]:
    """
    Parse an Ansible inventory file (INI or YAML).
    Returns groups first (sorted), then individual hosts (sorted).
    """
    path = Path(inventory_path)
    if not path.exists():
        print(f"WARNING: inventory not found: {inventory_path}", file=sys.stderr)
        return []

    if _is_yaml_inventory(path):
        return _parse_yaml_inventory(path)
    return _parse_ini_inventory(path)


# ---------------------------------------------------------------------------
# Playbook helpers
# ---------------------------------------------------------------------------

def find_playbooks(playbook_dir: Path = Path("playbooks")) -> list[str]:
    if playbook_dir.exists():
        return sorted(str(p) for p in playbook_dir.rglob("*.yml"))
    return sorted(str(p) for p in Path(".").glob("*.yml"))


# ---------------------------------------------------------------------------
# Command execution
# ---------------------------------------------------------------------------

def run_command(cmd: list[str]) -> int:
    """Print the full command, then execute it."""
    print()
    print("  " + " ".join(cmd))
    print()
    return subprocess.call(cmd)
