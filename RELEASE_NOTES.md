# mongo-x-ray 2.1.0 — Release Notes

**Scope**: v2.0.0 (2026-08-31) → 2.1.0 (2026-09-08)
**TL;DR**: Report usability improvements (copy icons for every code string, better output folder names), and the issue catalog moved back to the plugin that owns it.

## New Features ✨

- **Copy icons in every report** (#334): all backtick-wrapped strings (inline `<code>`) now show a small copy icon on their right edge — click copies the exact string with a transient ✓ confirmation
  - The icon is always visible (subtle, full opacity on hover) and flows with the text, so it stays correct when a long string wraps onto several lines
  - Code blocks (` ``` ` fenced, managed by highlight.js) re-use the same icon in the **top-right corner** instead of the plugin's "Copy" text
  - Bare `<pre>` blocks (e.g. the JSON samples inside tables) get the same icon too, and are now outlined with a border so they no longer blend into the cell background
  - Copying a block preserves line breaks and indentation (`<br>`/`&nbsp;` markup is converted back to newlines/spaces)
- **Better output folder names** (#335): generated report folders are renamed with the plugin name as a prefix — `log-default-<timestamp>`, `log-<hostname>-default-<timestamp>`, `ftdc-…`, `healthcheck-…`, `gmd-…` — so it is always clear which plugin produced a report (and, with `--discover`, which run)

## Changed 🔧

- **Issue catalog ownership**: `mongo_x_ray.issues` was removed from core — the catalog is maintained by the healthcheck plugin (`mongo_x_ray_hc.issues`), and the plugins that reuse healthcheck rules (log, gmd) reference it through those rules. Core no longer ships any module's issue definitions
- **Shared configuration**: added warning thresholds used by the log plugin's rules (slow rate, connection rate, slow operations, query targeting high) now that Top Slow Operations and its chart are a single `SlowItem`
- **Issue definitions**: NUMA is now reported on all MongoDB versions (previously version-dependent)
- Version bumped to 2.0.1 (intermediate fix release) and then to **2.1.0**
- **Prebuilt binary contents**: the frozen `x-ray` binaries bundle the `healthcheck` (`hc`) plugin as well — the `log` plugin depends on it, and `make plugin-deps` installs it from source, so `x-ray log`, `x-ray ftdc` and `x-ray healthcheck` all work out of the box

## Fixed 🐛

- No behavioural regressions; the report-copy work above includes several fixes found while validating it in a real browser (button anchoring, wrapped-line positioning, preserved line breaks, setup timing)

## Dependencies

- Runtime pins: `pymongo` 4.17.0 → 4.18.0, `openai` 3.5.0 → 3.8.0
- Security: `WeasyPrint` 69.0 → 70.0, which fixes an SSRF / local-file-read issue
  ([GHSA-jf6q-chmf-3h3v](https://github.com/advisories/GHSA-jf6q-chmf-3h3v),
  CVE-2026-55073) in PDF rendering
- Dev tooling: `ruff` 0.16.5 → 0.16.6, `pylint` 4.0.7 → 4.0.8, plus routine bumps of `pyinstaller`, `idna` and `python-dotenv`

## Development 🔩

- **Dependabot**: enabled for `pip` and GitHub Actions (weekly). Patch and minor updates merge automatically once every check is green, as do major updates of the CI actions and the build/lint/test tooling; a major update of a runtime dependency (`pymongo`, `openai`, `WeasyPrint`, …) is left for review, and a failing or missing check leaves the pull request open instead of merging
- **Bundled plugin build**: `make plugin-deps` installs `mongo-x-ray-hc` from source alongside `log` and `ftdc`, because hc 2.0.0 on PyPI imports `mongo_x_ray.issues`, which 2.1.0 removed; the pin moves to `mongo-x-ray-hc>=2.1.0` once hc 2.1.0 is published

## Upgrade Guide (2.0.0 → 2.1.0)

```bash
pip install -U mongo-x-ray mongo-x-ray-log mongo-x-ray-ftdc mongo-x-ray-hc
```

- No API or CLI breaking changes — commands, options and report structure are unchanged
- This is a coordinated release: `mongo-x-ray-hc` **2.1.0 or newer** is required. hc 2.0.0 imports `mongo_x_ray.issues`, a module core 2.1.0 no longer ships, so an older hc breaks plugin discovery — the `pip install -U …` line above upgrades all four packages together
- If you maintain code against the core, note that `mongo_x_ray.issues` no longer exists; use the healthcheck plugin's catalog (`mongo_x_ray_hc.issues`) or your own
