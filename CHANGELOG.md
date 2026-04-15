# Changelog

All notable changes to ansifuzz are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-04-15

### Added
- Multi-inventory support in `ap`: when `-i` is given, Tab selects multiple
  inventory files; each is passed as a separate `-i` flag to `ansible-playbook`
- Limit picker now merges hosts and groups from all selected inventories,
  deduplicated, when multiple inventories are active
- All pickers can now be opened without a value: `ap -i -l -p -t` opens each
  picker in sequence with an empty query

### Changed
- `-i` without a value now always opens the picker (previously fell back to
  config default); config default is only used when `-i` is omitted entirely
- `default_inventory` in config updated to `production.ini` in documentation
  and generated config template

## [1.0.0] - 2025-01-01

### Added
- `ap` command: fuzzy-search wrapper for `ansible-playbook`
- `aa` command: fuzzy-search wrapper for `ansible` ad-hoc
- Fuzzy picker for inventory files (`-i`), including pre-fill query
- Fuzzy picker for playbooks (`-p`), including pre-fill query
- Fuzzy picker for hosts/groups from inventory (`-l`), including pre-fill query
- Fuzzy picker for tags parsed from the selected playbook (`-t`)
- Review mode (`-r`): adds `--check --diff` (ap) or `--check` (aa)
- Config file support: `~/.config/ansifuzz/config.yaml`
  - `default_inventory`: skip inventory picker when set
  - `playbook_dir`: configure playbook search directory
- INI and YAML inventory format support
- Multi-select in limit and tags pickers (Tab key)
