"""
font_manager.py - Font management for Novium

Handles font configuration, loading, and path resolution.
Supports switching between bundled fonts and system defaults.
"""

import os
import json
from pathlib import Path

# Project root directory
SCRIPT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
FONTS_DIR = SCRIPT_DIR / "assets" / "fonts"

# Available fonts
AVAILABLE_FONTS = {
    "default": "System Default",
    "monocraft": "Monocraft"
}

# Default font configuration
DEFAULT_CONFIG = {
    "font": "default"
}


def load_config():
    """Loads configuration from disk, or returns default if not found."""
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    try:
        with CONFIG_FILE.open('r', encoding='utf-8') as f:
            data = json.load(f)
        return {**DEFAULT_CONFIG, **data}
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config):
    """Saves the given configuration dictionary to disk."""
    try:
        with CONFIG_FILE.open('w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception:
        return False


def set_font(font_name):
    """
    Sets the font in config.json.
    
    Args:
        font_name: Name of the font to use (e.g., 'monocraft', 'default')
    
    Returns:
        tuple: (success: bool, message: str)
    """
    font_name = font_name.lower().strip()
    
    if font_name not in AVAILABLE_FONTS:
        return False, f"Invalid font: {font_name}. Available: {', '.join(AVAILABLE_FONTS.keys())}"
    
    config = load_config()
    config['font'] = font_name
    
    if save_config(config):
        return True, f"Font set to {AVAILABLE_FONTS[font_name]}"
    else:
        return False, "Failed to save configuration"


def get_font_path():
    """
    Returns the path to the currently selected font file.
    
    Returns:
        Path or None: Path to the font file, or None if using system default
    """
    config = load_config()
    font_name = config.get('font', 'default')
    
    if font_name == 'default':
        return None
    
    font_path = FONTS_DIR / f"{font_name}.ttc"
    if font_path.exists():
        return font_path
    
    # Fallback to default if bundled font not found
    return None


def get_font_name():
    """
    Returns the name of the currently selected font.
    
    Returns:
        str: Font name
    """
    config = load_config()
    return config.get('font', 'default')


def get_available_fonts():
    """
    Returns a list of available font names.
    
    Returns:
        list: List of available font names
    """
    return list(AVAILABLE_FONTS.keys())


def get_font_display_name(font_name):
    """
    Returns the display name for a font.
    
    Args:
        font_name: Font name to get display name for
    
    Returns:
        str: Display name
    """
    return AVAILABLE_FONTS.get(font_name, font_name)


def list_fonts():
    """
    Lists all available fonts with their status.
    
    Returns:
        list: List of tuples (name, display_name, available)
    """
    config = load_config()
    current_font = config.get('font', 'default')
    fonts = []
    
    for name, display_name in AVAILABLE_FONTS.items():
        if name == 'default':
            available = True
        else:
            font_path = FONTS_DIR / f"{name}.ttc"
            available = font_path.exists()
        
        fonts.append((name, display_name, available))
    
    return fonts


def apply_font_to_terminal():
    """
    Attempts to set the terminal font to the selected font.
    This is a best-effort operation and may not work on all systems.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    config = load_config()
    font_name = config.get('font', 'default')
    
    if font_name == 'default':
        return True, "Using system default font"
    
    font_path = get_font_path()
    if not font_path:
        return False, f"Font file not found: {font_name}"
    
    # Note: Terminal font switching is platform-specific and limited
    # This function documents the capability but actual implementation
    # depends on the terminal emulator being used
    if os.name == 'nt':
        return False, "Terminal font switching not supported on Windows. Set font in your terminal settings."
    else:
        return False, "Terminal font switching requires terminal emulator support. Set font manually in your terminal settings."
