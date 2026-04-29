# Changelog

All notable changes to `dotref`.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] — 2026-04-29

The "actually useful" release. Reshapes the CLI surface, lands colors and an interactive picker, triples the database, and reconciles the contributor docs with reality.

### Added

**CLI**
- **Auto-bootstrap on first run.** `~/.dotref/data` is seeded from the bundled database the first time the CLI runs against an empty data dir — no manual `mkdir && cp -r data/*` step after `pipx install -e .`. Looks first beside `dotref.py`, then under `<sys.prefix>/share/dotref/data` for non-editable installs.
- **Real `dotref update`.** Fetches the latest `data/` tree from the official repo as a tarball (`urllib` + `tarfile`, stdlib-only — no `requests` dependency), extracts it, and atomically replaces `~/.dotref/data`. Refuses to operate inside a git checkout to protect in-progress work.
- **Direct knob lookup.** `dotref <subsystem> <name>` (e.g. `dotref zsh HISTFILE`) resolves a single knob by exact name when the second argument is not a category file. Falls back to a helpful error listing available categories.
- **Color layer.** ANSI output for subsystem, category, knob name, type tag, defaults, examples, docs URLs. Resolves once per process via `_use_color()` from `NO_COLOR` / `FORCE_COLOR` / `sys.stdout.isatty()`. Type-specific colors are keyed off the `type` field via `_TYPE_CODES` (env=green, setopt/shopt=magenta, parameter=cyan, config=blue, flag=yellow).
- **fzf interactive picker.** Bare `dotref` launches the picker if fzf is on PATH (or `dotref pick` to invoke explicitly). Tab-delimited input feeds fzf with `<path>\t<colored display>`; `--with-nth=2..` hides the path; `--preview` re-invokes the script via the hidden `--preview-knob <path>` flag, with `FORCE_COLOR=1` injected so colors survive the subprocess.
- **`--json` output flag.** Machine-readable output for `list`, `<subsystem>`, `<subsystem> <category>`, `<subsystem> <name>`, `search`, and `version`. Composable with `jq` and shell pipelines.
- **`--plain` output flag.** Plain text without ANSI colors. Overrides `FORCE_COLOR=1` for clean script output.
- **Ranked search.** Results are sorted by tier — exact name match (0) > name prefix (1) > name substring (2) > description substring (3). A subsystem-name keyword (e.g. `dotref search gtk`) bumps that subsystem's hits by half a tier.

**Data format**
- **`type` field on every knob.** One of `env`, `parameter`, `setopt`, `shopt`, `config`, `flag`. Renders as a colored tag in output. Required on new entries.
- **`[meta]` block per file.** Optional `[meta] docs = "..."` table at the top of each TOML. The docs URL is rendered in category headers, in the fzf preview footer, and in `--json` output. All shipped data files seeded with authoritative URLs.

**New subsystems**
- `xdg` — basedir, userdirs, session (≈25 knobs).
- `hyprland` — environment, input, general, decoration, animations, monitors, misc, binds (≈108 knobs).
- `systemd` — unit, service, journal, environment (≈86 knobs).
- `uwsm` — environment, finalize (≈24 knobs).
- `bash` — parameters, history, prompt, shopts (≈73 knobs).
- `qt` — platform, scaling, theming, debug (≈37 knobs).
- `mesa` — drivers, debug, glsl, vulkan (≈53 knobs).

**Code & docs**
- `ConfigKnob.subsystem` field surfaced in JSON output.
- `DotrefDB.find_knob()`, `DotrefDB.get_meta()`, `DotrefDB._maybe_bootstrap()` helpers.
- `_bundled_data_dir()` resolves the seed database location across editable / wheel / user-site installs.
- `setup.py` ships TOML data via `data_files`; `MANIFEST.in` includes them in sdists.
- `RESERVED_COMMANDS` set drives the argv dispatch (`list`, `search`, `update`, `version`, `pick`).
- `CLAUDE.md` documenting project conventions for future Claude Code sessions.
- `CHANGELOG.md` (this file).

### Changed
- **`show` subcommand removed.** `dotref <subsystem> [category|name]` is now the canonical form. `dotref show zsh history` no longer works — use `dotref zsh history`.
- **README rewritten** to match the shipped CLI: replaced the stale `[meta]` + `[[entry]]` array-of-tables format documentation with the actual `[knob.<id>]` table format, regenerated example output, added a status table for shipped vs. planned subsystems, dropped the "concept / RFC — does not exist yet" framing.
- **TOML files cleaned up:** file-level prefixes stripped from knob `name` fields (a knob in `hyprland/input.toml` is `kb_layout`, not `input:kb_layout`). Sub-section nesting that conveys real structure is preserved (`touchpad:natural_scroll`, `blur:enabled`, `[Install] WantedBy`).
- `CONTRIBUTING.md` tightened with a TOML-validation snippet and an anchor link to the README's data-format section.

### Removed
- `show` subcommand.

### Stats
- 9 subsystems, 31 files, **429 knobs** (up from 3/3/~30 in 0.1.0).
- CLI: ~530 LOC, single file.

---

## [0.1.0] — initial release

Initial implementation: a single-file CLI plus a tiny seed database.

### Added
- `dotref.py` single-file CLI: `list`, `show <sub> [cat]`, `search <kw>`, `update`, `version`.
- `DotrefDB` / `ConfigKnob` data model reading `[knob.<id>]` tables from `data/<subsystem>/<category>.toml`.
- Initial seed data: `zsh/history.toml`, `gtk/environment.toml`, `xdg/basedir.toml`.
- Plain-text output formatter.
- `pipx install -e .` packaging via `setup.py`.
- `CONTRIBUTING.md`, `README.md` with proposed format and roadmap.

### Notes
- README documented an aspirational `[meta]` + `[[entry]]` array-of-tables format that never matched what the loader actually read; this was reconciled in 0.2.0.

---

[0.2.0]: https://github.com/evoppuden/dotref/releases/tag/v0.2.0
[0.1.0]: https://github.com/evoppuden/dotref/releases/tag/v0.1.0
