from threading import Thread
from io import BytesIO
from xml.etree import ElementTree

import requests
from PIL import Image
from customtkinter import CTkButton, CTkFrame, CTkImage, CTkLabel, CTkScrollableFrame

from .constants import CACHE_DIR
from .resources import resource_path
from .theme import COLORS, FONTS, SPACE
from .widgets import create_action_button, create_input_card, create_panel, create_text_entry

PLAYER_FIELD_METADATA = [
    ("Health", "health", "playerHealth", None, None, "Current player HP. Recommended max: 200."),
    ("Health Upgrade", "health_upgrade", "playerUpgradeHealth", "+20 HP each", COLORS["success_soft"], None),
    ("Stamina", "stamina_upgrade", "playerUpgradeStamina", "+10 SP each", COLORS["success_soft"], None),
    ("Extra Jump", "extra_jump_upgrade", "playerUpgradeExtraJump", "MAX 1", COLORS["danger_soft"], None),
    ("Launch", "launch_upgrade", "playerUpgradeLaunch", "~10 rec.", COLORS["success_soft"], None),
    ("Map Player Count", "mapplayercount_upgrade", "playerUpgradeMapPlayerCount", "MAX 1", COLORS["danger_soft"], None),
    ("Speed", "speed_upgrade", "playerUpgradeSpeed", "Caution 4+", COLORS["accent_soft"], None),
    ("Strength", "strength_upgrade", "playerUpgradeStrength", "~13 rec.", COLORS["success_soft"], None),
    ("Range", "range_upgrade", "playerUpgradeRange", "~10 rec.", COLORS["success_soft"], None),
    ("Throw", "throw_upgrade", "playerUpgradeThrow", "No hard cap", COLORS["surface_alt"], None),
    ("Crouch Rest", "crouchrest_upgrade", "playerUpgradeCrouchRest", "No hard cap", COLORS["surface_alt"], None),
    ("Tumble Climb", "tumbleclimb_upgrade", "playerUpgradeTumbleClimb", "No hard cap", COLORS["surface_alt"], None),
    ("Tumble Wings", "tumblewings_upgrade", "playerUpgradeTumbleWings", "No hard cap", COLORS["surface_alt"], None),
    ("Death Head Battery", "deathheadbattery_upgrade", "playerUpgradeDeathHeadBattery", "No hard cap", COLORS["surface_alt"], None),
]


def _initials_from_name(name):
    parts = [part for part in name.split() if part]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def _build_initials_avatar(parent, player_name):
    avatar = CTkFrame(parent, width=42, height=42, corner_radius=21, fg_color=COLORS["info"])
    avatar.pack(side="left", anchor="n", padx=(SPACE["lg"], SPACE["md"]), pady=SPACE["lg"])
    avatar.pack_propagate(False)
    CTkLabel(avatar, text=_initials_from_name(player_name), font=FONTS["body_bold"], text_color=COLORS["text"]).pack(expand=True)


def _get_fallback_avatar():
    return Image.open(resource_path("icon.ico"))


def _get_cached_avatar_path(player_id):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{player_id}.png"


def _load_cached_avatar(player_id):
    cached_image_path = _get_cached_avatar_path(player_id)
    if cached_image_path.exists():
        return Image.open(cached_image_path)
    return None


def _fetch_steam_avatar(player_id):
    cached_image_path = _get_cached_avatar_path(player_id)
    cached_image = _load_cached_avatar(player_id)
    if cached_image is not None:
        return cached_image

    response = requests.get(f"https://steamcommunity.com/profiles/{player_id}/?xml=1", timeout=5)
    response.raise_for_status()
    tree = ElementTree.fromstring(response.content)
    avatar_icon = tree.find("avatarIcon")
    if avatar_icon is None or not avatar_icon.text:
        raise ValueError("Steam avatarIcon not found")

    image_response = requests.get(avatar_icon.text, timeout=5)
    image_response.raise_for_status()
    image = Image.open(BytesIO(image_response.content))
    image.save(cached_image_path)
    return image


