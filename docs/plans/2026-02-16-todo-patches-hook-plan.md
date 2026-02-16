# TODO.md Auto-Update Hook Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a pre-commit hook that auto-generates a Patches section in TODO.md from `# TODO:` comments and `NotImplementedError` stubs across the codebase.

**Architecture:** A standalone Python script (`scripts/update_todo_patches.py`) scans `squeaky_knees/`, `config/`, and `tests/` for TODO markers, groups them by Django app/directory, and rewrites the `## Patches` section of `TODO.md` while preserving the manual `## Features` section. Runs as a local pre-commit hook.

**Tech Stack:** Python 3.13 stdlib only (re, pathlib, sys). No external dependencies.

**Design doc:** `docs/plans/2026-02-16-todo-patches-hook-design.md`

---

### Task 1: Create initial TODO.md

**Files:**
- Create: `TODO.md`

**Step 1: Create the seed TODO.md**

```markdown
# TODO

## Patches

_No TODO comments or NotImplementedError stubs found._

---

## Features

_Manually maintained. Add planned features and enhancements here._
```

The `## Patches` and `## Features` markers are required by the script to find
section boundaries. The header above Patches and everything from Features onward
are preserved verbatim across script runs.

**Step 2: Commit**

```bash
git add TODO.md
git commit -m "Add initial TODO.md with Patches and Features sections"
```

---

### Task 2: Create the scanner script

**Files:**
- Create: `scripts/update_todo_patches.py`

**Reference:** The original script is in the `update_todo_patches.py` attachment from
the acoustic_emissions_processing project. The key adaptations are listed below.

**Step 1: Create `scripts/` directory and write the script**

The script structure mirrors the original with these changes:

1. **Replace `SRC_DIR` with `SCAN_DIRS`:**

```python
REPO_ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = [
    REPO_ROOT / "squeaky_knees",
    REPO_ROOT / "config",
    REPO_ROOT / "tests",
]
TODO_PATH = REPO_ROOT / "TODO.md"
```

2. **Add exclusion for migrations and __pycache__:**

In the `scan_patches()` function, when iterating `*.py` files, skip any path
that contains `/migrations/` or `/__pycache__/`:

```python
def scan_patches() -> list[PatchItem]:
    items: list[PatchItem] = []

    for scan_dir in SCAN_DIRS:
        if not scan_dir.exists():
            continue
        for py_file in sorted(scan_dir.rglob("*.py")):
            if "/migrations/" in str(py_file) or "/__pycache__/" in str(py_file):
                continue
            # ... rest of scanning logic identical to original
```

3. **Update `PatchItem.module` property for Django app grouping:**

```python
@property
def module(self) -> str:
    rel = self.file.relative_to(REPO_ROOT)
    parts = rel.parts
    # squeaky_knees/blog/... -> "blog", squeaky_knees/users/... -> "users"
    if parts[0] == "squeaky_knees" and len(parts) > 1:
        return parts[1]
    # config/... -> "config", tests/... -> "tests"
    return parts[0]
```

4. **Everything else stays the same:** `TODO_RE`, `NOT_IMPL_RE`, `_rel()`,
`_github_link()`, `_find_enclosing_function()`, `_read_docstring_summary()`,
`PatchItem.to_markdown()`, `group_by_module()`, `build_patches_section()`,
`rewrite_todo_md()`, and `main()` are unchanged from the original.

**Step 2: Make the script executable**

```bash
chmod +x scripts/update_todo_patches.py
```

**Step 3: Run the script standalone to verify**

```bash
python scripts/update_todo_patches.py
```

Expected output: `TODO.md updated (1 patch items found).`
Exit code: 1 (because content changed)

The one known TODO is in `config/settings/production.py:57`:
```python
# TODO: set this to 60 seconds first and then to 518400 once you prove the former works
```

**Step 4: Verify TODO.md was updated correctly**

Read `TODO.md` and confirm it now contains a `### Config` section with the
production.py TODO item, with a correct relative link.

**Step 5: Run again to verify idempotency**

```bash
python scripts/update_todo_patches.py
```

Expected output: (no output)
Exit code: 0 (because content didn't change)

**Step 6: Commit**

```bash
git add scripts/update_todo_patches.py TODO.md
git commit -m "Add update_todo_patches.py scanner script

Scans squeaky_knees/, config/, and tests/ for TODO comments
and NotImplementedError stubs. Generates the Patches section
of TODO.md with grouped entries and GitHub-compatible links."
```

---

### Task 3: Add the pre-commit hook

**Files:**
- Modify: `.pre-commit-config.yaml` (append before the `ci:` block)

**Step 1: Add the local hook entry**

Append this block before the `ci:` section at the end of `.pre-commit-config.yaml`:

```yaml
  # ── TODO.md patches auto-update ──────────────────────────────────
  - repo: local
    hooks:
      - id: update-todo-patches
        name: update TODO.md patches
        entry: python scripts/update_todo_patches.py
        language: python
        pass_filenames: false
        always_run: true
        stages: [pre-commit]
```

**Step 2: Run pre-commit to verify the hook works**

```bash
pre-commit run update-todo-patches --all-files
```

Expected: The hook runs and either passes (no changes) or fails and re-stages
the modified `TODO.md`. Since we already ran the script in Task 2, this should
pass with no changes.

**Step 3: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "Add update-todo-patches pre-commit hook"
```

---

### Task 4: End-to-end verification

**Step 1: Add a test TODO comment temporarily**

Add to any Python file (e.g., `squeaky_knees/blog/views.py`):
```python
# TODO: Verify the pre-commit hook catches this
```

**Step 2: Stage and attempt a commit**

```bash
git add squeaky_knees/blog/views.py
git commit -m "test: verify todo hook"
```

Expected: The `update-todo-patches` hook fires, detects the new TODO, updates
`TODO.md`, and exits 1. The commit fails (by design — pre-commit needs to
re-stage the changed file).

**Step 3: Verify TODO.md now includes the new item**

Check that a `### Blog` section appeared with the test TODO entry.

**Step 4: Clean up the test TODO**

Remove the test comment, restore `TODO.md` to its previous state:

```bash
git checkout -- squeaky_knees/blog/views.py
python scripts/update_todo_patches.py
```

**Step 5: Final commit with all clean state**

```bash
git add TODO.md
git commit -m "Verify todo-patches hook works end-to-end"
```

Or simply reset if no commit is desired:
```bash
git checkout -- TODO.md squeaky_knees/blog/views.py
```
