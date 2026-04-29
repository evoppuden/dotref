<div align="center">

# 📖 dotref

### The missing reference manual for your dotfiles.

*A community-maintained, tldr-style lookup for Linux environment variables,
shell parameters, and setopts — for GTK, ZSH, XDG, Qt, Wayland and more.*

[![Version](https://img.shields.io/badge/version-v0.2.0-blue?style=flat-square)](https://github.com/evoppuden/dotref/releases/tag/Latest)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen?style=flat-square)](https://github.com/evoppuden/dotref/graphs/contributors)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](https://github.com/evoppuden/dotref/graphs/contributors)

</div>

---

## 📦 Installation

**Requirements:** `python3` (≥3.10) · `python-pipx` · *optional:* [`fzf`](https://github.com/junegunn/fzf) for the interactive picker

```bash
git clone https://github.com/evoppuden/dotref
cd dotref
pipx install -e .
```

The first run of `dotref` seeds `~/.dotref/data` from the bundled database automatically — no manual `cp` step. To pull a fresh copy from the official repo any time:

```bash
dotref update
```

---

## 💡 Usage

```bash
dotref                          # interactive fzf picker (if fzf is installed)
dotref list                     # list all available subsystems
dotref <subsystem>              # list categories for a subsystem
dotref <subsystem> <category>   # show all knobs in a category
dotref search <keyword>         # search across every subsystem
dotref pick                     # explicit picker invocation
dotref version
```

Colors auto-enable on a TTY. Override with `NO_COLOR=1` or `FORCE_COLOR=1`. Override the data directory with `--data-dir <path>` — useful when iterating on data inside a checkout (`python3 dotref.py --data-dir ./data zsh history`).

### Examples

```bash
dotref zsh                      # list zsh categories
dotref zsh history              # show all zsh history knobs
dotref gtk environment          # show GTK env vars
dotref hyprland input           # Hyprland input config directives
dotref search theme             # find every knob mentioning "theme"
dotref search XDG               # find every XDG_* knob
```

---

## 📟 Example output

### `dotref zsh history`

```
# zsh - history
========================================

  HISTFILE  (parameter)
    Path to the file where history is persisted across sessions.
    default: ~/.zsh_history
    example: HISTFILE=~/.zsh_history

  HISTSIZE  (parameter)
    Max number of events kept in memory during a session.
    default: 10000

  HIST_IGNORE_DUPS  (setopt)
    Don't record a command if identical to the previous one.
    example: setopt HIST_IGNORE_DUPS

  SHARE_HISTORY  (setopt)
    Share history in real time across all open zsh sessions.
    example: setopt SHARE_HISTORY
```

The `(parameter)`, `(setopt)`, `(env)`, `(config)` tags are color-coded in a TTY so types are scannable at a glance.

---

## 📦 Subsystems

| Subsystem | Status | Description | Source |
|-----------|--------|-------------|--------|
| `xdg` | ✅ shipped | Base directories, user dirs, session vars | freedesktop.org spec |
| `zsh` | ✅ shipped | Parameters, setopts (history) | `man zshparam`, `man zshoptions` |
| `gtk` | ✅ shipped | Theming, rendering, debug env | docs.gtk.org |
| `hyprland` | ✅ shipped | input, monitors, decoration, animations, binds | wiki.hyprland.org |
| `systemd` | ✅ shipped | unit, service, journal, environment | `man systemd.unit`, `man systemd.service` |
| `uwsm` | ✅ shipped | Wayland session env, finalize vars | `man uwsm` |
| `bash` | 🟡 planned | Parameters, shopts, prompt, history | `man bash` |
| `qt` | 🟡 planned | Platform, scaling, theming | doc.qt.io |
| `mesa` | 🟡 planned | GPU drivers, GLSL, Vulkan | docs.mesa3d.org |
| `wayland` | 🟡 planned | Compositor, backend, display | wayland.freedesktop.org |
| `nvidia` | 🟡 planned | Driver-specific vars | NVIDIA docs |
| `x11` | 🟡 planned | Display, rendering, input | x.org |
| `dbus` | 🟡 planned | Session bus, activation | dbus.freedesktop.org |
| `locale` | 🟡 planned | Language, encoding, formats | `man locale` |
| `color` | 🟡 planned | NO_COLOR, COLORTERM | no-color.org |

🟡 **planned** = wanted, not yet contributed. PRs welcome.

---

## 🗂️ Data format

Each subsystem lives in `data/<subsystem>/`, with one TOML file per category. Every knob is a `[knob.<id>]` table.

```toml
# data/zsh/history.toml
# Source: https://zsh.sourceforge.io/Doc/Release/Parameters.html

[knob.HISTFILE]
name = "HISTFILE"
type = "parameter"
description = "Path to the file where history is persisted across sessions."
default = "~/.zsh_history"
example = "HISTFILE=~/.zsh_history"

[knob.HIST_IGNORE_DUPS]
name = "HIST_IGNORE_DUPS"
type = "setopt"
description = "Don't record a command if identical to the previous one."
example = "setopt HIST_IGNORE_DUPS"
```

### Conventions

- **Source comment at top.** First line(s) of every file should cite the upstream doc you sourced from (`# Source: …`).
- **The table key (`HISTFILE` here) is just an internal identifier — only `name` is displayed.** Use a safe identifier when the displayed name has spaces or punctuation:
  ```toml
  [knob.touchpad_natural_scroll]
  name = "touchpad:natural_scroll"
  ```
- **Strip the file's section name from `name`.** A knob in `hyprland/input.toml` should be `kb_layout`, not `input:kb_layout` — the file already conveys "input". *Do* keep sub-section nesting that conveys real structure: `touchpad:natural_scroll`, `blur:enabled`, `[Install] WantedBy`.
- **`type` is required.** It controls the color tag and helps users tell `env` apart from `setopt` apart from `config`.

### Entry types

| Type | Meaning |
|------|---------|
| `env` | Runtime environment variable (`export FOO=bar`) |
| `parameter` | Shell parameter (ZSH / Bash built-in variable) |
| `setopt` | ZSH `setopt` option |
| `shopt` | Bash `shopt` option |
| `config` | Config-file directive (e.g. systemd `[Service]` keys, Hyprland config lines) |
| `flag` | CLI flag also exposed via env or config |

### Validate before opening a PR

```bash
python3 -c "import tomllib, pathlib; [tomllib.loads(p.read_text()) for p in pathlib.Path('data').rglob('*.toml')]"
python3 dotref.py --data-dir ./data <subsystem> <category>   # spot-check rendering
```

---

## 📊 Why not just use the man page?

| | `man zsh` | `dotref zsh` |
|---|---|---|
| Finds `HISTFILE` | ✅ eventually | ✅ instantly |
| Finds `GTK_THEME` | ❌ wrong man page | ✅ |
| Shows default values | ⚠️ sometimes | ✅ always |
| Searchable by keyword | ⚠️ only inside pager | ✅ `dotref search` |
| Cross-subsystem search | ❌ | ✅ |
| Scannable at a glance | ❌ | ✅ |

---

## 📚 Sources per subsystem

Authoritative pages each subsystem's data should be sourced from:

- **ZSH** — `man zshparam` · `man zshoptions` · https://zsh.sourceforge.io
- **Bash** — `man bash` (PARAMETERS and SHELL BUILTIN COMMANDS sections)
- **GTK 3** — https://docs.gtk.org/gtk3/running.html
- **GTK 4** — https://docs.gtk.org/gtk4/running.html
- **Qt** — https://doc.qt.io/qt-6/qtenvironment.html
- **XDG Base Dir** — https://specifications.freedesktop.org/basedir-spec/latest/
- **XDG User Dirs** — `man xdg-user-dirs`
- **Wayland** — https://wayland.freedesktop.org/docs/html/
- **SDL2** — https://wiki.libsdl.org/SDL2/CategoryHints
- **Mesa** — https://docs.mesa3d.org/envvars.html
- **NO_COLOR / Color** — https://no-color.org · https://bixense.com/clicolors/
- **D-Bus** — https://dbus.freedesktop.org/doc/dbus-specification.html

---

## 🔍 Prior art & related tools

| Tool | What it does | The gap |
|------|-------------|---------|
| [tldr-pages](https://github.com/tldr-pages/tldr) | Short CLI command reference | Commands only, not configuration knobs |
| [navi](https://github.com/denisidoro/navi) | Interactive cheatsheet runner | Commands only, no env var database |
| [cheat](https://github.com/cheat/cheat) | Personal cheatsheets | Not curated per subsystem |
| Arch Wiki | Excellent env var docs | Browser only, not searchable from terminal |
| `man` pages | Authoritative and exhaustive | Slow, verbose, no cross-subsystem search |

`dotref` fills the gap none of these cover.

---

## 🚀 Project status

Working tool, early days. v0.2.0 ships with a CLI (~530 lines of Python), 9 subsystems, 31 files, ~430 knobs, an fzf-driven picker, color-coded type tags, ranked search, and `--json`/`--plain` output formats.

The real product is the data, not the code. The most valuable thing you can contribute is a `.toml` file for a subsystem you know — see the [planned subsystems table](#-subsystems) for what's wanted.

### On the roadmap

- [ ] `dotref <subsystem> <name>` — direct lookup (e.g. `dotref zsh HISTFILE`)
- [ ] `dotref --json` / `--plain` — machine-readable output
- [ ] Smarter `search` ranking (exact > prefix > substring)
- [ ] `[meta] docs = "..."` block per file, surfaced in output
- [ ] `dotref update` — actually fetch latest data from the repo
- [ ] More subsystems: `bash`, `qt`, `mesa`, `wayland`, `nvidia`, `x11`, `dbus`, `locale`, `color`

---

## 🤝 Contributing

You don't need to know how to code — contributing is just editing a TOML file:

1. Fork this repo
2. Find or create `data/<subsystem>/<category>.toml`
3. Add your entry following the [Data format](#️-data-format) above
4. Validate with the snippet in that section
5. Open a PR with a link to the source documentation

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the short version.

---

## ⚖️ License

MIT — do whatever you want with it.

---

<div align="center">
  <sub>Born from typing <code>man zsh</code> one too many times just to find <code>HISTFILE</code>.</sub>
</div>
