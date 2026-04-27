#!/usr/bin/env python3
"""dotref - Linux configuration reference CLI tool.

Like tldr but for Linux configuration knobs: environment variables,
shell parameters, and setopts for subsystems like ZSH, GTK, XDG, Qt, Wayland.

Usage:
    dotref <subsystem>                    # List all categories for a subsystem
    dotref <subsystem> <category>         # Show config knobs for a category
    dotref search <keyword>               # Search across all subsystems
    dotref list                           # List all available subsystems
    dotref update                         # Update local data from remote repo
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback

try:
    import requests
except ImportError:
    requests = None

__version__ = "0.1.0"

# Default data source
DEFAULT_DATA_URL = "https://raw.githubusercontent.com/evoppuden/dotref/main/data"
DEFAULT_DATA_DIR = Path.home() / ".dotref" / "data"


class DotrefError(Exception):
    """Base error for dotref."""
    pass


class DataNotFoundError(DotrefError):
    """Raised when requested data is not found."""
    pass


class ConfigKnob:
    """Represents a single configuration knob entry."""

    def __init__(self, name: str, description: str, example: str = "",
                 default: str = "", category: str = ""):
        self.name = name
        self.description = description
        self.example = example
        self.default = default
        self.category = category

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "example": self.example,
            "default": self.default,
            "category": self.category,
        }


class DotrefDB:
    """Manages the local dotref database."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or DEFAULT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def list_subsystems(self) -> list[str]:
        """List all available subsystems."""
        if not self.data_dir.exists():
            return []
        return sorted([
            d.name for d in self.data_dir.iterdir() if d.is_dir()
        ])

    def list_categories(self, subsystem: str) -> list[str]:
        """List categories for a subsystem."""
        subsystem_dir = self.data_dir / subsystem
        if not subsystem_dir.exists():
            raise DataNotFoundError(f"Subsystem '{subsystem}' not found. Run 'dotref list' to see available subsystems.")
        return sorted([
            f.stem for f in subsystem_dir.glob("*.toml")
        ])

    def load_toml(self, subsystem: str, category: str) -> dict:
        """Load a TOML data file."""
        toml_path = self.data_dir / subsystem / f"{category}.toml"
        if not toml_path.exists():
            raise DataNotFoundError(
                f"Data file not found: {toml_path}\n"
                f"Run 'dotref {subsystem}' to see available categories."
            )
        with open(toml_path, "rb") as f:
            return tomllib.load(f)

    def get_knobs(self, subsystem: str, category: str) -> list[ConfigKnob]:
        """Get all config knobs for a subsystem/category."""
        data = self.load_toml(subsystem, category)
        knobs = []
        for entry in data.get("knob", {}).values():
            knobs.append(ConfigKnob(
                name=entry.get("name", ""),
                description=entry.get("description", ""),
                example=entry.get("example", ""),
                default=entry.get("default", ""),
                category=category,
            ))
        return knobs

    def search(self, keyword: str) -> list[ConfigKnob]:
        """Search across all subsystems and categories."""
        results = []
        keyword_lower = keyword.lower()
        for subsystem in self.list_subsystems():
            for category in self.list_categories(subsystem):
                try:
                    knobs = self.get_knobs(subsystem, category)
                    for knob in knobs:
                        if (keyword_lower in knob.name.lower() or
                            keyword_lower in knob.description.lower()):
                            knob.category = f"{subsystem}/{category}"
                            results.append(knob)
                except DataNotFoundError:
                    continue
        return results

    def update(self) -> int:
        """Update local data from remote repository."""
        if requests is None:
            raise DotrefError(
                "requests library not installed. Install with: pip install requests\n"
                "Or manually clone: git clone https://github.com/evoppuden/dotref.git"
            )
        # For now, just inform user to clone the repo
        print("To get the latest data, run:")
        print("  git clone https://github.com/evoppuden/dotref.git")
        print("  cp -r dotref/data ~/.dotref/data")
        return 0


