#!/usr/bin/env python3
"""dotref - Linux configuration reference CLI tool.

Like tldr but for Linux configuration knobs: environment variables,
shell parameters, setopts, and config-file directives.

Usage:
    dotref                                # Interactive picker (requires fzf)
    dotref <subsystem>                    # List categories for a subsystem
    dotref <subsystem> <category>         # Show knobs for a category
    dotref <subsystem> <name>             # Show one knob by name (e.g. dotref zsh HISTFILE)
    dotref list                           # List all available subsystems
    dotref search <keyword>               # Search across all subsystems (ranked)
    dotref pick                           # Interactive picker (explicit)
    dotref update                         # Update local data from remote repo
    dotref version                        # Show version

Output flags:
    --json                                # Emit machine-readable JSON
    --plain                               # Plain text, no ANSI colors

Color is enabled when stdout is a TTY. Override with NO_COLOR=1 or FORCE_COLOR=1.
"""

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib

__version__ = "0.2.0"

UPDATE_TARBALL_URL = "https://codeload.github.com/evoppuden/dotref/tar.gz/refs/heads/main"
DEFAULT_DATA_DIR = Path.home() / ".dotref" / "data"

RESERVED_COMMANDS = {"list", "search", "update", "version", "pick"}


# ─────────────────────────────────────────────────────────────────────────────
# Colors
# ─────────────────────────────────────────────────────────────────────────────

_color_cache: Optional[bool] = None
_force_no_color: bool = False  # set by --plain / --json


def _use_color() -> bool:
    global _color_cache
    if _force_no_color:
        return False
    if _color_cache is None:
        if os.environ.get("NO_COLOR"):
            _color_cache = False
        elif os.environ.get("FORCE_COLOR"):
            _color_cache = True
        else:
            _color_cache = sys.stdout.isatty()
    return _color_cache


def _paint(s: str, code: str) -> str:
    if not s or not _use_color():
        return s
    return f"\033[{code}m{s}\033[0m"


def c_subsystem(s: str) -> str: return _paint(s, "1;36")    # bold cyan
def c_category(s: str)  -> str: return _paint(s, "1;34")    # bold blue
def c_name(s: str)      -> str: return _paint(s, "1")       # bold
def c_default(s: str)   -> str: return _paint(s, "2")       # dim
def c_example(s: str)   -> str: return _paint(s, "33")      # yellow
def c_label(s: str)     -> str: return _paint(s, "2")       # dim
def c_count(s: str)     -> str: return _paint(s, "2")       # dim
def c_header(s: str)    -> str: return _paint(s, "1;37")    # bold white
def c_sep(s: str)       -> str: return _paint(s, "2")       # dim
def c_url(s: str)       -> str: return _paint(s, "4;36")    # underlined cyan


_TYPE_CODES = {
    "env":       "32",   # green
    "setopt":    "35",   # magenta
    "shopt":     "35",   # magenta
    "parameter": "36",   # cyan
    "config":    "34",   # blue
    "flag":      "33",   # yellow
}


def c_type(knob_type: str) -> str:
    if not knob_type:
        return ""
    code = _TYPE_CODES.get(knob_type, "2")
    return _paint(f"({knob_type})", code)


# ─────────────────────────────────────────────────────────────────────────────
# Errors
# ─────────────────────────────────────────────────────────────────────────────

class DotrefError(Exception):
    pass


class DataNotFoundError(DotrefError):
    pass


# ─────────────────────────────────────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────────────────────────────────────

class ConfigKnob:
    def __init__(self, name: str, description: str, example: str = "",
                 default: str = "", category: str = "", knob_type: str = "",
                 subsystem: str = ""):
        self.name = name
        self.description = description
        self.example = example
        self.default = default
        self.category = category
        self.type = knob_type
        self.subsystem = subsystem

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "example": self.example,
            "default": self.default,
            "category": self.category,
            "type": self.type,
            "subsystem": self.subsystem,
        }


def _bundled_data_dir() -> Optional[Path]:
    """Return the directory that ships the seed database, or None if unavailable.

    Looks first beside dotref.py (editable install / running from a checkout),
    then in standard data-files locations populated by `pip install`.
    """
    here = Path(__file__).resolve().parent
    candidates = [
        here / "data",
        Path(sys.prefix) / "share" / "dotref" / "data",
        Path.home() / ".local" / "share" / "dotref" / "data",
    ]
    for c in candidates:
        if c.is_dir() and any(c.iterdir()):
            return c
    return None


def _copy_tree(src: Path, dest: Path) -> None:
    """Copy every file/dir in src into dest, creating dest if needed."""
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dest / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


