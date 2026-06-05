import pytest
import os
import tempfile
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_manager import load_config, save_config, hard_reset, DEFAULT_CONFIG, CONFIG_FILE, MARKER_FILE


@pytest.fixture(scope="function")
def clean_environment():
    """Fixture to ensure a clean slate before each test."""
    # Clean up before test
    if MARKER_FILE.exists():
        MARKER_FILE.unlink()
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
    yield
    # Cleanup after test
    if MARKER_FILE.exists():
        MARKER_FILE.unlink()
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()


def test_default_config_load_empty(clean_environment):
    """Tests that load_config returns defaults when no configuration file exists."""
    config = load_config()
    assert isinstance(config, dict)
    assert config["logo_color"] == "BLUE"
    assert config["hardware_monitoring"] is True
    assert config["web_search_enabled"] is True


def test_save_and_load_config(clean_environment):
    """Tests the full save/load cycle of configuration."""
    test_config = {
        "logo_color": "CYAN",
        "hardware_monitoring": False,
        "web_search_enabled": False,
        "app_launcher_active": True,
        "autostart_enabled": True
    }

    save_config(test_config)
    loaded_config = load_config()

    assert loaded_config["logo_color"] == "CYAN"
    assert loaded_config["hardware_monitoring"] is False
    assert loaded_config["app_launcher_active"] is True
    assert loaded_config["autostart_enabled"] is True


def test_hard_reset_removes_files(clean_environment):
    """Tests that hard_reset successfully cleans up the marker and config files."""
    MARKER_FILE.touch()
    CONFIG_FILE.write_text("{}")

    assert MARKER_FILE.exists()
    assert CONFIG_FILE.exists()

    hard_reset()

    assert not MARKER_FILE.exists()
    assert not CONFIG_FILE.exists()


def test_config_merge_with_defaults(clean_environment):
    """Tests that partial config files are merged with defaults."""
    partial = {"logo_color": "RED"}
    save_config(partial)

    loaded = load_config()
    assert loaded["logo_color"] == "RED"
    assert loaded["hardware_monitoring"] is True  # from default
    assert loaded["autostart_enabled"] is False    # from default