def format_knob(knob: ConfigKnob, show_category: bool = False) -> str:
    """Format a single knob for display."""
    lines = []
    prefix = f"[{knob.category}] " if show_category else ""
    lines.append(f"\n  {prefix}{knob.name}")
    lines.append(f"    {knob.description}")
    if knob.default:
        lines.append(f"    Default: {knob.default}")
    if knob.example:
        lines.append(f"    Example: {knob.example}")
    return "\n".join(lines)


def format_results(knobs: list[ConfigKnob], subsystem: str = "",
                   category: str = "", show_category: bool = False) -> str:
    """Format search/list results for display."""
    if not knobs:
        return "No results found."

    lines = []
    if subsystem and category:
        lines.append(f"\n# {subsystem} - {category}")
        lines.append("=" * 40)
    elif show_category:
        lines.append(f"\n# Search Results")
        lines.append("=" * 40)

    for knob in knobs:
        lines.append(format_knob(knob, show_category))

    return "\n".join(lines)


def cmd_list(db: DotrefDB, args: argparse.Namespace) -> None:
    """Handle 'dotref list' command."""
    subsystems = db.list_subsystems()
    if not subsystems:
        print("No data available. Run 'dotref update' to fetch data.")
        return
    print(f"\nAvailable subsystems ({len(subsystems)}):\n")
    for s in subsystems:
        categories = db.list_categories(s)
        print(f"  {s} ({len(categories)} categories)")
    print()


def cmd_show(db: DotrefDB, args: argparse.Namespace) -> None:
    """Handle 'dotref <subsystem> [category]' command."""
    subsystem = args.subsystem
    if args.category:
        # Show specific category
        try:
            knobs = db.get_knobs(subsystem, args.category)
            print(format_results(knobs, subsystem, args.category))
        except DataNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # List categories for subsystem
        try:
            categories = db.list_categories(subsystem)
            print(f"\n# {subsystem} - Categories\n")
            for cat in categories:
                print(f"  {cat}")
            print(f"\n  Use 'dotref {subsystem} <category>' to view details.\n")
        except DataNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


def cmd_search(db: DotrefDB, args: argparse.Namespace) -> None:
    """Handle 'dotref search <keyword>' command."""
    keyword = args.keyword
    results = db.search(keyword)
    print(format_results(results, show_category=True))
    if results:
        print(f"\n  Found {len(results)} result(s) for '{keyword}'.\n")
    else:
        print(f"\n  No results for '{keyword}'. Try a different keyword.\n")


def cmd_update(db: DotrefDB, args: argparse.Namespace) -> None:
    """Handle 'dotref update' command."""
    db.update()


def cmd_version(db: DotrefDB, args: argparse.Namespace) -> None:
    """Handle 'dotref --version'."""
    print(f"dotref v{__version__}")


def main():
    parser = argparse.ArgumentParser(
        prog="dotref",
        description="Linux configuration reference tool - like tldr for dotfiles",
    )
    parser.add_argument("--version", action="store_true", help="Show version")
    parser.add_argument("--data-dir", type=Path, default=None,
                        help="Custom data directory")

    subparsers = parser.add_subparsers(dest="command")

    # list
    list_parser = subparsers.add_parser("list", help="List available subsystems")
    list_parser.set_defaults(func=cmd_list)

    # search
    search_parser = subparsers.add_parser("search", help="Search across all subsystems")
    search_parser.add_argument("keyword", help="Search keyword")
    search_parser.set_defaults(func=cmd_search)

    # update
    update_parser = subparsers.add_parser("update", help="Update local data")
    update_parser.set_defaults(func=cmd_update)

    # version
    version_parser = subparsers.add_parser("version", help="Show version")
    version_parser.set_defaults(func=cmd_version)

    # positional: subsystem [category]
    show_parser = subparsers.add_parser("show", help="Show config for a subsystem/category")
    show_parser.add_argument("subsystem", help="Subsystem name (e.g., zsh, gtk)")
    show_parser.add_argument("category", nargs="?", default=None,
                             help="Category name (e.g., history, theme)")
    show_parser.set_defaults(func=cmd_show)

    args = parser.parse_args()

    if args.version:
        cmd_version(None, args)
        return

    if not args.command:
        parser.print_help()
        return

    db = DotrefDB(data_dir=args.data_dir)
    args.func(db, args)


if __name__ == "__main__":
    main()
