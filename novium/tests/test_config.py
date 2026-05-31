import pytest
from pathlib import Path
from novium.config_manager import load_config, save_config, hard_reset, DEFAULT_CONFIG, CONFIG_FILE, MARKER_FILE

# --- Fixtures for setup and cleanup ---

@pytest.fixture(scope="module")
def clean_environment():
    """Fixture to ensure a clean slate before running tests."""
    hard_reset() # Uses the function from config_manager which handles cleanup

def test_default_config_load_empty(clean_environment):
    """Tests that load_config returns defaults when no configuration file exists."""
    # Since hard_reset was called, we guarantee no config file exists.
    config = load_config()
    assert isinstance(config, dict)
    # Check a few key default values
    assert config["logo_color"] == "BLUE"
    assert config["hardware_monitoring"] is True

def test_save_and_load_config(clean_environment):
    """Tests the full save/load cycle of configuration."""
    test_config = {
        "logo_color": "CYAN",
        "hardware_monitoring": False,
        "web_search_enabled": False,
        "app_launcher_active": True,
        "autostart_enabled": True
    }

    # 1. Save the test configuration
    save_config(test_config)
    
    # 2. Load and verify
    loaded_config = load_config()
    assert loaded_config == pytest.approx(test_config)

def test_hard_reset_removes_files(clean_environment):
    """Tests that hard_reset successfully cleans up the marker and config files."""
    # Ensure files exist before testing removal
    with open(str(MARKER_FILE), 'w') as f: f.write("test")
    with open(str(CONFIG_FILE), 'w') as f: f.write("{}")
    assert MARKER_FILE.exists() and CONFIG_FILE.exists()

    # Run reset
    hard_reset()

    # Verify files are gone
    assert not MARKER_FILE.exists()
    assert not CONFIG_FILE.exists()