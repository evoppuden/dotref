"""Tests for dotref CLI."""
import os
import sys
import tempfile
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotref import DotrefDB, ConfigKnob, DataNotFoundError


def test_list_subsystems():
    """Test listing subsystems."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = DotrefDB(data_dir=Path(tmpdir))
        # Create test data
        (Path(tmpdir) / "test_sub").mkdir()
        (Path(tmpdir) / "test_sub" / "cat1.toml").write_text("")
        subs = db.list_subsystems()
        assert "test_sub" in subs


def test_get_knobs():
    """Test loading config knobs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = DotrefDB(data_dir=Path(tmpdir))
        # Create test TOML
        toml_content = """
[[knobs]]
name = "TEST_VAR"
description = "A test variable"
default = "test"
example = "export TEST_VAR=test"
"""
        (Path(tmpdir) / "test_sub").mkdir()
        (Path(tmpdir) / "test_sub" / "test.toml").write_text(toml_content)
        
        knobs = db.get_knobs("test_sub", "test")
        assert len(knobs) == 1
        assert knobs[0].name == "TEST_VAR"
        assert knobs[0].description == "A test variable"


def test_search():
    """Test search functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = DotrefDB(data_dir=Path(tmpdir))
        toml_content = """
[[knobs]]
name = "HISTFILE"
description = "ZSH history file path"
default = "~/.zsh_history"
"""
        (Path(tmpdir) / "zsh").mkdir()
        (Path(tmpdir) / "zsh" / "history.toml").write_text(toml_content)
        
        results = db.search("history")
        assert len(results) == 1
        assert results[0].name == "HISTFILE"


def test_data_not_found():
    """Test error handling for missing data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = DotrefDB(data_dir=Path(tmpdir))
        try:
            db.get_knobs("nonexistent", "category")
            assert False, "Should have raised DataNotFoundError"
        except DataNotFoundError:
            pass


if __name__ == "__main__":
    test_list_subsystems()
    test_get_knobs()
    test_search()
    test_data_not_found()
    print("All tests passed!")