def _apply_avatar_image(app, image_label, image):
    ctk_image = CTkImage(light_image=image, dark_image=image, size=(42, 42))
    app.player_images.append(ctk_image)
    try:
        image_label.configure(image=ctk_image, text="")
    except Exception:
        return
    image_label.image = ctk_image


def _build_avatar(parent, app, player_id, player_name):
    avatar_shell = CTkFrame(parent, width=42, height=42, corner_radius=21, fg_color=COLORS["surface_alt"])
    avatar_shell.pack(side="left", anchor="n", padx=(SPACE["lg"], SPACE["md"]), pady=SPACE["lg"])
    avatar_shell.pack_propagate(False)

    image_label = CTkLabel(
        avatar_shell,
        text=_initials_from_name(player_name),
        font=FONTS["body_bold"],
        text_color=COLORS["text"],
    )
    image_label.pack(expand=True, fill="both")

    cached_image = _load_cached_avatar(player_id)
    if cached_image is not None:
        _apply_avatar_image(app, image_label, cached_image)
        return

    try:
        image = _get_fallback_avatar()
    except Exception:
        image = None

    if image is not None:
        _apply_avatar_image(app, image_label, image)

    def load_avatar():
        try:
            fetched_image = _fetch_steam_avatar(player_id)
        except Exception:
            return

        def apply_image():
            if image_label.winfo_exists():
                _apply_avatar_image(app, image_label, fetched_image)

        app.root.after(0, apply_image)

    Thread(target=load_avatar, daemon=True).start()


def _count_upgrade_points(upgrades, player_id):
    total = 0
    for _, _, json_key, _, _, _ in PLAYER_FIELD_METADATA[1:]:
        total += int(upgrades.get(json_key, {}).get(player_id, 0))
    return total


