# ansifuzz

Fuzzy-search CLI wrappers for `ansible-playbook` (`ap`) and `ansible` ad-hoc (`aa`).

Every flag opens an [fzf](https://github.com/junegunn/fzf) picker. Passing a value pre-fills the search query — you still confirm with Enter. This means `ap -i dev -l web -p nginx -t config -r` opens four sequential pickers, each already filtered, so a few keystrokes get you to a reviewed playbook run.

## Requirements

- Python 3.9+
- [fzf](https://github.com/junegunn/fzf) on your PATH
- `pyyaml` (installed automatically)

```bash
# Debian/Ubuntu
sudo apt install fzf

# macOS
brew install fzf

# Fedora/RHEL
sudo dnf install fzf
```

## Installation

### From PyPI (recommended)

```bash
pip install ansifuzz
```

### From source

```bash
git clone https://github.com/chrisvanmeer/ansifuzz
cd ansifuzz
bash install.sh
```

Make sure `~/.local/bin` is on your PATH (not needed inside a virtualenv):

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Configuration

`~/.config/ansifuzz/config.yaml` is created automatically on first install.

```yaml
# Default inventory used by both ap and aa.
# Relative paths are resolved from the current working directory.
# When set, the inventory picker is skipped — unless you pass -i explicitly.
default_inventory: production.ini

# Directory to search for playbooks (default: playbooks/)
# playbook_dir: playbooks
```

Inventory files can be either **INI** or **YAML** format — both are detected and parsed automatically.

---

## `ap` — ansible-playbook

```
ap [-i [query]] [-l [query]] [-p [query]] [-t [query]] [-r]
```

| Flag | Description |
|------|-------------|
| `-i` | Inventory picker, optionally pre-filled. Overrides `default_inventory`. |
| `-l` | Limit picker over hosts/groups from the inventory, optionally pre-filled. |
| `-p` | Playbook picker over `playbooks/*.yml`, optionally pre-filled. |
| `-t` | Tags picker — tags are parsed from the chosen playbook, optionally pre-filled. |
| `-r` | Review mode: adds `--check --diff` to the ansible-playbook call. |

### Examples

```bash
# Fully interactive — all pickers in sequence
ap

# Inventory from config, pick playbook interactively
ap

# Pre-fill playbook picker with "nginx"
ap -p nginx

# Pre-fill limit picker with "0007" → finds server0007.example.com
ap -l 0007

# All four pickers pre-filled
ap -i dev -l web -p nginx -t config

# Review run with pre-filled pickers
ap -i dev -l 0007 -p infra -r

# Explicit values only, no pickers
ap -i production.ini -l webservers -p playbooks/deploy.yml
```

### fzf keybindings

| Key | Action |
|-----|--------|
| `Enter` | Confirm selection |
| `Esc` | Cancel / skip optional step |
| `Tab` | Multi-select (limit and tags pickers) |

Multi-selected limits are joined with `:` (`web01:web02`).
Multi-selected tags are joined with `,` (`deploy,config`).

---

## `aa` — ansible ad-hoc

```
aa [-i [query]] [-l [query]] [-m module] [-a 'args'] [-r]
```

| Flag | Description |
|------|-------------|
| `-i` | Inventory picker, optionally pre-filled. Overrides `default_inventory`. |
| `-l` | Target picker over hosts/groups, optionally pre-filled. Defaults to `all`. |
| `-m` | Module name — skips picker when given directly. |
| `-a` | Module arguments (free-form string). |
| `-r` | Review mode: adds `--check` to the ansible call. |

### Examples

```bash
# Ping all hosts in default inventory
aa -m ansible.builtin.ping

# Uptime of a pre-filtered group
aa -l web -m ansible.builtin.command -a "cmd=uptime"

# Pick everything interactively
aa

# Restart a service — review first
aa -l db01 -m ansible.builtin.service -a "name=postgresql state=restarted" -r

# Switch to staging inventory, pick target interactively
aa -i staging
```

---

## Flag behaviour at a glance

| Invocation | Behaviour |
|------------|-----------|
| `-i` omitted | Use `default_inventory` from config, or picker if not set |
| `-i` (no value) | Picker opens, no pre-fill |
| `-i dev` | Picker opens, pre-filled with `dev` |
| `-l` omitted | No limit applied |
| `-l` (no value) | Picker opens, no pre-fill |
| `-l 0007` | Picker opens, pre-filled — fzf finds `server0007.example.com` |
| `-p`, `-t` | Same pattern as `-l` |

---

## License

MIT — see [LICENSE](LICENSE).
