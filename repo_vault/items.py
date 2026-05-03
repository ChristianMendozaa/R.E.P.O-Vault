from customtkinter import CTkFrame, CTkLabel, CTkScrollableFrame

from .constants import STATE_OPTIONS
from .inventory_logic import add_item, apply_have_everything, build_type_id_map, calculate_item_totals, force_shop_state, remove_item
from .theme import COLORS, FONTS, SPACE
from .widgets import create_action_button, create_input_card, create_panel, create_stat_card, create_text_entry

STATIC_ITEM_IDS = {
    "Item Cart Cannon": 0,
    "Item Cart Laser": 1,
    "Item Cart Medium": 2,
    "Item Cart Small": 3,
    "Item Drone Battery": 4,
    "Item Drone Feather": 5,
    "Item Drone Indestructible": 6,
    "Item Drone Torque": 7,
    "Item Drone Zero Gravity": 8,
    "Item Duck Bucket": 9,
    "Item Extraction Tracker": 10,
    "Item Grenade Duct Taped": 11,
    "Item Grenade Explosive": 12,
    "Item Grenade Human": 13,
    "Item Grenade Shockwave": 14,
    "Item Grenade Stun": 15,
    "Item Gun Handgun": 16,
    "Item Gun Laser": 17,
    "Item Gun Shockwave": 18,
    "Item Gun Shotgun": 19,
    "Item Gun Stun": 20,
    "Item Gun Tranq": 21,
    "Item Health Pack Large": 22,
    "Item Health Pack Medium": 23,
    "Item Health Pack Small": 24,
    "Item Melee Baseball Bat": 25,
    "Item Melee Frying Pan": 26,
    "Item Melee Inflatable Hammer": 27,
    "Item Melee Sledge Hammer": 28,
    "Item Melee Stun Baton": 29,
    "Item Melee Sword": 30,
    "Item Mine Explosive": 31,
    "Item Mine Shockwave": 32,
    "Item Mine Stun": 33,
    "Item Orb Zero Gravity": 34,
    "Item Phase Bridge": 35,
    "Item Power Crystal": 36,
    "Item Rubber Duck": 37,
    "Item Upgrade Death Head Battery": 38,
    "Item Upgrade Map Player Count": 39,
    "Item Upgrade Player Crouch Rest": 40,
    "Item Upgrade Player Energy": 41,
    "Item Upgrade Player Extra Jump": 42,
    "Item Upgrade Player Grab Range": 43,
    "Item Upgrade Player Grab Strength": 44,
    "Item Upgrade Player Health": 45,
    "Item Upgrade Player Sprint Speed": 46,
    "Item Upgrade Player Tumble Climb": 47,
    "Item Upgrade Player Tumble Launch": 48,
    "Item Upgrade Player Tumble Wings": 49,
    "Item Valuable Tracker": 50,
}


