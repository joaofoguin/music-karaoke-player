from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

SVG_ICONS = {
    "play": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
        <path fill="{color}" d="M8 5.14v13.72a1 1 0 0 0 1.5.86l11-6.86a1 1 0 0 0 0-1.72l-11-6.86A1 1 0 0 0 8 5.14z"/>
    </svg>""",

    "pause": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
        <path fill="{color}" d="M6 5h3.5a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zm8.5 0H18a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1h-3.5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z"/>
    </svg>""",

    "previous": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
        <path fill="{color}" d="M6 6a1 1 0 0 1 1 1v10a1 1 0 0 1-2 0V7a1 1 0 0 1 1-1zm12.5 0.28a1 1 0 0 0-1.5-.86l-8 5.14a1 1 0 0 0 0 1.72l8 5.14a1 1 0 0 0 1.5-.86V6.28z"/>
    </svg>""",

    "next": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
        <path fill="{color}" d="M18 6a1 1 0 0 1 1 1v10a1 1 0 0 1-2 0V7a1 1 0 0 1 1-1zM5.5 6.28a1 1 0 0 1 1.5-.86l8 5.14a1 1 0 0 1 0 1.72l-8 5.14a1 1 0 0 1-1.5-.86V6.28z"/>
    </svg>""",

    "repeat": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
        <path fill="{color}" d="M7 7h10v3l4-4-4-4v3H5a2 2 0 0 0-2 2v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12a2 2 0 0 0 2-2v-6h-2v4z"/>
    </svg>""",

    "microphone": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
        <path fill="{color}" d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/>
    </svg>""",

    "karaoke": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
        <path fill="{color}" d="M9 2.5A3.5 3.5 0 0 0 5.5 6v5A3.5 3.5 0 0 0 9 14.5a3.5 3.5 0 0 0 3.5-3.5V6A3.5 3.5 0 0 0 9 2.5zm1.5 3.5v5a1.5 1.5 0 0 1-3 0V6a1.5 1.5 0 0 1 3 0zM14 10.5V7h2v3.5h-2zm0 0c0 3.04-2.24 5.58-5.16 6.04V20h2v-3.46A7.5 7.5 0 0 0 16 10.5h-2zM16.5 5.5v2h2v2h-2v2h-2v-2h2v-2h-2v-2h2z"/>
        <path fill="{color}" d="M18 13h2v2h-2zm-2 2h2v2h-2z"/>
    </svg>""",

    "volume_high": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
        <path fill="{color}" d="M3 9v6h4l5 5V4L7 9H3zm13.5 3a4.5 4.5 0 0 0-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
    </svg>""",

    "volume_low": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
        <path fill="{color}" d="M3 9v6h4l5 5V4L7 9H3zm13.5 3a4.5 4.5 0 0 0-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/>
    </svg>""",

    "volume_mute": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
        <path fill="{color}" d="M3.27 2L2 3.27l4.99 4.99L7 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L3.27 2zM12 4L9.91 6.09 12 8.18V4zm4.5 8c0-.7-.18-1.36-.5-1.94l1.52-1.52c.62 1.02.98 2.21.98 3.46 0 2.45-1.29 4.61-3.23 5.82l-1.46-1.46c1.06-.85 1.69-2.21 1.69-3.86z"/>
    </svg>""",

    "folder": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
        <path fill="{color}" d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/>
    </svg>""",

    "edit": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zm14.71-9.04a1 1 0 0 0 0-1.41l-2.5-2.5a1 1 0 0 0-1.41 0l-1.17 1.17 3.75 3.75 1.33-1.01z"/></svg>""",

    "font_decrease": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M5 11h14v2H5zM7 20h2l1.2-4h3.6l1.2 4h2L13 4h-2L7 20zm3.7-6 1.3-5 1.3 5h-2.6z"/></svg>""",

    "font_increase": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M5 11h14v2H5zM11 5h2v14h-2zM7 20h2l1.2-4h3.6l1.2 4h2L13 4h-2L7 20zm3.7-6 1.3-5 1.3 5h-2.6z"/></svg>""",

    "fullscreen": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M4 4h6v2H6v4H4V4zm10 0h6v6h-2V6h-4V4zM4 14h2v4h4v2H4v-6zm14 0h2v6h-6v-2h4v-4z"/></svg>""",

    "fullscreen_exit": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M8 4h2v4h4v2H8V4zm6 16v-4h-4v-2h6v6h-2zM4 8h4v2H4V8zm12 6h4v2h-4v-2z"/></svg>""",


    "rewind_5": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M11 5V2L6 6l5 4V7c3.31 0 6 2.69 6 6a6 6 0 0 1-11.2 3H3.7A8 8 0 1 0 11 5z"/></svg>""",
    "forward_5": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M13 5V2l5 4-5 4V7c-3.31 0-6 2.69-6 6a6 6 0 0 0 11.2 3h2.1A8 8 0 1 1 13 5z"/></svg>""",
    "timer": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M15 1H9v2h6V1zm-1 12h-4V8h2v3h2v2zm6.03-5.39 1.42-1.42a9.94 9.94 0 0 0-1.42-1.42l-1.42 1.42A9.96 9.96 0 1 0 19 17.03l1.42 1.42c.5-.42.99-.89 1.42-1.42l-1.42-1.42A9.96 9.96 0 0 0 20.03 7.61zM12 20a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"/></svg>""",
    "paste": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M19 2h-4.18C14.4.84 13.3 0 12 0s-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm7 18H5V4h2v3h10V4h2v16z"/></svg>""",
    "plus": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M19 11h-6V5h-2v6H5v2h6v6h2v-6h6v-2z"/></svg>""",
    "minus": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M5 11h14v2H5z"/></svg>""",
    "arrow_up": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 4l-7 7 1.4 1.4L11 7.8V20h2V7.8l4.6 4.6L19 11l-7-7z"/></svg>""",
    "arrow_down": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M12 20l7-7-1.4-1.4L13 16.2V4h-2v12.2l-4.6-4.6L5 13l7 7z"/></svg>""",
    "settings": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M19.43 12.98c.04-.32.07-.65.07-.98s-.02-.66-.07-.98l2.11-1.65-2-3.46-2.49 1a7.45 7.45 0 0 0-1.69-.98L15 2h-4l-.38 2.93c-.6.24-1.17.57-1.69.98l-2.49-1-2 3.46 2.11 1.65c-.04.32-.08.65-.08.98s.03.66.08.98l-2.11 1.65 2 3.46 2.49-1c.52.41 1.09.74 1.69.98L11 22h4l.38-2.93c.6-.24 1.17-.57 1.69-.98l2.49 1 2-3.46-2.13-1.65zM13 16.5A4.5 4.5 0 1 1 13 7a4.5 4.5 0 0 1 0 9.5z"/></svg>""",
    "save": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M17 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V7l-4-4zm-5 16a3 3 0 1 1 0-6 3 3 0 0 1 0 6zM6 5h8v4H6V5z"/></svg>""",

    "trash": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM8 9h8v10H8V9zm7.5-5-1-1h-5l-1 1H5v2h14V4z"/></svg>""",
    "view_details": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M3 5h18v3H3V5zm0 5h18v3H3v-3zm0 5h18v3H3v-3z"/></svg>""",
    "view_list": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M4 5h2v2H4V5zm4 0h12v2H8V5zM4 11h2v2H4v-2zm4 0h12v2H8v-2zM4 17h2v2H4v-2zm4 0h12v2H8v-2z"/></svg>""",
    "view_grid": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M4 4h6v6H4V4zm10 0h6v6h-6V4zM4 14h6v6H4v-6zm10 0h6v6h-6v-6z"/></svg>""",
    "view_large": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{color}" d="M3 3h8v8H3V3zm10 0h8v8h-8V3zM3 13h8v8H3v-8zm10 0h8v8h-8v-8z"/></svg>""",

    "music": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
        <path fill="{color}" d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
    </svg>""",
}


def _render_pixmap(svg_template: str, color: str, size: int) -> QPixmap:
    svg_content = svg_template.format(color=color)
    renderer = QSvgRenderer(QByteArray(svg_content.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    renderer.render(painter)
    painter.end()
    return pixmap


def get_svg_icon(name: str, color: str = "#ffffff", size: int = 64) -> QIcon:
    """Retorna um QIcon renderizado em alta resolução a partir do SVG."""
    template = SVG_ICONS.get(name)
    if not template:
        return QIcon()
    pixmap = _render_pixmap(template, color, size)
    return QIcon(pixmap)


def get_stateful_icon(
    name: str,
    normal_color: str = "#e0e0e0",
    hover_color: str = "#ffffff",
    disabled_color: str = "#666666",
    active_color: str = "#3b82f6",
    size: int = 64,
) -> QIcon:
    """Cria um QIcon com variações automáticas de estado (normal, hover, desabilitado, selecionado)."""
    template = SVG_ICONS.get(name)
    if not template:
        return QIcon()

    icon = QIcon()
    # Normal / Off
    icon.addPixmap(_render_pixmap(template, normal_color, size), QIcon.Mode.Normal, QIcon.State.Off)
    # Active / Hover
    icon.addPixmap(_render_pixmap(template, hover_color, size), QIcon.Mode.Active, QIcon.State.Off)
    # Disabled
    icon.addPixmap(_render_pixmap(template, disabled_color, size), QIcon.Mode.Disabled, QIcon.State.Off)
    # Selected / Checked
    icon.addPixmap(_render_pixmap(template, active_color, size), QIcon.Mode.Normal, QIcon.State.On)
    icon.addPixmap(_render_pixmap(template, active_color, size), QIcon.Mode.Active, QIcon.State.On)

    return icon
