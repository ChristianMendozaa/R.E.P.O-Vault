from customtkinter import CTkButton, CTkEntry, CTkFrame, CTkLabel

from .hovercard import bind_hint
from .theme import BUTTON_TONES, COLORS, FONTS, RADIUS, SPACE, STATUS_TONES


def create_panel(parent, fg_color=None, border_color=None, corner_radius=None, border_width=1):
    return CTkFrame(
        parent,
        fg_color=fg_color or COLORS["surface"],
        border_color=border_color or COLORS["border"],
        border_width=border_width,
        corner_radius=corner_radius or RADIUS["md"],
    )


def create_action_button(parent, text, command, tone="primary", width=132):
    colors = BUTTON_TONES[tone]
    return CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        height=40,
        corner_radius=RADIUS["sm"],
        font=FONTS["body_bold"],
        fg_color=colors["fg"],
        hover_color=colors["hover"],
        text_color=colors["text"],
    )


def create_nav_button(parent, text, command):
    return CTkButton(
        parent,
        text=text,
        command=command,
        height=44,
        anchor="w",
        corner_radius=RADIUS["sm"],
        font=FONTS["body_bold"],
        fg_color=COLORS["surface_soft"],
        hover_color=COLORS["surface_alt"],
        text_color=COLORS["text_muted"],
    )


def style_nav_button(button, is_active, is_enabled=True):
    if not is_enabled:
        button.configure(
            state="disabled",
            fg_color=COLORS["surface_soft"],
            hover_color=COLORS["surface_soft"],
            text_color="#6B675E",
        )
        return

    button.configure(state="normal")
    if is_active:
        button.configure(
            fg_color=COLORS["accent_soft"],
            hover_color=COLORS["accent_soft"],
            text_color=COLORS["text"],
        )
    else:
        button.configure(
            fg_color=COLORS["surface_soft"],
            hover_color=COLORS["surface_alt"],
            text_color=COLORS["text_muted"],
        )


def create_status_badge(parent, text, tone="info"):
    colors = STATUS_TONES[tone]
    return CTkLabel(
        parent,
        text=text,
        font=FONTS["small_bold"],
        text_color=colors["text"],
        fg_color=colors["fg"],
        corner_radius=RADIUS["pill"],
        padx=12,
        pady=6,
    )


def update_status_badge(label, text, tone="info"):
    colors = STATUS_TONES[tone]
    label.configure(text=text, text_color=colors["text"], fg_color=colors["fg"])


def create_stat_card(parent, label, value, hint="", accent=None):
    card = create_panel(parent, fg_color=COLORS["surface"], border_color=accent or COLORS["border"])
    CTkLabel(card, text=label, font=FONTS["small_bold"], text_color=COLORS["text_muted"]).pack(anchor="w", padx=SPACE["md"], pady=(SPACE["md"], 2))
    CTkLabel(card, text=value, font=FONTS["metric"], text_color=accent or COLORS["text"]).pack(anchor="w", padx=SPACE["md"])
    if hint:
        CTkLabel(card, text=hint, font=FONTS["small"], text_color=COLORS["text_muted"]).pack(anchor="w", padx=SPACE["md"], pady=(4, SPACE["md"]))
    else:
        CTkLabel(card, text="", font=FONTS["small"], text_color=COLORS["text_muted"]).pack(anchor="w", padx=SPACE["md"], pady=(4, SPACE["md"]))
    return card


def create_section_card(parent, kicker, title, body, button_text, command, tone="primary"):
    card = create_panel(parent, fg_color=COLORS["surface"], border_color=COLORS["border"], corner_radius=RADIUS["lg"])
    CTkLabel(card, text=kicker, font=FONTS["small_bold"], text_color=COLORS["accent"]).pack(anchor="w", padx=SPACE["lg"], pady=(SPACE["lg"], 6))
    CTkLabel(card, text=title, font=FONTS["title"], text_color=COLORS["text"]).pack(anchor="w", padx=SPACE["lg"])
    CTkLabel(
        card,
        text=body,
        font=FONTS["body"],
        text_color=COLORS["text_muted"],
        justify="left",
        wraplength=280,
    ).pack(anchor="w", padx=SPACE["lg"], pady=(8, SPACE["lg"]))
    create_action_button(card, button_text, command, tone=tone, width=170).pack(anchor="w", padx=SPACE["lg"], pady=(0, SPACE["lg"]))
    return card


def create_empty_state(parent, title, body, action_text, action_command):
    shell = CTkFrame(parent, fg_color="transparent")
    shell.pack(expand=True, fill="both")
    CTkLabel(shell, text="R.E.P.O", font=FONTS["display"], text_color=COLORS["accent"]).pack(pady=(100, 4))
    CTkLabel(shell, text=title, font=FONTS["title"], text_color=COLORS["text"]).pack()
    CTkLabel(
        shell,
        text=body,
        font=FONTS["body"],
        text_color=COLORS["text_muted"],
        justify="center",
        wraplength=540,
    ).pack(pady=(12, 26))
    create_action_button(shell, action_text, action_command, tone="primary", width=190).pack()
    return shell


def create_input_card(parent, label, description="", cap_text=None, cap_color=None):
    card = create_panel(parent, fg_color=COLORS["surface"], border_color=COLORS["border"])
    CTkLabel(card, text=label, font=FONTS["body_bold"], text_color=COLORS["text"]).pack(anchor="w", padx=SPACE["md"], pady=(SPACE["md"], 2))
    if description:
        CTkLabel(card, text=description, font=FONTS["small"], text_color=COLORS["text_muted"], justify="left", wraplength=240).pack(anchor="w", padx=SPACE["md"])
    if cap_text:
        CTkLabel(
            card,
            text=cap_text,
            font=FONTS["small_bold"],
            text_color=COLORS["text"],
            fg_color=cap_color or COLORS["surface_alt"],
            corner_radius=RADIUS["pill"],
            padx=8,
            pady=3,
        ).pack(anchor="w", padx=SPACE["md"], pady=(8, 0))
    return card


def create_text_entry(parent, placeholder=""):
    return CTkEntry(
        parent,
        height=40,
        corner_radius=RADIUS["sm"],
        font=FONTS["body"],
        fg_color=COLORS["surface_alt"],
        border_color=COLORS["border"],
        text_color=COLORS["text"],
        placeholder_text=placeholder,
        placeholder_text_color=COLORS["text_muted"],
    )


def mark_entry_valid(entry):
    entry.configure(border_color=COLORS["border"])


def mark_entry_invalid(entry):
    entry.configure(border_color=COLORS["danger"])


def attach_tooltip(widget, tooltip):
    bind_hint(widget, tooltip)