def render_items_view(app, parent):
    shell = CTkScrollableFrame(parent, fg_color="transparent")
    shell.pack(fill="both", expand=True)

    root_data = app.get_root_data()
    type_id_map = build_type_id_map(root_data, STATIC_ITEM_IDS)
    purch_dict = root_data.setdefault("itemsPurchased", {})
    sorted_item_names = sorted(type_id_map.keys())

    header = create_panel(shell, fg_color=COLORS["surface"], border_color=COLORS["accent"])
    header.pack(fill="x", pady=(0, SPACE["lg"]))
    CTkLabel(header, text="Items & Inventory", font=FONTS["display"], text_color=COLORS["text"]).pack(anchor="w", padx=SPACE["lg"], pady=(SPACE["lg"], 6))
    CTkLabel(
        header,
        text="Navigable catalog with a summary band, local search and wide controls for adding or removing stock from the truck.",
        font=FONTS["body"],
        text_color=COLORS["text_muted"],
        wraplength=780,
        justify="left",
    ).pack(anchor="w", padx=SPACE["lg"], pady=(0, SPACE["lg"]))

    summary = CTkFrame(shell, fg_color="transparent")
    summary.pack(fill="x", pady=(0, SPACE["lg"]))
    for col in range(3):
        summary.grid_columnconfigure(col, weight=1)

    totals_card = create_stat_card(summary, "Total Qty", "0", hint="Physical items in the truck", accent=COLORS["accent"])
    totals_card.grid(row=0, column=0, sticky="nsew")
    totals_value_label = totals_card.winfo_children()[1]
    unique_card = create_stat_card(summary, "Unique Items", "0", hint="Distinct purchased item types", accent=COLORS["success"])
    unique_card.grid(row=0, column=1, sticky="nsew", padx=(SPACE["md"], 0))
    unique_value_label = unique_card.winfo_children()[1]
    state_card = create_stat_card(summary, "Save State", app.get_save_state_label().split("  ")[0], hint="Forced to shop whenever inventory is added", accent=COLORS["info"])
    state_card.grid(row=0, column=2, sticky="nsew", padx=(SPACE["md"], 0))
    state_value_label = state_card.winfo_children()[1]

    control_band = create_panel(shell, fg_color=COLORS["surface_alt"], border_color=COLORS["border"])
    control_band.pack(fill="x", pady=(0, SPACE["lg"]))
    top_controls = CTkFrame(control_band, fg_color="transparent")
    top_controls.pack(fill="x", padx=SPACE["lg"], pady=SPACE["lg"])

    search_card = create_input_card(top_controls, "Search Items", description="Filter by name to move through the catalog instantly.")
    search_card.pack(side="left", fill="x", expand=True)
    search_entry = create_text_entry(search_card, placeholder="Type an item name")
    search_entry.pack(fill="x", padx=SPACE["md"], pady=(SPACE["md"], SPACE["md"]))

    action_stack = CTkFrame(top_controls, fg_color="transparent")
    action_stack.pack(side="left", padx=(SPACE["lg"], 0))
    create_action_button(action_stack, "Have Everything", lambda: have_everything(), tone="success", width=180).pack(fill="x")
    CTkLabel(
        action_stack,
        text="Set all 0 -> x1",
        font=FONTS["small"],
        text_color=COLORS["text_muted"],
    ).pack(anchor="center", pady=(6, 0))

    catalog = CTkFrame(shell, fg_color="transparent")
    catalog.pack(fill="x")
    for col in range(2):
        catalog.grid_columnconfigure(col, weight=1)
    item_cards = {}

    def add_one(item_name):
        add_item(root_data, type_id_map, item_name)
        app.mark_dirty(f"{item_name} +1")
        refresh_summary()
        refresh_item_card(item_name)

    def remove_one(item_name):
        remove_item(root_data, item_name)
        app.mark_dirty(f"{item_name} -1")
        refresh_summary()
        refresh_item_card(item_name)

    def have_everything():
        added_count = apply_have_everything(root_data, type_id_map)
        app.mark_dirty(f"Have Everything applied to {added_count} items")
        refresh_summary()
        for item_name in item_cards:
            refresh_item_card(item_name)

    def refresh_summary():
        total_qty, unique_qty = calculate_item_totals(root_data)
        totals_value_label.configure(text=str(total_qty))
        unique_value_label.configure(text=str(unique_qty))
        state_value_label.configure(text=app.get_save_state_label().split("  ")[0])

    def refresh_item_card(item_name):
        widgets = item_cards[item_name]
        qty = int(purch_dict.get(item_name, 0))
        widgets["qty_label"].configure(
            text=f"Qty {qty}",
            fg_color=COLORS["accent_soft"] if qty > 0 else COLORS["surface_alt"],
        )

    def apply_filter_layout():
        query = search_entry.get().strip().lower()
        filtered_items = [name for name in sorted_item_names if query in name.lower()]

        for widgets in item_cards.values():
            widgets["card"].grid_forget()

        if not filtered_items:
            empty_state.grid(row=0, column=0, columnspan=2, sticky="ew")
            return
        empty_state.grid_forget()

        for index, item_name in enumerate(filtered_items):
            row, col = divmod(index, 2)
            item_cards[item_name]["card"].grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else SPACE["md"], 0), pady=(0, SPACE["md"]))

    empty_state = create_panel(catalog, fg_color=COLORS["surface"], border_color=COLORS["border"])
    CTkLabel(empty_state, text="No matching items", font=FONTS["section"], text_color=COLORS["text"]).pack(anchor="w", padx=SPACE["lg"], pady=(SPACE["lg"], 4))
    CTkLabel(empty_state, text="Try another search term to browse the catalog.", font=FONTS["small"], text_color=COLORS["text_muted"]).pack(anchor="w", padx=SPACE["lg"], pady=(0, SPACE["lg"]))

    for index, item_name in enumerate(sorted_item_names):
        item_card = create_panel(catalog, fg_color=COLORS["surface"], border_color=COLORS["border"], corner_radius=20)
        row, col = divmod(index, 2)
        item_card.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else SPACE["md"], 0), pady=(0, SPACE["md"]))

        CTkLabel(item_card, text=item_name, font=FONTS["section"], text_color=COLORS["text"], wraplength=300, justify="left").pack(anchor="w", padx=SPACE["lg"], pady=(SPACE["lg"], 8))

        meta = CTkFrame(item_card, fg_color="transparent")
        meta.pack(fill="x", padx=SPACE["lg"])
        qty_label = CTkLabel(meta, text="", font=FONTS["small_bold"], text_color=COLORS["text"], corner_radius=999, padx=10, pady=4)
        qty_label.pack(side="left")
        CTkLabel(meta, text="Truck inventory", font=FONTS["small"], text_color=COLORS["text_muted"]).pack(side="right")

        actions = CTkFrame(item_card, fg_color="transparent")
        actions.pack(fill="x", padx=SPACE["lg"], pady=SPACE["lg"])
        create_action_button(actions, "-1", lambda name=item_name: remove_one(name), tone="danger", width=70).pack(side="left", padx=(0, SPACE["sm"]))
        create_action_button(actions, "+1", lambda name=item_name: add_one(name), tone="primary", width=70).pack(side="left")

        item_cards[item_name] = {"card": item_card, "qty_label": qty_label}
        refresh_item_card(item_name)

    search_entry.bind(
        "<KeyRelease>",
        lambda _event: app.debounce("items::search", 140, apply_filter_layout),
    )
    refresh_summary()
    apply_filter_layout()
    return shell
