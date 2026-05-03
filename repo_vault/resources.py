import os
import sys


def resource_path(relative_path):
    """Get the absolute path to bundled resources."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def set_window_icon(window):
    """Set the window icon when the bundled icon exists."""
    icon_path = resource_path("icon.ico")
    if not os.path.exists(icon_path):
        return

    try:
        window.iconbitmap(icon_path)
    except Exception:
        pass
