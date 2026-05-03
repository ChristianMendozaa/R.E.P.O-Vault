COLORS = {
    "bg": "#111315",
    "surface": "#1A1E21",
    "surface_alt": "#22282D",
    "surface_soft": "#161A1D",
    "border": "#31383F",
    "text": "#E9E2D0",
    "text_muted": "#A8A18F",
    "accent": "#E0A94A",
    "accent_soft": "#5D4720",
    "success": "#6FA66B",
    "success_soft": "#253626",
    "danger": "#A94F43",
    "danger_soft": "#3C221F",
    "info": "#4E6E81",
    "info_soft": "#22343F",
    "focus": "#D7BC7A",
}

FONTS = {
    "display": ("Consolas", 28, "bold"),
    "title": ("Consolas", 20, "bold"),
    "section": ("Consolas", 16, "bold"),
    "body": ("Arial", 12),
    "body_bold": ("Arial", 12, "bold"),
    "small": ("Arial", 10),
    "small_bold": ("Arial", 10, "bold"),
    "metric": ("Consolas", 24, "bold"),
}

SPACE = {
    "xs": 6,
    "sm": 10,
    "md": 16,
    "lg": 24,
    "xl": 32,
}

RADIUS = {
    "sm": 10,
    "md": 16,
    "lg": 22,
    "pill": 999,
}

BUTTON_TONES = {
    "primary": {"fg": COLORS["accent"], "hover": "#F0BC63", "text": "#111315"},
    "secondary": {"fg": COLORS["surface_alt"], "hover": "#2B3137", "text": COLORS["text"]},
    "success": {"fg": COLORS["success"], "hover": "#7DB879", "text": "#111315"},
    "danger": {"fg": COLORS["danger"], "hover": "#B45C4F", "text": COLORS["text"]},
}

STATUS_TONES = {
    "info": {"fg": COLORS["info_soft"], "text": COLORS["text"]},
    "success": {"fg": COLORS["success_soft"], "text": COLORS["text"]},
    "warning": {"fg": COLORS["accent_soft"], "text": COLORS["text"]},
    "danger": {"fg": COLORS["danger_soft"], "text": COLORS["text"]},
}
