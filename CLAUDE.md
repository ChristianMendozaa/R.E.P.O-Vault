# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Run all tests:**
```bash
.\.venv\Scripts\python.exe run_tests.py
```

**Run a single test module:**
```bash
.\.venv\Scripts\python.exe -m unittest tests.test_inventory_logic -v
```

**Run the app:**
```bash
.\.venv\Scripts\python.exe main.py
```

**Build the Windows executable:**
```bash
.\.venv\Scripts\python.exe -m PyInstaller "R.E.P.O Vault.spec" --clean
```

## Architecture

R.E.P.O Vault is a Windows desktop save editor for the game R.E.P.O. It reads/writes encrypted `.es3` save files using AES-CBC + PBKDF2 (via `pycryptodome`). The UI is built with `customtkinter` (a modern Tkinter wrapper).

**Data flow:**
1. `main.py` → `repo_vault.app.launch()` starts the app
2. User opens a `.es3` file → `save_service.load_save_data()` decrypts it via `oxide_cipher` → returns parsed JSON
3. `EditorApp` holds the live JSON in `self.json_data` and renders one of 5 views (Dashboard, Overview, Players, Items, Truck)
4. View modules (`items.py`, `players.py`) call pure mutation functions in `inventory_logic.py`
5. On save → `save_service.save_save_data()` re-encrypts the modified JSON back to `.es3`

**Key modules:**

| Module | Role |
|--------|------|
| `repo_vault/app.py` | `EditorApp` class — UI shell, navigation, state (`json_data`, `players`, `field_entries`) |
| `repo_vault/oxide_cipher.py` | `unwrap_payload()` / `wrap_payload()` — AES-CBC encryption engine |
| `repo_vault/save_service.py` | `load_save_data()` / `save_save_data()` — file I/O with cipher |
| `repo_vault/inventory_logic.py` | Pure functions: `add_item()`, `remove_item()`, `apply_have_everything()` — no UI dependencies |
| `repo_vault/items.py` | Items & Inventory view — item catalog UI, search, quantity controls |
| `repo_vault/players.py` | Players view — crew management, upgrade cards, Steam avatar fetching |
| `repo_vault/theme.py` | Design tokens: colors, fonts, spacing, status tone definitions |
| `repo_vault/widgets.py` | Reusable UI components (panels, buttons, badges, input cards) |
| `repo_vault/constants.py` | App-wide constants: version, window size, default save directory path |
| `repo_vault/env_bootstrap.py` | Loads `.env` into `os.environ` at startup (provides the save file password) |

**Save file JSON shape:**
```json
{
  "teamName": { "value": "..." },
  "playerNames": { "value": { "0": "...", ... } },
  "dictionaryOfDictionaries": {
    "value": {
      "runStats": { "level": ..., "currency": ..., "lives": ..., "save level": ... },
      "itemsPurchased": { "Item Name": quantity },
      "itemStatBattery": { "Item Name/index": battery_value },
      "item": { "Item Name/index": type_id }
    }
  }
}
```

## Key Design Patterns

- **MVC-like**: `EditorApp` owns all state; view modules are functions that build and return packed Tkinter frames.
- **Pure logic layer**: `inventory_logic.py` mutates dicts but has zero UI imports — safe to unit test without a display.
- **Debounced entries**: Entry field changes go through `debounce()` (180 ms) to avoid redundant state updates.
- **Status feedback**: `update_status_badge(tone, message)` drives the header badge — use tones from `theme.py` (`info`, `success`, `warning`, `danger`).
- **Steam avatars**: `players.py` fetches player avatars from the Steam API and caches them locally.

## Environment

The `.env` file (see `.env.example`) must supply `REPO_VAULT_SAVE_PASSWORD`, which is the AES decryption key for `.es3` save files. `env_bootstrap.py` loads this before `constants.py` reads it.

## Tests

- Test runner: standard `unittest` via `run_tests.py` (discovers `tests/`)
- Fixture: `test.es3` — an encrypted example save used by `test_save_service.py`
- Mocks: `tests/helpers.py` provides `FakeEntry` and `FakeLabel` to test UI-adjacent logic without a display
- Tests write temp files under `C:\tmp` (Windows-specific path in test helpers)
