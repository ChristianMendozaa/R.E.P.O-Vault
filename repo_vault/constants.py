import os
from pathlib import Path

from .env_bootstrap import load_local_env

load_local_env()

APP_NAME = "R.E.P.O Vault"
VERSION = "1.0.0"
WINDOW_SIZE = "1360x860"
FONT = ("Arial", 12)
SMALL_FONT = ("Arial", 9)
SAVEFILE_DIR = Path.home() / "AppData" / "LocalLow" / "semiwork" / "Repo" / "saves"
CACHE_DIR = Path.home() / ".cache" / "repo_vault"
STATE_OPTIONS = [
    "In-Game / Truck  (save level = 0)",
    "Shop  (save level = 1)",
]

# Keep this value stable: existing .es3 files depend on it for compatibility.
SAVE_PASSWORD = os.getenv("REPO_VAULT_SAVE_PASSWORD", "Why would you want to cheat?... :o It's no fun. :') :'D")