class DotrefDB:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or DEFAULT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._maybe_bootstrap()

    def _maybe_bootstrap(self) -> None:
        """Seed an empty data directory from the bundled database on first run."""
        if any(self.data_dir.iterdir()):
            return
        src = _bundled_data_dir()
        if src is None or src.resolve() == self.data_dir.resolve():
            return
        print(f"dotref: bootstrapping data into {self.data_dir} (from {src})",
              file=sys.stderr)
        _copy_tree(src, self.data_dir)

    def list_subsystems(self) -> list[str]:
        if not self.data_dir.exists():
            return []
        return sorted([d.name for d in self.data_dir.iterdir() if d.is_dir()])

    def list_categories(self, subsystem: str) -> list[str]:
        subsystem_dir = self.data_dir / subsystem
        if not subsystem_dir.exists():
            raise DataNotFoundError(
                f"Subsystem '{subsystem}' not found. Run 'dotref list' to see available subsystems."
            )
        return sorted([f.stem for f in subsystem_dir.glob("*.toml")])

    def load_toml(self, subsystem: str, category: str) -> dict:
        toml_path = self.data_dir / subsystem / f"{category}.toml"
        if not toml_path.exists():
            raise DataNotFoundError(
                f"Data file not found: {toml_path}\n"
                f"Run 'dotref {subsystem}' to see available categories."
            )
        with open(toml_path, "rb") as f:
            return tomllib.load(f)

    def get_meta(self, subsystem: str, category: str) -> dict:
        try:
            data = self.load_toml(subsystem, category)
        except DataNotFoundError:
            return {}
        meta = data.get("meta", {})
        return meta if isinstance(meta, dict) else {}

    def get_knobs(self, subsystem: str, category: str) -> list[ConfigKnob]:
        data = self.load_toml(subsystem, category)
        knobs = []
        for entry in data.get("knob", {}).values():
            knobs.append(ConfigKnob(
                name=entry.get("name", ""),
                description=entry.get("description", ""),
                example=entry.get("example", ""),
                default=entry.get("default", ""),
                category=category,
                knob_type=entry.get("type", ""),
                subsystem=subsystem,
            ))
        return knobs

    def find_knob(self, subsystem: str, name: str) -> Optional[tuple[str, ConfigKnob]]:
        """Find a knob in <subsystem> by exact name (case-insensitive).
        Returns (category, ConfigKnob) or None.
        """
        try:
            cats = self.list_categories(subsystem)
        except DataNotFoundError:
            return None
        target = name.lower()
        for cat in cats:
            try:
                for k in self.get_knobs(subsystem, cat):
                    if k.name.lower() == target:
                        return cat, k
            except DataNotFoundError:
                continue
        return None

    def search(self, keyword: str) -> list[ConfigKnob]:
        """Ranked search.

        Tier 0: exact name match
        Tier 1: name prefix
        Tier 2: name substring
        Tier 3: description substring
        Subsystem-name keyword bumps matches in that subsystem by half a tier.
        """
        kw = keyword.lower()
        ranked: list[tuple[float, str, ConfigKnob]] = []
        for subsystem in self.list_subsystems():
            try:
                cats = self.list_categories(subsystem)
            except DataNotFoundError:
                continue
            sub_boost = 0.5 if subsystem.lower() == kw else 0.0
            for category in cats:
                try:
                    knobs = self.get_knobs(subsystem, category)
                except DataNotFoundError:
                    continue
                for knob in knobs:
                    nm = knob.name.lower()
                    desc = knob.description.lower()
                    if nm == kw:
                        rank = 0.0
                    elif nm.startswith(kw):
                        rank = 1.0
                    elif kw in nm:
                        rank = 2.0
                    elif kw in desc:
                        rank = 3.0
                    else:
                        continue
                    rank -= sub_boost
                    knob.category = f"{subsystem}/{category}"
                    ranked.append((rank, knob.name.lower(), knob))
        ranked.sort(key=lambda t: (t[0], t[1]))
        return [k for _, _, k in ranked]

    def update(self) -> int:
        """Fetch the latest data/ tree from the official repo and replace
        self.data_dir atomically. Refuses to operate inside a git checkout."""
        # Refuse if data_dir lives inside a git working tree — almost
        # certainly a developer running `dotref update --data-dir ./data`.
        probe = self.data_dir.resolve()
        for parent in [probe, *probe.parents]:
            if (parent / ".git").exists():
                raise DotrefError(
                    f"Refusing to update {self.data_dir}: it is inside a git "
                    f"checkout ({parent}). Run dotref update against the "
                    f"default location (~/.dotref/data)."
                )

        print(f"dotref: fetching {UPDATE_TARBALL_URL}", file=sys.stderr)
        with tempfile.TemporaryDirectory(prefix="dotref-update-") as tmp:
            tmp_dir = Path(tmp)
            tarball = tmp_dir / "dotref.tar.gz"
            try:
                with urllib.request.urlopen(UPDATE_TARBALL_URL, timeout=30) as resp, \
                     open(tarball, "wb") as out:
                    shutil.copyfileobj(resp, out)
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                raise DotrefError(f"Failed to download update: {e}") from e

            extract_dir = tmp_dir / "extract"
            extract_dir.mkdir()
            try:
                with tarfile.open(tarball, "r:gz") as tar:
                    members = [
                        m for m in tar.getmembers()
                        if len(Path(m.name).parts) >= 2
                        and Path(m.name).parts[1] == "data"
                    ]
                    if not members:
                        raise DotrefError("Update tarball contains no data/ tree.")
                    # Python 3.12+ requires an explicit filter; older versions
                    # don't accept the kwarg.
                    try:
                        tar.extractall(extract_dir, members=members, filter="data")
                    except TypeError:
                        tar.extractall(extract_dir, members=members)
            except tarfile.TarError as e:
                raise DotrefError(f"Failed to extract update: {e}") from e

            new_data_candidates = list(extract_dir.glob("*/data"))
            if not new_data_candidates:
                raise DotrefError("Extracted archive missing a data/ directory.")
            new_data = new_data_candidates[0]

            # Atomic-ish replace: move old aside, move new in, delete old.
            backup = self.data_dir.with_name(self.data_dir.name + ".bak")
            if backup.exists():
                shutil.rmtree(backup)
            had_old = self.data_dir.exists()
            if had_old:
                shutil.move(str(self.data_dir), str(backup))
            try:
                shutil.move(str(new_data), str(self.data_dir))
            except Exception:
                if had_old and backup.exists():
                    shutil.move(str(backup), str(self.data_dir))
                raise
            if backup.exists():
                shutil.rmtree(backup)

        # Quick post-update sanity check.
        subs = self.list_subsystems()
        print(f"dotref: updated {self.data_dir} ({len(subs)} subsystems)",
              file=sys.stderr)
        return 0