def render_players_view(app, parent):
    scroll = CTkScrollableFrame(parent, fg_color="transparent")
    scroll.pack(fill="both", expand=True)
    app.player_entries = {}
    app.player_images = []

    hero = create_panel(scroll, fg_color=COLORS["surface"], border_color=COLORS["success"])
    hero.pack(fill="x", pady=(0, SPACE["lg"]))
    CTkLabel(hero, text="Players", font=FONTS["display"], text_color=COLORS["text"]).pack(anchor="w", padx=SPACE["lg"], pady=(SPACE["lg"], 6))
    CTkLabel(
        hero,
        text="Each player lives in its own operational card. Health on top, upgrades in a structured grid and a clean bulk-edit strip.",
        font=FONTS["body"],
        text_color=COLORS["text_muted"],
        wraplength=780,
        justify="left",
    ).pack(anchor="w", padx=SPACE["lg"], pady=(0, SPACE["lg"]))

    bulk_panel = create_panel(scroll, fg_color=COLORS["surface_alt"], border_color=COLORS["success"])
    bulk_panel.pack(fill="x", pady=(0, SPACE["lg"]))
    CTkLabel(bulk_panel, text="Apply to All Players", font=FONTS["section"], text_color=COLORS["text"]).pack(anchor="w", padx=SPACE["lg"], pady=(SPACE["lg"], 4))
    CTkLabel(
        bulk_panel,
        text="Fill only the fields you want to push to the full crew. Empty fields are ignored.",
        font=FONTS["small"],
        text_color=COLORS["text_muted"],
    ).pack(anchor="w", padx=SPACE["lg"], pady=(0, SPACE["md"]))

    bulk_grid = CTkFrame(bulk_panel, fg_color="transparent")
    bulk_grid.pack(fill="x", padx=SPACE["lg"])
    for col in range(4):
        bulk_grid.grid_columnconfigure(col, weight=1)

    bulk_entries = {}
    for index, (label, suffix, _, _, _, _) in enumerate(PLAYER_FIELD_METADATA):
        row, col = divmod(index, 4)
        field = create_input_card(bulk_grid, label, description="")
        field.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else SPACE["sm"], 0), pady=(0, SPACE["sm"]))
        entry = create_text_entry(field, placeholder="-")
        entry.pack(fill="x", padx=SPACE["md"], pady=(SPACE["md"], SPACE["md"]))
        bulk_entries[suffix] = entry

    upgrades = app.get_root_data()
    app.players = []
    for player_id, player_name in app.json_data["playerNames"]["value"].items():
        player_health = upgrades.get("playerHealth", {}).get(player_id, 100)
        app.players.append({"id": player_id, "name": player_name, "health": player_health})

    def apply_to_all_players():
        changed = False
        for player in app.players:
            player_id = player["id"]
            player_name = player["name"]
            for _, suffix, json_key, _, _, _ in PLAYER_FIELD_METADATA:
                raw_value = bulk_entries[suffix].get().strip()
                if not raw_value:
                    continue
                try:
                    parsed_value = int(raw_value)
                except ValueError:
                    app.set_status("Bulk apply accepts whole numbers only", tone="danger")
                    return

                upgrades.setdefault(json_key, {})[player_id] = parsed_value
                field_key = f"{player_name}_{suffix}"
                entry_widget = app.player_entries.get(field_key)
                if entry_widget is not None:
                    entry_widget.delete(0, "end")
                    entry_widget.insert(0, str(parsed_value))
                    app.mark_entry_state(entry_widget, True)
                changed = True

        if changed:
            app.mark_dirty("Bulk apply executed")
        else:
            app.set_status("There are no values to apply", tone="warning")

    create_action_button(bulk_panel, "Apply to All Players", apply_to_all_players, tone="success", width=190).pack(anchor="w", padx=SPACE["lg"], pady=(SPACE["md"], SPACE["lg"]))

    for player in app.players:
        player_card = create_panel(scroll, fg_color=COLORS["surface"], border_color=COLORS["border"], corner_radius=22)
        player_card.pack(fill="x", pady=(0, SPACE["md"]))

        top = CTkFrame(player_card, fg_color="transparent")
        top.pack(fill="x")
        _build_avatar(top, app, player["id"], player["name"])

        meta = CTkFrame(top, fg_color="transparent")
        meta.pack(side="left", fill="x", expand=True, pady=SPACE["lg"])
        CTkLabel(meta, text=player["name"], font=FONTS["title"], text_color=COLORS["text"]).pack(anchor="w")
        CTkLabel(meta, text=f"Steam ID {player['id']}", font=FONTS["small"], text_color=COLORS["text_muted"]).pack(anchor="w", pady=(2, 8))

        health_value = upgrades.get("playerHealth", {}).get(player["id"], 0)
        upgrade_total = _count_upgrade_points(upgrades, player["id"])
        chips = CTkFrame(meta, fg_color="transparent")
        chips.pack(anchor="w")
        CTkLabel(chips, text=f"HP {health_value}", font=FONTS["small_bold"], text_color=COLORS["text"], fg_color=COLORS["info_soft"], corner_radius=999, padx=10, pady=4).pack(side="left", padx=(0, SPACE["sm"]))
        CTkLabel(chips, text=f"Upgrades {upgrade_total}", font=FONTS["small_bold"], text_color=COLORS["text"], fg_color=COLORS["accent_soft"], corner_radius=999, padx=10, pady=4).pack(side="left")

        fields = CTkFrame(player_card, fg_color="transparent")
        fields.pack(fill="x", padx=SPACE["lg"], pady=(0, SPACE["lg"]))
        for col in range(3):
            fields.grid_columnconfigure(col, weight=1)

        for index, (label, suffix, json_key, cap_text, cap_color, description) in enumerate(PLAYER_FIELD_METADATA):
            field_card = create_input_card(fields, label, description=description or "", cap_text=cap_text, cap_color=cap_color)
            row, col = divmod(index, 3)
            field_card.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else SPACE["sm"], 0), pady=(0, SPACE["sm"]))

            entry = create_text_entry(field_card)
            entry.insert(0, str(upgrades.get(json_key, {}).get(player["id"], 0)))
            entry.pack(fill="x", padx=SPACE["md"], pady=(SPACE["md"], SPACE["md"]))
            app.player_entries[f"{player['name']}_{suffix}"] = entry
            app.bind_numeric_entry(
                entry,
                upgrades.setdefault(json_key, {}),
                player["id"],
                f"{player['name']} / {label} updated",
            )
    return scroll
