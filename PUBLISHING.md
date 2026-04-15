# Publishing ansifuzz to PyPI

## First-time setup

### 1. Create a PyPI account

Go to https://pypi.org/account/register/ and create an account.
Enable 2FA — PyPI requires it for publishing.

### 2. Configure trusted publishing (recommended — no API tokens needed)

Trusted publishing lets GitHub Actions publish to PyPI without storing a secret.

1. Go to https://pypi.org/manage/account/publishing/
2. Click **Add a new pending publisher**
3. Fill in:
   - **PyPI project name**: `ansifuzz`
   - **Owner**: `chrisvanmeer`
   - **Repository name**: `ansifuzz`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`
4. Click **Add**

Then in your GitHub repository:
1. Go to **Settings → Environments → New environment**
2. Name it `pypi`
3. Optionally add a protection rule (e.g. require a reviewer)

### 3. Create the GitHub repository

```bash
cd ansifuzz
git init
git add .
git commit -m "chore: initial release v1.0.0"
git branch -M main
git remote add origin https://github.com/chrisvanmeer/ansifuzz.git
git push -u origin main
```

---

## Releasing a new version

### Step 1 — Bump the version

Edit `pyproject.toml`:

```toml
[project]
version = "1.1.0"   # was 1.0.0
```

### Step 2 — Update the changelog

Add an entry to `CHANGELOG.md`:

```markdown
## [1.1.0] - 2025-06-01

### Added
- Description of new feature

### Fixed
- Description of bug fix
```

### Step 3 — Commit and tag

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release v1.1.0"
git tag v1.1.0
git push origin main --tags
```

Pushing the tag triggers the `publish.yml` GitHub Actions workflow, which:
1. Builds the source distribution and wheel
2. Publishes both to PyPI via trusted publishing

You can watch the run at:
`https://github.com/chrisvanmeer/ansifuzz/actions`

### Step 4 — Verify

```bash
pip install --upgrade ansifuzz
ap --help
```

---

## Versioning guidelines

ansifuzz follows [Semantic Versioning](https://semver.org/):

| Change | Version bump | Example |
|--------|-------------|---------|
| Bug fix, docs update | Patch | `1.0.0 → 1.0.1` |
| New flag, new feature (backwards-compatible) | Minor | `1.0.0 → 1.1.0` |
| Breaking change (flag renamed, behaviour change) | Major | `1.0.0 → 2.0.0` |

---

## Manual publish (fallback, no GitHub Actions)

If you need to publish manually:

```bash
pip install build twine
python -m build
twine upload dist/*
```

You will be prompted for your PyPI username and password (or an API token as the password).