# ─────────────────────────────────────────────────────────────────────────────
# Formatting
# ─────────────────────────────────────────────────────────────────────────────

def format_knob(knob: ConfigKnob, show_category: bool = False) -> str:
    cat_prefix = ""
    if show_category and knob.category:
        if "/" in knob.category:
            sub, cat = knob.category.split("/", 1)
            cat_prefix = f"[{c_subsystem(sub)}/{c_category(cat)}] "
        else:
            cat_prefix = f"[{c_category(knob.category)}] "

    type_suffix = f"  {c_type(knob.type)}" if knob.type else ""
    lines = [f"\n  {cat_prefix}{c_name(knob.name)}{type_suffix}"]
    lines.append(f"    {knob.description}")
    if knob.default:
        lines.append(f"    {c_label('default:')} {c_default(knob.default)}")
    if knob.example:
        lines.append(f"    {c_label('example:')} {c_example(knob.example)}")
    return "\n".join(lines)


def format_results(knobs: list[ConfigKnob], subsystem: str = "",
                   category: str = "", show_category: bool = False,
                   meta: Optional[dict] = None) -> str:
    if not knobs:
        return "No results found."
    lines = []
    if subsystem and category:
        lines.append(f"\n# {c_subsystem(subsystem)} - {c_category(category)}")
        if meta and meta.get("docs"):
            lines.append(f"  {c_label('docs:')} {c_url(meta['docs'])}")
        lines.append(c_sep("=" * 40))
    elif show_category:
        lines.append(f"\n# {c_header('Search Results')}")
        lines.append(c_sep("=" * 40))
    for knob in knobs:
        lines.append(format_knob(knob, show_category))
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────

def cmd_list(db: DotrefDB, output_format: str = "text") -> None:
    subsystems = db.list_subsystems()
    if output_format == "json":
        out = []
        for s in subsystems:
            try:
                out.append({"subsystem": s, "categories": db.list_categories(s)})
            except DataNotFoundError:
                out.append({"subsystem": s, "categories": []})
        print(json.dumps(out, indent=2))
        return
    if not subsystems:
        print("No data available. Run 'dotref update' to fetch data.")
        return
    print(f"\nAvailable subsystems ({len(subsystems)}):\n")
    for s in subsystems:
        cats = db.list_categories(s)
        print(f"  {c_subsystem(s)}  {c_count(f'({len(cats)} categories)')}")
    print()


