<div align="center">

# 📖 dotref

### The missing reference manual for your dotfiles.

*A community-maintained, tldr-style lookup for Linux environment variables,
shell parameters, and setopts — for GTK, ZSH, XDG, Qt, Wayland and more.*

[![Version](https://img.shields.io/badge/version-v0.1.0-blue?style=flat-square)](https://github.com/evoppuden/dotref/releases/tag/Latest)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen?style=flat-square)](https://github.com/evoppuden/dotref/graphs/contributors)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](https://github.com/evoppuden/dotref/graphs/contributors)

</div>

---

## 📦 Installation

**Requirements:** `python3` · `python-pipx`

```bash
git clone https://github.com/evoppuden/dotref
cd dotref
pipx install -e .
mkdir -p ~/.dotref/data
cp -r data/* ~/.dotref/data/
```

---

## 💡 Usage

```bash
dotref list                  # list all available subsystems

dotref show zsh              # list all categories for zsh
dotref show zsh history      # show zsh history knobs

dotref show gtk              # list all categories for gtk
dotref show gtk environment  # show gtk environment variables

dotref search theme          # search by keyword across all subsystems
dotref search gtk            # search by keyword across all subsystems
```

---

## ✍️ Next Steps

The most valuable thing you can do right now is contribute a .toml file for a subsystem you know well — XDG, Qt, Wayland, Bash, SDL, Mesa, or anything else. You don't need to know Python. Just copy the format from an existing file in data/, fill it in, and open a PR.

The dream is a community-maintained reference that covers everything — the kind of tool you reach for before opening a browser.

Improvements on the list
- [ ] `dotref update` Support for auto pull /data from the latest repo to ~/.dotref/data
- [ ] `<subsystem>` Replaced with `<app>` or `<package>`. Let's keep it simple :)
- [ ] `dotref show <subsystem>` replaced with `dotref <subsystem>`
- [ ] DotrefDB installation in ~/.dotref/data included in `pipx install -e .`

---
## 🤔 The Problem

You're setting up a minimal Wayland compositor. You vaguely remember there's an env var that forces Qt apps to use Wayland. So you open a browser, dig through the Arch Wiki, scroll past three unrelated sections, and finally find `QT_QPA_PLATFORM=wayland` buried in a paragraph.

**This happens constantly.** There is no tool that answers:

- *what env vars does GTK accept?*
- *what setopts does ZSH have for history?*
- *how do I configure Qt scaling?*

`man` pages are exhaustive but slow to navigate. `tldr` covers commands beautifully — but nothing covers **configuration knobs**: the env vars, shell parameters, and setopts that change how apps *behave*.

**`dotref` is that missing tool.**

---

## 💡 Proposed Usage

```bash
# List all variables for a subsystem
dotref zsh
dotref gtk
dotref xdg
dotref qt
dotref wayland

# Browse by category
dotref zsh history
dotref zsh completion
dotref gtk theming

# Search across all subsystems
dotref search HIST
dotref search theme
dotref search wayland

# Show a specific variable
dotref zsh HISTFILE
dotref gtk GTK_THEME
```

---

## 📟 Example Output

### `dotref zsh history`

```
📖 ZSH › History

  Controls how zsh records and replays command history.
  Docs: https://zsh.sourceforge.io/Doc/Release/Parameters.html

──────────────────────────────────────────────────────────────

  HISTFILE=~/.zsh_history
  Path to the file where history is persisted across sessions.

  HISTSIZE=10000
  Max number of events kept in memory during a session.

  SAVEHIST=10000
  Max events written to HISTFILE on exit. Should be <= HISTSIZE.

  setopt HIST_IGNORE_DUPS
  Don't record a command if identical to the previous one.

  setopt HIST_IGNORE_SPACE
  Commands prefixed with a space are not saved. Useful for secrets.

  setopt HIST_VERIFY
  Show the expanded history command before executing it.

  setopt SHARE_HISTORY
  Share history in real time across all open zsh sessions.
```

### `dotref gtk`

```
📖 GTK › Environment Variables

  Docs: https://docs.gtk.org/gtk3/running.html

──────────────────────────────────────────────────────────────

  GTK_THEME=Adwaita
  Force a specific GTK theme. Append :dark or :light for variant.
  Example: GTK_THEME=Adwaita:dark

  GTK_DEBUG=interactive
  Launch the GTK inspector alongside the app.
  Values: actions, builder, geometry, icontheme, interactive,
          keybindings, modules, printing, size-request, text, tree

  GTK_PATH=/usr/lib/gtk-3.0
  Extra directories to search for GTK modules and backends.

  GTK_IM_MODULE=cedilla
  Override the input method module.

  GTK_OVERLAY_SCROLLING=0
  Disable overlay (auto-hide) scrollbars. GTK3 only, removed in GTK4.

  GDK_BACKEND=wayland,x11,*
  Force a specific GDK rendering backend.
  Values: wayland, x11, broadway
```

---

## 📦 Proposed Subsystems

| Subsystem | Description | Source |
|-----------|-------------|--------|
| `xdg` | Base directories, user dirs, portals | freedesktop.org spec |
| `zsh` | Parameters, setopts, completion | man zshparam, man zshoptions |
| `bash` | Variables, shopts | man bash |
| `gtk` / `gdk` | Theming, rendering, debug | docs.gtk.org |
| `qt` | Platform, scaling, theming | doc.qt.io |
| `wayland` | Compositor, backend, display | wayland.freedesktop.org |
| `x11` | Display, rendering, input | x.org |
| `sdl` | Video, audio, input hints | wiki.libsdl.org |
| `mesa` | GPU drivers, rendering | docs.mesa3d.org |
| `nvidia` | Driver-specific vars | NVIDIA docs |
| `dbus` | Session bus, activation | dbus.freedesktop.org |
| `locale` | Language, encoding, formats | man locale |
| `color` | NO_COLOR, COLORTERM, color scheme | no-color.org |
| `cursor` | Theme, size | XCURSOR_* vars |

---

## 🗂️ Proposed Data Format

Each subsystem is a plain `.toml` file in `data/<subsystem>/`. Simple to edit, easy to diff, and easy to contribute without knowing how to code.

```toml
# data/zsh/history.toml

[meta]
subsystem = "zsh"
category  = "history"
docs      = "https://zsh.sourceforge.io/Doc/Release/Parameters.html"

[[entry]]
type        = "parameter"
key         = "HISTFILE"
default     = "~/.zsh_history"
description = "Path to the file where history is persisted across sessions."

[[entry]]
type        = "parameter"
key         = "HISTSIZE"
default     = "1000"
description = "Max number of events kept in memory during a session."

[[entry]]
type        = "parameter"
key         = "SAVEHIST"
default     = "1000"
description = "Max events written to HISTFILE on exit. Should be <= HISTSIZE."

[[entry]]
type        = "setopt"
key         = "HIST_IGNORE_DUPS"
description = "Don't record a command if identical to the previous one."

[[entry]]
type        = "setopt"
key         = "HIST_IGNORE_SPACE"
description = "Commands prefixed with a space are not saved. Useful for secrets."
```

### Entry types

| Type | Meaning |
|------|---------|
| `env` | Runtime environment variable (`export FOO=bar`) |
| `parameter` | Shell parameter (ZSH / Bash built-in variable) |
| `setopt` | ZSH `setopt` option |
| `shopt` | Bash `shopt` option |
| `flag` | Command-line flag configurable via env or config file |

---

## 📊 Why Not Just Use the Man Page?

| | `man zsh` | `dotref zsh` |
|---|---|---|
| Finds `HISTFILE` | ✅ eventually | ✅ instantly |
| Finds `GTK_THEME` | ❌ wrong man page | ✅ |
| Shows default values | ⚠️ sometimes | ✅ always |
| Searchable by keyword | ⚠️ only inside pager | ✅ `dotref search` |
| Cross-subsystem search | ❌ | ✅ |
| Scannable at a glance | ❌ | ✅ |

---

## 📚 Sources Per Subsystem

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

## 🔍 Prior Art & Related Tools

| Tool | What it does | The gap |
|------|-------------|---------|
| [tldr-pages](https://github.com/tldr-pages/tldr) | Short CLI command reference | Commands only, not configuration knobs |
| [navi](https://github.com/denisidoro/navi) | Interactive cheatsheet runner | Commands only, no env var database |
| [cheat](https://github.com/cheat/cheat) | Personal cheatsheets | Not curated per subsystem |
| Arch Wiki | Excellent env var docs | Browser only, not searchable from terminal |
| `man` pages | Authoritative and exhaustive | Slow, verbose, no cross-subsystem search |

`dotref` fills the gap none of these cover.

---

## 🚀 Project Status

This is currently a **concept / RFC**. It does not exist yet as a working tool.

**If you're a developer who wants to build this:**

- The CLI itself is probably ~200 lines of Python, Go, or Rust
- The real value is in the database — and that can be crowdsourced
- The format is intentionally simple so anyone can contribute a `.toml` file
- A minimal `v0.1` with just ZSH + GTK + XDG would already be immediately useful

> 💬 **Open an issue if you want to build this, discuss the format, or contribute data for a subsystem.** PRs with just `.toml` data files are very welcome — you don't need to know how to code.

---

## 🤝 Contributing an Entry

You don't need to know how to code. Contributing is just editing a TOML file:

1. Fork this repo
2. Find or create `data/<subsystem>/<category>.toml`
3. Add your entry following the format above
4. Open a PR with a link to the source documentation

---

## ⚖️ License

MIT — do whatever you want with it.

---

<div align="center">
  <sub>Born from typing <code>man zsh</code> one too many times just to find <code>HISTFILE</code>.</sub>
</div>
