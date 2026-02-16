# Design: TODO.md Auto-Update Pre-Commit Hook

## Goal

Port the `update_todo_patches.py` pre-commit hook from the acoustic_emissions_processing
project to squeaky_knees. The hook scans Python source for `# TODO:` comments and
`raise NotImplementedError` stubs, then auto-generates a `## Patches` section in
`TODO.md`. A manually-maintained `## Features` section is preserved across runs.

## Files

| Action | Path | Purpose |
|--------|------|---------|
| Create | `scripts/update_todo_patches.py` | Scanner script |
| Create | `TODO.md` | Initial TODO with Patches + Features sections |
| Modify | `.pre-commit-config.yaml` | Add local hook entry |

## Scanner Behavior

### Scan directories

- `squeaky_knees/` (blog, users, contrib apps)
- `config/` (Django settings and middleware)
- `tests/` (test suite)

### Exclusions

- `*/migrations/` directories (skipped internally so standalone runs also work)
- `__pycache__/` directories

### Patterns detected

1. `# TODO:` and `# TODO ` comments, with multi-line continuation
2. `raise NotImplementedError(...)` stubs with enclosing function context

### Module grouping

Files are grouped by their top-level location for the Markdown headings:

| File path | Group heading |
|-----------|--------------|
| `squeaky_knees/blog/*.py` | Blog |
| `squeaky_knees/users/*.py` | Users |
| `squeaky_knees/contrib/*.py` | Contrib |
| `config/*.py` | Config |
| `tests/*.py` | Tests |

The grouping logic resolves relative to `REPO_ROOT` and uses the first meaningful
directory component (for `squeaky_knees/`, it uses the second component since the
first is the project package).

### Link format

Relative paths with GitHub-compatible line anchors:

```
[squeaky_knees/blog/views.py:42](squeaky_knees/blog/views.py#L42)
```

## TODO.md Structure

```markdown
# TODO

## Patches

Code-level TODOs and stubs that need attention.

### Blog
- **some_function()** - Description
  [squeaky_knees/blog/views.py:42](squeaky_knees/blog/views.py#L42)

### Tests
- **TODO** - Add edge case for...
  [tests/test_comments.py:15](tests/test_comments.py#L15)

---

## Features

_Manually maintained. Add planned features and enhancements here._
```

The script rewrites everything between `## Patches` and `## Features`, preserving
the header above Patches and the Features section below.

## Pre-Commit Hook Configuration

Appended to `.pre-commit-config.yaml` as a local repo:

```yaml
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

## Key Adaptations from Original

1. **Multiple scan roots** instead of a single `SRC_DIR`
2. **Module resolution** uses repo-relative paths with Django app awareness
3. **Migration exclusion** built into the scanner (not just pre-commit exclude)
4. **No external dependencies** - pure stdlib, same as original
