from PySide6.QtCore import QTimer, QSize, Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QToolButton, QVBoxLayout, QWidget

from core.icons import get_svg_icon
from widgets.queue_item_widget import QueueItemWidget


class QueueWidget(QFrame):
    """Widget composto responsável pela apresentação visual da fila."""

    play_requested = Signal(int)
    play_next_requested = Signal(int)
    move_requested = Signal(int, int)
    remove_requested = Signal(int)
    clear_requested = Signal()

    def __init__(self, queue_controller, parent=None):
        super().__init__(parent)
        self.queue_controller = queue_controller
        self.setObjectName("panel")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._theme = "dark"
        self._build_ui()

    def _build_ui(self):
        layout_queue = QVBoxLayout(self)

        titulo_queue = QLabel("FILA DE REPRODUÇÃO")
        titulo_queue.setObjectName("sectionTitle")

        cabecalho_fila = QHBoxLayout()
        cabecalho_fila.setSpacing(4)
        cabecalho_fila.addWidget(titulo_queue, 1)

        self.btn_add_arquivos = QToolButton()
        self.btn_add_arquivos.setObjectName("panelAction")
        self.btn_add_arquivos.setIconSize(QSize(19, 19))
        self.btn_add_arquivos.setToolTip("Adicionar arquivos à fila (Ctrl+O)")
        cabecalho_fila.addWidget(self.btn_add_arquivos)

        self.botao_limpar_fila = QToolButton()
        self.botao_limpar_fila.setObjectName("panelAction")
        self.botao_limpar_fila.setIconSize(QSize(19, 19))
        self.botao_limpar_fila.setToolTip("Limpar fila de reprodução (Ctrl+L)")
        self.botao_limpar_fila.clicked.connect(self.clear_requested.emit)
        self.botao_limpar_fila.setEnabled(False)
        cabecalho_fila.addWidget(self.botao_limpar_fila)
        layout_queue.addLayout(cabecalho_fila)

        self.queue_scroll = QScrollArea()
        self.queue_scroll.setWidgetResizable(True)
        self.queue_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.queue_content = QWidget()
        self.queue_layout = QVBoxLayout(self.queue_content)
        self.queue_layout.setContentsMargins(0, 0, 0, 0)
        self.queue_layout.setSpacing(4)
        self.queue_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.queue_scroll.setWidget(self.queue_content)
        self.queue_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout_queue.addWidget(self.queue_scroll)

    def set_add_files_callback(self, callback):
        self.btn_add_arquivos.clicked.connect(callback)

    def atualizar_icones(self, tema="dark"):
        self._theme = tema
        cor_icone = "#374151" if tema == "light" else "#e5e7eb"
        self.btn_add_arquivos.setIcon(get_svg_icon("plus", color=cor_icone, size=64))
        self.botao_limpar_fila.setIcon(get_svg_icon("trash", color=cor_icone, size=64))

    def atualizar_fila(self):
        while self.queue_layout.count():
            item = self.queue_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        icon_color = "#374151" if self._theme == "light" else "#e5e7eb"
        for index, track in enumerate(self.queue_controller.tracks):
            item_widget = QueueItemWidget(
                index=index,
                track=track,
                is_current=index == self.queue_controller.current_index,
                is_next=index == self.queue_controller.current_index + 1,
                icon_color=icon_color,
                on_play=self.play_requested.emit,
                on_play_next=self.play_next_requested.emit,
                on_move=self.move_requested.emit,
                on_remove=self.remove_requested.emit,
                track_count=len(self.queue_controller.tracks),
            )
            self.queue_layout.addWidget(item_widget)

        self.botao_limpar_fila.setEnabled(bool(self.queue_controller.tracks))
        QTimer.singleShot(0, self._manter_faixas_atuais_visiveis)

    def _manter_faixas_atuais_visiveis(self):
        if not self.queue_controller.tracks or self.queue_controller.current_index < 0:
            return

        widgets = [self.queue_layout.itemAt(i).widget() for i in range(self.queue_layout.count())]
        widgets = [widget for widget in widgets if widget is not None]
        indice = self.queue_controller.current_index
        atual = widgets[indice] if indice < len(widgets) else None
        proxima = widgets[indice + 1] if indice + 1 < len(widgets) else None
        if atual is None:
            return

        barra = self.queue_scroll.verticalScrollBar()
        topo = atual.geometry().top()
        limite_inferior = proxima.geometry().bottom() if proxima is not None else atual.geometry().bottom()
        viewport = self.queue_scroll.viewport().height()
        valor = barra.value()
        if topo < valor:
            valor = topo
        elif limite_inferior > valor + viewport:
            valor = limite_inferior - viewport
        barra.setValue(max(0, min(valor, barra.maximum())))
