"""
Icon utilities using QtAwesome with Material Design Icons 6.x (mdi6).
Provides crisp, scalable vector icons that render consistently across all platforms.
"""

import qtawesome as qta
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize

ICONS = {
    # Action icons
    'play': 'mdi6.play',
    'start': 'mdi6.play',
    'stop': 'mdi6.stop',
    'pause': 'mdi6.pause',

    # File operations
    'add': 'mdi6.plus',
    'plus': 'mdi6.plus',
    'remove': 'mdi6.delete-outline',
    'delete': 'mdi6.delete-outline',
    'clear': 'mdi6.delete-outline',
    'folder': 'mdi6.folder-open-outline',
    'browse': 'mdi6.folder-open-outline',
    'open': 'mdi6.folder-open-outline',
    'export': 'mdi6.export-variant',

    # UI icons
    'settings': 'mdi6.cog-outline',
    'info': 'mdi6.information-outline',
    'warning': 'mdi6.alert-outline',
    'error': 'mdi6.close-circle-outline',
    'success': 'mdi6.check-circle-outline',
    'check': 'mdi6.check-circle-outline',

    # Navigation
    'arrow_right': 'mdi6.arrow-right',
    'arrow_left': 'mdi6.arrow-left',
    'arrow_up': 'mdi6.arrow-up',
    'arrow_down': 'mdi6.arrow-down',

    # Web / External
    'web': 'mdi6.web',
    'open_in_new': 'mdi6.open-in-new',
}

from ui.theme import ICON_DEFAULT

DEFAULT_COLOR = ICON_DEFAULT
ICON_SIZE = QSize(20, 20)
BROWSE_ICON_SIZE = QSize(26, 26)


def get_icon(icon_name: str, color: str = DEFAULT_COLOR) -> QIcon:
    """
    Get a QIcon for the given icon name.

    Args:
        icon_name: Name of the icon (e.g., 'play', 'stop', 'folder')
        color: Hex color string for the icon

    Returns:
        QIcon object (empty QIcon if name not found)
    """
    mdi_name = ICONS.get(icon_name.lower(), '')
    if not mdi_name:
        return QIcon()
    return qta.icon(mdi_name, color=color)
