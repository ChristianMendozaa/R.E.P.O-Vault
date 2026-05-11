from pathlib import Path

from customtkinter import CTk, CTkFrame, CTkLabel, CTkOptionMenu, CTkProgressBar, CTkScrollableFrame, set_appearance_mode, set_default_color_theme
from tkinter import filedialog, messagebox

from .constants import APP_NAME, SAVEFILE_DIR, STATE_OPTIONS, VERSION, WINDOW_SIZE
from .inventory_logic import add_item, build_type_id_map, remove_item
from .items import STATIC_ITEM_IDS, render_items_view
from .players import PLAYER_FIELD_METADATA, render_players_view
from .resources import set_window_icon
from .save_service import load_save_data, save_save_data
from .theme import COLORS, FONTS, SPACE
from .widgets import (
    create_action_button,
    create_empty_state,
    create_input_card,
    create_nav_button,
    create_panel,
    create_section_card,
    create_stat_card,
    create_status_badge,
    create_text_entry,
    mark_entry_invalid,
    mark_entry_valid,
    style_nav_button,
    update_status_badge,
)


class EditorApp:
    def __init__(self):
        self.root = CTk()
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(1220, 760)
        self.root.title(APP_NAME)
        self.root.configure(fg_color=COLORS["bg"])
        set_window_icon(self.root)
        set_appearance_mode("dark")
        set_default_color_theme("dark-blue")

        self.json_data = {}
        self.savefilename = ""
        self.current_file_path = None
        self.has_unsaved_changes = False
        self.current_view = "dashboard"
        self.players = []
        self.player_entries = {}
        self.player_images = []
        self.nav_buttons = {}
        self.field_entries = {}
        self.entry_game_state = None
        self.current_content = None
        self.current_content_name = None
        self.debounce_jobs = {}

        self.header_file_label = None
        self.status_badge = None
        self.sidebar = None
        self.content_frame = None

        self._build_shell()
        self._set_nav_enabled(False)
        self.render_current_view()

    def _build_shell(self):
        header = CTkFrame(self.root, fg_color=COLORS["bg"])
        header.pack(fill="x", padx=SPACE["xl"], pady=(SPACE["lg"], SPACE["sm"]))

        brand = CTkFrame(header, fg_color="transparent")
        brand.pack(side="left")
        CTkLabel(brand, text="R.E.P.O", font=FONTS["small_bold"], text_color=COLORS["accent"]).pack(anchor="w")
        CTkLabel(brand, text="Vault", font=FONTS["display"], text_color=COLORS["text"]).pack(anchor="w")
        CTkLabel(brand, text=f"Build {VERSION}", font=FONTS["small"], text_color=COLORS["text_muted"]).pack(anchor="w", pady=(0, 2))

        header_meta = CTkFrame(header, fg_color="transparent")
        header_meta.pack(side="left", padx=SPACE["xl"])
        CTkLabel(header_meta, text="Active save", font=FONTS["small_bold"], text_color=COLORS["text_muted"]).pack(anchor="w")
        self.header_file_label = CTkLabel(header_meta, text="No save loaded", font=FONTS["body_bold"], text_color=COLORS["text"])
        self.header_file_label.pack(anchor="w", pady=(2, 0))
        self.status_badge = create_status_badge(header_meta, "Idle", tone="info")
        self.status_badge.pack(anchor="w", pady=(10, 0))

        actions = CTkFrame(header, fg_color="transparent")
        actions.pack(side="right")
        self.open_button = create_action_button(actions, "Open Save", self.open_file, tone="success", width=132)
        self.open_button.pack(side="left", padx=(0, SPACE["sm"]))
        self.save_button = create_action_button(actions, "Save", self.save_data, tone="primary", width=132)
        self.save_button.pack(side="left")

        divider = CTkFrame(self.root, fg_color=COLORS["border"], height=1)
        divider.pack(fill="x", padx=SPACE["xl"], pady=(0, SPACE["md"]))

        body = CTkFrame(self.root, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=SPACE["xl"], pady=(0, SPACE["xl"]))

        self.sidebar = create_panel(body, fg_color=COLORS["surface_soft"], border_color=COLORS["border"])
        self.sidebar.pack(side="left", fill="y", padx=(0, SPACE["lg"]))
        self.sidebar.configure(width=240)
        self.sidebar.pack_propagate(False)

        CTkLabel(self.sidebar, text="Workspace", font=FONTS["section"], text_color=COLORS["text"]).pack(anchor="w", padx=SPACE["md"], pady=(SPACE["lg"], 4))
        CTkLabel(
            self.sidebar,
            text="Move through focused screens. Each view edits one part of the save without noise.",
            font=FONTS["small"],
            text_color=COLORS["text_muted"],
            wraplength=180,
            justify="left",
        ).pack(anchor="w", padx=SPACE["md"], pady=(0, SPACE["lg"]))

        nav_definitions = [
            ("dashboard", "Dashboard Home"),
            ("overview", "Run Overview"),
            ("players", "Players"),
            ("items", "Items & Inventory"),
            ("truck", "Power / Truck"),
        ]

        for view_name, label in nav_definitions:
            button = create_nav_button(self.sidebar, label, lambda name=view_name: self.navigate(name))
            button.pack(fill="x", padx=SPACE["md"], pady=(0, SPACE["sm"]))
            self.nav_buttons[view_name] = button

        self.sidebar_hint = CTkLabel(
            self.sidebar,
            text="Open a save to unlock the workspace.",
            font=FONTS["small"],
            text_color=COLORS["text_muted"],
            wraplength=180,
            justify="left",
        )
        self.sidebar_hint.pack(side="bottom", anchor="w", padx=SPACE["md"], pady=SPACE["lg"])

        self.content_frame = CTkFrame(body, fg_color="transparent")
        self.content_frame.pack(side="left", fill="both", expand=True)

    def _reset_view_refs(self):
        self.field_entries = {}
        self.player_entries = {}
        self.player_images = []
        self.entry_game_state = None

    def _destroy_cached_views(self):
        return

    def _clear_active_content(self):
        for child in self.content_frame.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass

        self.current_content = None
        self.current_content_name = None
        self._reset_view_refs()

    def _set_nav_enabled(self, enabled):
        for view_name, button in self.nav_buttons.items():
            style_nav_button(button, self.current_view == view_name, is_enabled=enabled)
        self.sidebar_hint.configure(
            text="Use the dashboard to enter each system." if enabled else "Open a save to unlock the workspace."
        )

    def _update_nav_state(self):
        enabled = bool(self.json_data)
        for view_name, button in self.nav_buttons.items():
            style_nav_button(button, self.current_view == view_name, is_enabled=enabled)

    def _update_header_file_info(self):
        if not self.current_file_path:
            self.header_file_label.configure(text="No save loaded")
            return

        suffix = " *" if self.has_unsaved_changes else ""
        self.header_file_label.configure(text=f"{self.savefilename}{suffix}")

    def set_status(self, text, tone="info"):
        update_status_badge(self.status_badge, text, tone=tone)

    def mark_dirty(self, message="Changes pending"):
        self.has_unsaved_changes = True
        self._update_header_file_info()
        self.set_status(message, tone="warning")

    def mark_saved(self, message="Save stored"):
        self.has_unsaved_changes = False
        self._update_header_file_info()
        self.set_status(message, tone="success")

    def make_plain_entry(self, parent, width=120, placeholder="", border_color=None, fg_color=None):
        entry = create_text_entry(parent, placeholder=placeholder)
        entry.configure(width=width, border_color=border_color or COLORS["border"], fg_color=fg_color or COLORS["surface_alt"])
        return entry

    def debounce(self, job_key, delay_ms, callback):
        previous_job = self.debounce_jobs.pop(job_key, None)
        if previous_job is not None:
            try:
                self.root.after_cancel(previous_job)
            except Exception:
                pass

        self.debounce_jobs[job_key] = self.root.after(
            delay_ms,
            lambda: self._run_debounced(job_key, callback),
        )

    def _run_debounced(self, job_key, callback):
        self.debounce_jobs.pop(job_key, None)
        callback()

    def mark_entry_state(self, entry, is_valid):
        if is_valid:
            mark_entry_valid(entry)
        else:
            mark_entry_invalid(entry)

    def get_root_data(self):
        return self.json_data["dictionaryOfDictionaries"]["value"]

    def get_run_stats(self):
        return self.get_root_data()["runStats"]

    def get_team_name(self):
        return self.json_data["teamName"]["value"]

    def get_save_state_label(self):
        save_level = self.get_run_stats().get("save level", 0)
        if save_level in (0, 1):
            return STATE_OPTIONS[save_level]
        return STATE_OPTIONS[0]

    def get_player_count(self):
        return len(self.json_data.get("playerNames", {}).get("value", {}))

    def get_item_totals(self):
        purchased = self.get_root_data().get("itemsPurchased", {})
        total_qty = sum(int(value) for value in purchased.values())
        unique_qty = sum(1 for value in purchased.values() if int(value) > 0)
        return total_qty, unique_qty

    def set_numeric_value(self, entry, target_dict, key, message):
        raw_value = entry.get().strip()
        if raw_value == "":
            self.mark_entry_state(entry, False)
            self.set_status("Required numeric fields cannot be empty", tone="warning")
            return
        try:
            parsed_value = int(raw_value)
        except ValueError:
            self.mark_entry_state(entry, False)
            self.set_status("Only whole numbers are allowed here", tone="danger")
            return

        target_dict[key] = parsed_value
        self.mark_entry_state(entry, True)
        self.mark_dirty(message)

    def set_text_value(self, entry, target_dict, key, message):
        value = entry.get().strip()
        if value == "":
            self.mark_entry_state(entry, False)
            self.set_status("This field cannot be empty", tone="warning")
            return

        target_dict[key] = value
        self.mark_entry_state(entry, True)
        self.mark_dirty(message)

    def bind_numeric_entry(self, entry, target_dict, key, message):
        entry.bind(
            "<KeyRelease>",
            lambda _event: self.debounce(
                f"numeric::{id(entry)}",
                180,
                lambda: self.set_numeric_value(entry, target_dict, key, message),
            ),
        )

    def bind_text_entry(self, entry, target_dict, key, message):
        entry.bind(
            "<KeyRelease>",
            lambda _event: self.debounce(
                f"text::{id(entry)}",
                180,
                lambda: self.set_text_value(entry, target_dict, key, message),
            ),
        )

    def navigate(self, view_name):
        if not self.json_data:
            self.render_current_view()
            return
        self.current_view = view_name
        self._update_nav_state()
        self.render_current_view()

    def render_current_view(self):
        self._clear_active_content()
        self._update_nav_state()

        if not self.json_data:
            self.current_content = create_empty_state(
                self.content_frame,
                "Retro save control room",
                "Load a .es3 save to enter the dashboard, edit players, review inventory and tune truck power through a cleaner, faster interface.",
                "Open Save File",
                self.open_file,
            )
            self.current_content_name = "empty"
            return

        if self.current_view == "dashboard":
            self.current_content = self.render_dashboard()
        elif self.current_view == "overview":
            self.current_content = self.render_overview()
        elif self.current_view == "players":
            self.current_content = render_players_view(self, self.content_frame)
        elif self.current_view == "items":
            self.current_content = render_items_view(self, self.content_frame)
        elif self.current_view == "truck":
            self.current_content = self.render_truck_view()
        else:
            self.current_view = "dashboard"
            self.current_content = self.render_dashboard()

        self.current_content_name = self.current_view

    def open_file(self):
        file_path = filedialog.askopenfilename(
            initialdir=SAVEFILE_DIR,
            filetypes=[("Game Save (.es3 file)", "*.es3")],
        )
        if not file_path:
            return

        try:
            self.json_data = load_save_data(file_path)
        except Exception as exc:
            messagebox.showerror("Open failed", f"Failed to open file:\n{exc}")
            return

        self.current_file_path = file_path
        self.savefilename = Path(file_path).name
        self.has_unsaved_changes = False
        self.current_view = "dashboard"
        self._destroy_cached_views()
        self._clear_active_content()
        self._set_nav_enabled(True)
        self._update_header_file_info()
        self.set_status("Save loaded", tone="success")
        self.render_current_view()

    def save_data(self):
        if not self.json_data:
            messagebox.showerror("No data", "There is no loaded save to write.")
            return

        file_path = filedialog.asksaveasfilename(
            initialdir=SAVEFILE_DIR,
            initialfile=self.savefilename or "repo_save.es3",
            defaultextension=".es3",
            filetypes=[("Game Save (.es3 file)", "*.es3")],
        )
        if not file_path:
            return

        try:
            save_save_data(file_path, self.json_data)
        except Exception as exc:
            messagebox.showerror("Save failed", f"Failed to save file:\n{exc}")
            return

        self.current_file_path = file_path
        self.savefilename = Path(file_path).name
        self.mark_saved("Save stored")

    def render_dashboard(self):
        scroll = CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        hero = create_panel(scroll, fg_color=COLORS["surface"], border_color=COLORS["accent"], corner_radius=24)
        hero.pack(fill="x", pady=(0, SPACE["lg"]))
        CTkLabel(hero, text="Dashboard Home", font=FONTS["display"], text_color=COLORS["text"]).pack(anchor="w", padx=SPACE["xl"], pady=(SPACE["xl"], 8))
        CTkLabel(
            hero,
            text="Control the save like an operations console: run overview, players, inventory and truck power split into clean focused screens.",
            font=FONTS["body"],
            text_color=COLORS["text_muted"],
            justify="left",
            wraplength=760,
        ).pack(anchor="w", padx=SPACE["xl"])

        hero_actions = CTkFrame(hero, fg_color="transparent")
        hero_actions.pack(anchor="w", padx=SPACE["xl"], pady=(SPACE["lg"], SPACE["xl"]))
        create_action_button(hero_actions, "Run Overview", lambda: self.navigate("overview"), tone="primary", width=150).pack(side="left", padx=(0, SPACE["sm"]))
        create_action_button(hero_actions, "Players", lambda: self.navigate("players"), tone="secondary", width=120).pack(side="left", padx=(0, SPACE["sm"]))
        create_action_button(hero_actions, "Items", lambda: self.navigate("items"), tone="secondary", width=120).pack(side="left")

        metrics = CTkFrame(scroll, fg_color="transparent")
        metrics.pack(fill="x", pady=(0, SPACE["lg"]))
        cards = [
            ("Level", str(self.get_run_stats().get("level", 0)), "Current progress", COLORS["accent"]),
            ("Currency", str(self.get_run_stats().get("currency", 0)), "Run economy", COLORS["success"]),
            ("Players", str(self.get_player_count()), "Registered crew", COLORS["text"]),
            ("Save State", self.get_save_state_label().split("  ")[0], "Spawn on load", COLORS["accent"]),
        ]
        for col in range(2):
            metrics.grid_columnconfigure(col, weight=1)
        for index, (label, value, hint, accent) in enumerate(cards):
            card = create_stat_card(metrics, label, value, hint=hint, accent=accent)
            row, col = divmod(index, 2)
            card.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else SPACE["md"], 0), pady=(0, SPACE["md"]))

        section_grid = CTkFrame(scroll, fg_color="transparent")
        section_grid.pack(fill="x")
        for col in range(2):
            section_grid.grid_columnconfigure(col, weight=1)

        sections = [
            ("RUN", "Run Overview", "Edit progress, economy, team name and spawn state with a more breathable layout.", "Open Overview", lambda: self.navigate("overview"), "primary"),
            ("CREW", "Players", "Manage health and upgrades per player inside modular cards with avatars and quick summaries.", "Open Players", lambda: self.navigate("players"), "secondary"),
            ("LOADOUT", "Items & Inventory", "Find items instantly, adjust quantities and apply Have Everything without dense lists.", "Open Items", lambda: self.navigate("items"), "secondary"),
            ("POWER", "Power / Truck", "Concentrate charging station, truck energy, power crystals and save state in one focused view.", "Open Power", lambda: self.navigate("truck"), "secondary"),
        ]
        for index, (kicker, title, body, button_text, command, tone) in enumerate(sections):
            card = create_section_card(section_grid, kicker, title, body, button_text, command, tone=tone)
            row, col = divmod(index, 2)
            card.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else SPACE["md"], 0), pady=(0, SPACE["md"]))
        return scroll

    def build_field_card(self, parent, label, description, initial_value, cap_text=None, cap_color=None):
        card = create_input_card(parent, label, description=description, cap_text=cap_text, cap_color=cap_color)
        entry = create_text_entry(card)
        entry.insert(0, str(initial_value))
        entry.pack(fill="x", padx=SPACE["md"], pady=(SPACE["md"], SPACE["md"]))
        return card, entry

    def render_overview(self):
        scroll = CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        header = create_panel(scroll, fg_color=COLORS["surface"])
        header.pack(fill="x", pady=(0, SPACE["lg"]))
        CTkLabel(header, text="Run Overview", font=FONTS["display"], text_color=COLORS["text"]).pack(anchor="w", padx=SPACE["lg"], pady=(SPACE["lg"], 6))
        CTkLabel(
            header,
            text="Progress, economy and team identity grouped into wide panels. Every change writes directly into the active save state.",
            font=FONTS["body"],
            text_color=COLORS["text_muted"],
            justify="left",
            wraplength=780,
        ).pack(anchor="w", padx=SPACE["lg"], pady=(0, SPACE["lg"]))

        grid = CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x")
        for col in range(2):
            grid.grid_columnconfigure(col, weight=1)

        run_stats = self.get_run_stats()

        field_specs = [
            ("Level", "Current run level.", run_stats.get("level", 0), "level", "Level updated"),
            ("Currency", "Available money for purchases and upgrades.", run_stats.get("currency", 0), "currency", "Currency updated"),
        ]

        for index, (label, description, initial, target_key, target_message) in enumerate(field_specs):
            card, entry = self.build_field_card(grid, label, description, initial)
            self.bind_numeric_entry(entry, run_stats, target_key, target_message)
            row, col = divmod(index, 2)
            card.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else SPACE["md"], 0), pady=(0, SPACE["md"]))
            self.field_entries[label] = entry

        state_card = create_panel(grid, fg_color=COLORS["surface"], border_color=COLORS["border"])
        CTkLabel(state_card, text="Save State", font=FONTS["body_bold"], text_color=COLORS["text"]).pack(anchor="w", padx=SPACE["md"], pady=(SPACE["md"], 2))
        CTkLabel(
            state_card,
            text="Choose whether the save spawns in-game or in the shop when loaded.",
            font=FONTS["small"],
            text_color=COLORS["text_muted"],
            wraplength=240,
        ).pack(anchor="w", padx=SPACE["md"])
        self.entry_game_state = CTkOptionMenu(
            state_card,
            values=STATE_OPTIONS,
            font=FONTS["body"],
            width=250,
            fg_color=COLORS["surface_alt"],
            button_color=COLORS["accent_soft"],
            button_hover_color=COLORS["accent"],
            text_color=COLORS["text"],
            command=self.on_state_change,
        )
        self.entry_game_state.set(self.get_save_state_label())
        self.entry_game_state.pack(anchor="w", padx=SPACE["md"], pady=(SPACE["md"], SPACE["md"]))
        row, col = divmod(len(field_specs), 2)
        state_card.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else SPACE["md"], 0), pady=(0, SPACE["md"]))
        return scroll

    def on_state_change(self, selected_value):
        run_stats = self.get_run_stats()
        run_stats["save level"] = 1 if selected_value == STATE_OPTIONS[1] else 0
        self.mark_dirty("Save state updated")

    def render_truck_view(self):
        scroll = CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        header = create_panel(scroll, fg_color=COLORS["surface"], border_color=COLORS["info"])
        header.pack(fill="x", pady=(0, SPACE["lg"]))
        CTkLabel(header, text="Power / Truck", font=FONTS["display"], text_color=COLORS["text"]).pack(anchor="w", padx=SPACE["lg"], pady=(SPACE["lg"], 6))
        CTkLabel(
            header,
            text="Manage power crystals loaded in the truck and the save spawn target.",
            font=FONTS["body"],
            text_color=COLORS["text_muted"],
            wraplength=780,
            justify="left",
        ).pack(anchor="w", padx=SPACE["lg"], pady=(0, SPACE["lg"]))

        root_data = self.get_root_data()
        type_id_map = build_type_id_map(root_data, STATIC_ITEM_IDS)

        _CRYSTAL_MAX = 10

        crystal_panel = create_panel(scroll, fg_color=COLORS["surface"], border_color=COLORS["border"])
        crystal_panel.pack(fill="x", pady=(0, SPACE["lg"]))

        CTkLabel(crystal_panel, text="Power Crystals", font=FONTS["section"], text_color=COLORS["text"]).pack(anchor="w", padx=SPACE["lg"], pady=(SPACE["lg"], 4))
        CTkLabel(
            crystal_panel,
            text="Crystals currently loaded in the truck. Maximum is 6.",
            font=FONTS["small"],
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=SPACE["lg"])

        bar_row = CTkFrame(crystal_panel, fg_color="transparent")
        bar_row.pack(anchor="w", fill="x", padx=SPACE["lg"], pady=(SPACE["md"], 0))

        current_crystals = int(root_data.get("itemsPurchased", {}).get("Item Power Crystal", 0))
        progress_val = min(current_crystals / _CRYSTAL_MAX, 1.0)

        bar = CTkProgressBar(bar_row, height=14, corner_radius=6, fg_color=COLORS["surface_alt"], progress_color=COLORS["success"])
        bar.set(progress_val)
        bar.pack(side="left", fill="x", expand=True, padx=(0, SPACE["md"]))
        CTkLabel(bar_row, text=f"{current_crystals} / {_CRYSTAL_MAX}", font=FONTS["body_bold"], text_color=COLORS["text"]).pack(side="left")

        btn_row = CTkFrame(crystal_panel, fg_color="transparent")
        btn_row.pack(anchor="w", padx=SPACE["lg"], pady=(SPACE["sm"], SPACE["lg"]))

        def _remove_crystal():
            remove_item(root_data, "Item Power Crystal")
            self.mark_dirty("Power crystal removed")
            self.navigate("truck")

        def _add_crystal():
            if int(root_data.get("itemsPurchased", {}).get("Item Power Crystal", 0)) >= _CRYSTAL_MAX:
                self.set_status(f"Maximum {_CRYSTAL_MAX} crystals reached", tone="warning")
                return
            add_item(root_data, type_id_map, "Item Power Crystal")
            self.mark_dirty("Power crystal added")
            self.navigate("truck")

        create_action_button(btn_row, "− 1", _remove_crystal, tone="danger", width=80).pack(side="left", padx=(0, SPACE["sm"]))
        create_action_button(btn_row, "+ 1", _add_crystal, tone="success", width=80).pack(side="left")

        state_card = create_panel(scroll, fg_color=COLORS["surface"])
        state_card.pack(fill="x")
        CTkLabel(state_card, text="Spawn State", font=FONTS["section"], text_color=COLORS["text"]).pack(anchor="w", padx=SPACE["lg"], pady=(SPACE["lg"], 4))
        CTkLabel(
            state_card,
            text="Adjust whether the save loads in the truck or in the shop. This mirrors the control shown in Run Overview.",
            font=FONTS["small"],
            text_color=COLORS["text_muted"],
            wraplength=760,
            justify="left",
        ).pack(anchor="w", padx=SPACE["lg"])
        self.entry_game_state = CTkOptionMenu(
            state_card,
            values=STATE_OPTIONS,
            font=FONTS["body"],
            width=280,
            fg_color=COLORS["surface_alt"],
            button_color=COLORS["accent_soft"],
            button_hover_color=COLORS["accent"],
            text_color=COLORS["text"],
            command=self.on_state_change,
        )
        self.entry_game_state.set(self.get_save_state_label())
        self.entry_game_state.pack(anchor="w", padx=SPACE["lg"], pady=(SPACE["md"], SPACE["lg"]))
        return scroll

    def run(self):
        self.root.mainloop()


def launch():
    EditorApp().run()
