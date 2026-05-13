"""
Design tokens aligned with ytstream247.com (variables.css :root + Tailwind theme).
CSS variable names are noted in comments for traceability.
"""

# --- Brand scale (--brand-900, --brand-800, --brand-700) ---
BRAND_900 = "#0B0F19"
BRAND_800 = "#111827"
BRAND_700 = "#1F2937"
PANEL_HOVER = "#374151"  # --panel-hover

# --- Text (--text, --text-secondary, --muted, --muted-dark) ---
TEXT = "#FFFFFF"
TEXT_SECONDARY = "#CBD5E1"
MUTED = "#94A3B8"
MUTED_DARK = "#64748B"

# --- YT logo tile (React YTLogo md: 40×40, rounded-xl) ---
LOGO_TILE_PX = 40
LOGO_TILE_RADIUS_PX = 12
LOGO_PLAY_PX = 20  # ~w-5 h-5 in Tailwind at md tile

# --- Primary YouTube red (--primary, --primary-light, --primary-dark) ---
PRIMARY = "#FF0000"
PRIMARY_LIGHT = "#FF4B4B"
PRIMARY_DARK = "#B91C1C"
PRIMARY_PRESS_MID = "#991B1B"  # primary-800
PRIMARY_PRESS_END = "#7F1D1D"  # primary-900

# --- Info / indigo for secondary actions (--info and Tailwind info scale) ---
INFO = "#6366F1"
INFO_LIGHT = "#818CF8"
INFO_DARK = "#4F46E5"
INFO_HOVER_FG = "#C7D2FE"  # indigo-200 (Add button hover text)

# --- Status (--success) ---
SUCCESS = "#22C55E"

# --- Error / destructive (--error-soft for icon tints) ---
ERROR_SOFT = "#F87171"
ERROR_HOVER_FG = "#FEE2E2"  # red-100 (Stop/Clear hover text)

# --- Borders (--border-dark, --border, --border-light) ---
BORDER_SUBTLE = "rgba(255, 255, 255, 0.05)"
BORDER_STRONG = "rgba(255, 255, 255, 0.10)"
BORDER_LIGHT = "rgba(255, 255, 255, 0.15)"

# --- Primary alpha (selection, focus, hovers) ---
PRIMARY_08 = "rgba(255, 0, 0, 0.08)"
PRIMARY_10 = "rgba(255, 0, 0, 0.10)"
PRIMARY_12 = "rgba(255, 0, 0, 0.12)"
PRIMARY_15 = "rgba(255, 0, 0, 0.15)"
PRIMARY_22 = "rgba(255, 0, 0, 0.22)"
PRIMARY_25 = "rgba(255, 0, 0, 0.25)"
PRIMARY_30 = "rgba(255, 0, 0, 0.30)"
PRIMARY_35 = "rgba(255, 0, 0, 0.35)"
PRIMARY_40 = "rgba(255, 0, 0, 0.40)"
PRIMARY_45 = "rgba(255, 0, 0, 0.45)"
PRIMARY_50 = "rgba(255, 0, 0, 0.50)"
PRIMARY_55 = "rgba(255, 0, 0, 0.55)"
PRIMARY_60 = "rgba(255, 0, 0, 0.60)"
PRIMARY_70 = "rgba(255, 0, 0, 0.70)"
PRIMARY_75 = "rgba(255, 0, 0, 0.75)"

# --- Surfaces (approx. --color-surface, glass / landing-card) ---
SURFACE_CARD = "rgba(31, 41, 55, 0.94)"  # --panel #1F2937
SURFACE_CARD_TOP = PRIMARY_45  # accent bar like former purple top border
SURFACE_INSET = "rgba(11, 15, 25, 0.92)"  # deep field for inputs/list
SURFACE_DROPZONE = "rgba(31, 41, 55, 0.82)"  # video queue tray vs BRAND_900 window
SURFACE_LIST_ITEM = "rgba(17, 24, 39, 0.95)"  # --sub-card-bg / brand-800
SURFACE_MENU = "rgba(17, 24, 39, 0.97)"
SURFACE_SCROLL = "rgba(11, 15, 25, 0.75)"

# --- Info alpha (Add / Browse buttons) ---
INFO_15 = "rgba(99, 102, 241, 0.15)"
INFO_28 = "rgba(99, 102, 241, 0.28)"
INFO_35 = "rgba(99, 102, 241, 0.35)"
INFO_40 = "rgba(99, 102, 241, 0.40)"
INFO_45 = "rgba(99, 102, 241, 0.45)"
INFO_50 = "rgba(99, 102, 241, 0.50)"
INFO_60 = "rgba(99, 102, 241, 0.60)"
INFO_65 = "rgba(99, 102, 241, 0.65)"
INFO_85 = "rgba(99, 102, 241, 0.85)"

# --- Error button alphas ---
ERR_35 = "rgba(239, 68, 68, 0.35)"
ERR_40 = "rgba(220, 38, 38, 0.40)"
ERR_45 = "rgba(239, 68, 68, 0.45)"
ERR_50 = "rgba(239, 68, 68, 0.50)"
ERR_60 = "rgba(220, 38, 38, 0.60)"
ERR_85 = "rgba(248, 113, 113, 0.85)"

# --- Neutral chrome (gray buttons, scrollbars) ---
NEUTRAL_BTN_BG = "rgba(55, 65, 81, 0.85)"
NEUTRAL_BTN_BORDER = "rgba(75, 85, 99, 0.50)"
NEUTRAL_BTN_HOVER = "rgba(75, 85, 99, 0.90)"
NEUTRAL_BTN_HOVER_B = "rgba(107, 114, 128, 0.75)"
NEUTRAL_PRESSED = "rgba(31, 41, 55, 0.90)"
NEUTRAL_DISABLED_BG = "rgba(31, 41, 55, 0.40)"
NEUTRAL_DISABLED_BR = "rgba(55, 65, 81, 0.20)"
NEUTRAL_DISABLED_FG = "rgba(156, 163, 175, 0.35)"

SCROLL_TRACK = "rgba(17, 24, 39, 0.85)"
SCROLL_HANDLE = "rgba(75, 85, 99, 0.55)"
SCROLL_HANDLE_HOVER = "rgba(107, 114, 128, 0.85)"

# --- Drop zone empty state (muted / zinc-adjacent) ---
DROPZONE_ICON = "#52525B"
DROPZONE_TEXT = MUTED
DROPZONE_SUBTEXT = MUTED_DARK
# Chrome (sync border px with DropListWidget viewport mask math)
DROPZONE_BORDER = "#FF0000"
DROPZONE_BORDER_HOVER = "#FF0000"
DROPZONE_BORDER_PX = 4
DROPZONE_BORDER_HOVER_PX = 4
SURFACE_DROPZONE_HOVER = "rgba(40, 48, 64, 0.95)"  # slightly lifted tray on hover

# --- Radii (--landing-radius-card, blob, pill) ---
RADIUS_CARD = 16
RADIUS_BLOB = RADIUS_CARD
RADIUS_PILL = 20
RADIUS_INPUT = 12
RADIUS_BTN = 12
RADIUS_LIST = 16
RADIUS_ITEM = 14
RADIUS_PROGRESS = 16
RADIUS_CHUNK = 13

# --- Icon default (folder etc.) ---
ICON_DEFAULT = TEXT_SECONDARY