def cmd_show(db: DotrefDB, subsystem: str, second_arg: Optional[str],
             output_format: str = "text") -> None:
    """Render either a category or a single knob.

    `dotref <sub>`              -> list categories
    `dotref <sub> <category>`   -> render category
    `dotref <sub> <knob_name>`  -> render the single knob (fallback when
                                   second_arg is not a category file)
    """
    # No second arg → list categories.
    if not second_arg:
        try:
            categories = db.list_categories(subsystem)
        except DataNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        if output_format == "json":
            print(json.dumps({"subsystem": subsystem, "categories": categories},
                             indent=2))
            return
        print(f"\n# {c_subsystem(subsystem)} - Categories\n")
        for cat in categories:
            print(f"  {c_category(cat)}")
        print(f"\n  Use 'dotref {subsystem} <category>' to view details.\n")
        return

    # Second arg is a category file → render that category.
    try:
        cats = db.list_categories(subsystem)
    except DataNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if second_arg in cats:
        try:
            knobs = db.get_knobs(subsystem, second_arg)
            meta = db.get_meta(subsystem, second_arg)
        except DataNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        if output_format == "json":
            payload = {
                "subsystem": subsystem,
                "category": second_arg,
                "meta": meta,
                "knobs": [k.to_dict() for k in knobs],
            }
            print(json.dumps(payload, indent=2))
            return
        print(format_results(knobs, subsystem, second_arg, meta=meta))
        return

    # Not a category — try direct knob lookup.
    hit = db.find_knob(subsystem, second_arg)
    if hit is None:
        print(
            f"Error: '{second_arg}' is not a category or known knob in '{subsystem}'.\n"
            f"Categories: {', '.join(cats) or '(none)'}\n"
            f"Try: dotref search {second_arg}",
            file=sys.stderr,
        )
        sys.exit(1)
    cat, knob = hit
    if output_format == "json":
        print(json.dumps(knob.to_dict(), indent=2))
        return
    meta = db.get_meta(subsystem, cat)
    print(f"\n# {c_subsystem(subsystem)} / {c_category(cat)}")
    if meta.get("docs"):
        print(f"  {c_label('docs:')} {c_url(meta['docs'])}")
    print(c_sep("=" * 40))
    print(format_knob(knob))
    print()


def cmd_search(db: DotrefDB, keyword: str, output_format: str = "text") -> None:
    results = db.search(keyword)
    if output_format == "json":
        print(json.dumps([k.to_dict() for k in results], indent=2))
        return
    print(format_results(results, show_category=True))
    if results:
        print(f"\n  Found {len(results)} result(s) for '{keyword}'.\n")
    else:
        print(f"\n  No results for '{keyword}'. Try a different keyword.\n")


def cmd_update(db: DotrefDB) -> None:
    try:
        db.update()
    except DotrefError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# fzf picker
# ─────────────────────────────────────────────────────────────────────────────

def _all_knobs(db: DotrefDB):
    """Yield (subsystem, category, ConfigKnob) for every knob in the DB."""
    for sub in db.list_subsystems():
        try:
            cats = db.list_categories(sub)
        except DataNotFoundError:
            continue
        for cat in cats:
            try:
                for k in db.get_knobs(sub, cat):
                    yield sub, cat, k
            except DataNotFoundError:
                continue


