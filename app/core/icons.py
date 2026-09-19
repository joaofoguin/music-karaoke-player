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
