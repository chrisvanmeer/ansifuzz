#!/usr/bin/env bash
# install.sh — Install ansifuzz from source and create default config.
# For PyPI installs, use: pip install ansifuzz
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${HOME}/.config/ansifuzz"
CONFIG_FILE="${CONFIG_DIR}/config.yaml"

echo "==> Installing ansifuzz..."

if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    pip install -e "${SCRIPT_DIR}" --quiet
else
    pip install --user -e "${SCRIPT_DIR}" --quiet
fi

echo "==> ansifuzz installed."

# Create default config only if it does not already exist
if [[ ! -f "${CONFIG_FILE}" ]]; then
    mkdir -p "${CONFIG_DIR}"
    cat > "${CONFIG_FILE}" << 'YAML'
# ansifuzz configuration (~/.config/ansifuzz/config.yaml)
# --------------------------------------------------------

# Default inventory file used by both ap and aa.
# Relative paths are resolved from the current working directory.
# When set, the inventory picker is skipped — unless you pass -i explicitly.
#
# default_inventory: production.ini

# Directory to search for playbooks (default: playbooks/)
# ap will recursively search for *.yml files here.
#
# playbook_dir: playbooks
YAML
    echo "==> Created config at ${CONFIG_FILE}"
    echo "    Set 'default_inventory' to skip the inventory picker by default."
else
    echo "==> Config already exists at ${CONFIG_FILE} — not overwritten."
fi

echo ""
if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    echo "Installed into: ${VIRTUAL_ENV}"
else
    echo "Make sure ~/.local/bin is on your PATH:"
    echo '  export PATH="$HOME/.local/bin:$PATH"'
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " ap — ansible-playbook"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ap                        fully interactive (all pickers)"
echo "  ap -p nginx               playbook picker pre-filled with 'nginx'"
echo "  ap -l 0007                limit picker pre-filled → finds server0007"
echo "  ap -i dev -l web -p nginx -t config"
echo "                            all four pickers pre-filled"
echo "  ap -i dev -l 0007 -p infra -r"
echo "                            review run (--check --diff)"
echo ""
echo "  fzf keybindings:"
echo "    Enter   confirm selection"
echo "    Esc     cancel / skip optional step"
echo "    Tab     multi-select (limit + tags pickers)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " aa — ansible ad-hoc"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  aa                        fully interactive"
echo "  aa -m ansible.builtin.ping"
echo "                            skip module picker"
echo "  aa -l web -m ansible.builtin.command -a 'cmd=uptime'"
echo "  aa -i staging             switch inventory, pick target interactively"
echo "  aa -l db01 -m ansible.builtin.service -a 'name=postgresql state=restarted' -r"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