def cmd_pick(db: DotrefDB) -> None:
    if not shutil.which("fzf"):
        print(
            "fzf not found. Install fzf to use the interactive picker:\n"
            "  https://github.com/junegunn/fzf\n\n"
            "Or use: dotref list, dotref <subsystem>, dotref search <keyword>",
            file=sys.stderr,
        )
        sys.exit(1)

    items = list(_all_knobs(db))
    if not items:
        print("No knobs available. Run 'dotref update' to fetch data.", file=sys.stderr)
        sys.exit(1)

    # Tab-separated: <path>\t<colored display>
    # --with-nth=2.. hides path from display; --preview uses {1} (path).
    lines = []
    for sub, cat, k in items:
        path = f"{sub}/{cat}/{k.name}"
        type_tag = f"  {c_type(k.type)}" if k.type else ""
        display = (
            f"{c_subsystem(sub)}/{c_category(cat)}/{c_name(k.name)}"
            f"{type_tag}  {c_sep('—')} {k.description}"
        )
        lines.append(f"{path}\t{display}")
    fzf_input = "\n".join(lines)

    script = os.path.abspath(__file__)
    preview_cmd = (
        f"{shlex.quote(sys.executable)} {shlex.quote(script)} "
        f"--data-dir {shlex.quote(str(db.data_dir))} --preview-knob {{1}}"
    )

    env = os.environ.copy()
    env["FORCE_COLOR"] = "1"  # ensure colors in the preview subprocess

    cmd = [
        "fzf",
        "--ansi",
        "--delimiter", "\t",
        "--with-nth", "2..",
        "--preview", preview_cmd,
        "--preview-window", "right:55%:wrap",
        "--prompt", "knob❯ ",
        "--header", "dotref — pick a knob (enter to print, esc to quit)",
        "--height", "90%",
        "--layout", "reverse",
        "--border",
    ]

    try:
        proc = subprocess.run(
            cmd, input=fzf_input, text=True, capture_output=True, env=env
        )
    except KeyboardInterrupt:
        return

    if proc.returncode != 0:
        return  # cancelled or no match

    selected = proc.stdout.strip()
    if not selected:
        return

    path = selected.split("\t", 1)[0]
    cmd_preview_knob(db, path)


def cmd_preview_knob(db: DotrefDB, path: str) -> None:
    """Print rich detail for a single knob. Used by fzf --preview and pick result."""
    parts = path.split("/", 2)
    if len(parts) != 3:
        return
    sub, cat, name = parts
    try:
        knobs = db.get_knobs(sub, cat)
    except DataNotFoundError:
        return
    matches = [k for k in knobs if k.name == name]
    if not matches:
        return
    k = matches[0]
    meta = db.get_meta(sub, cat)

    out = []
    out.append(f"{c_subsystem(sub)} {c_sep('/')} {c_category(cat)}")
    out.append("")
    type_tag = f"  {c_type(k.type)}" if k.type else ""
    out.append(f"{c_name(k.name)}{type_tag}")
    out.append("")
    out.append(k.description)
    if k.default:
        out.append("")
        out.append(f"{c_label('default:')} {c_default(k.default)}")
    if k.example:
        out.append("")
        out.append(f"{c_label('example:')}")
        out.append(f"  {c_example(k.example)}")
    if meta.get("docs"):
        out.append("")
        out.append(f"{c_label('docs:')} {c_url(meta['docs'])}")
    print("\n".join(out))


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def print_help() -> None:
    print(__doc__)


def main():
    parser = argparse.ArgumentParser(prog="dotref", add_help=False)
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--preview-knob", type=str, default=None,
                        help=argparse.SUPPRESS)
    parser.add_argument("--json", action="store_true",
                        help="Emit machine-readable JSON")
    parser.add_argument("--plain", action="store_true",
                        help="Plain text, no ANSI colors")
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("args", nargs="*")

    parsed = parser.parse_args()

    # JSON and plain both disable color output.
    global _force_no_color
    if parsed.json or parsed.plain:
        _force_no_color = True

    output_format = "json" if parsed.json else "text"

    if parsed.version:
        if output_format == "json":
            print(json.dumps({"version": __version__}))
        else:
            print(f"dotref v{__version__}")
        return

    db = DotrefDB(data_dir=parsed.data_dir)

    if parsed.preview_knob:
        cmd_preview_knob(db, parsed.preview_knob)
        return

    if parsed.help:
        print_help()
        return

    if not parsed.args:
        # No args: launch picker if fzf is available, otherwise show help.
        # JSON mode skips the picker (it's interactive).
        if output_format == "text" and shutil.which("fzf"):
            cmd_pick(db)
        else:
            print_help()
        return

    cmd = parsed.args[0]
    rest = parsed.args[1:]

    if cmd == "list":
        cmd_list(db, output_format=output_format)
    elif cmd == "search":
        if not rest:
            print("Error: 'search' requires a keyword.\nUsage: dotref search <keyword>",
                  file=sys.stderr)
            sys.exit(2)
        cmd_search(db, rest[0], output_format=output_format)
    elif cmd == "pick":
        cmd_pick(db)
    elif cmd == "update":
        cmd_update(db)
    elif cmd == "version":
        if output_format == "json":
            print(json.dumps({"version": __version__}))
        else:
            print(f"dotref v{__version__}")
    else:
        if len(rest) > 1:
            print("Error: too many arguments.\nUsage: dotref <subsystem> [category|knob]",
                  file=sys.stderr)
            sys.exit(2)
        second = rest[0] if rest else None
        cmd_show(db, cmd, second, output_format=output_format)


if __name__ == "__main__":
    main()
