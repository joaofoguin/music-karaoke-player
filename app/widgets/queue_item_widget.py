from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu, QPushButton, QVBoxLayout

from core.icons import get_svg_icon


class QueueItemWidget(QFrame):
    """Widget visual de uma faixa da fila de reprodução."""

    def __init__(self, index, track, is_current, is_next, icon_color, on_play, on_play_next, on_move, on_remove, track_count, parent=None):
        super().__init__(parent)
        self.index = index
        self.track = track
        self.is_current = is_current
        self.is_next = is_next
        self._icon_color = icon_color
        self._on_play = on_play
        self._on_play_next = on_play_next
        self._on_move = on_move
        self._on_remove = on_remove
        self._track_count = track_count
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._mostrar_menu_contexto)
        self._montar_layout()

    def _limitar_texto(self, texto: str, limite: int) -> str:
        if len(texto) <= limite:
            return texto
        return texto[:max(1, limite - 3)].rstrip() + "..."

    def _montar_layout(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(6)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(1)
        artista = self.track.artist if self.track.artist else "Artista desconhecido"
        duracao = self._formatar_duracao(self.track.duration)
        tag = " [Tocando Agora]" if self.is_current else " [A Seguir]" if self.is_next else ""
        lbl_titulo = QLabel(self._limitar_texto(f"{self.index + 1:02d}. {self.track.title}{tag}", 42))
        lbl_titulo.setStyleSheet("font-weight: bold; font-size: 13px;")
        lbl_sub = QLabel(self._limitar_texto(f"{artista}  •  {duracao}", 42))
        lbl_sub.setStyleSheet("font-size: 11px; opacity: 0.85;")
        info_layout.addWidget(lbl_titulo)
        info_layout.addWidget(lbl_sub)
        layout.addLayout(info_layout, 1)
        if self.is_current:
            self.setStyleSheet("QueueItemWidget { background-color: #1f7300; color: #ffffff; border-radius: 6px; border-left: 5px solid #4ade80; } QLabel { color: #ffffff; }")
        elif self.is_next:
            self.setStyleSheet("QueueItemWidget { background-color: #735600; color: #ffffff; border-radius: 6px; border-left: 5px solid #f59e0b; } QLabel { color: #ffffff; }")
        else:
            self.setStyleSheet("QueueItemWidget { background-color: #242424; color: #d8d8d8; border: 1px solid #383838; border-radius: 6px; } QueueItemWidget:hover { background-color: #2e2e2e; border-color: #4b5563; } QLabel { color: #e5e7eb; }")
        if not self.is_current:
            btn_next = self._criar_botao("next", "Tocar a seguir (Definir como próxima na fila)")
            btn_next.clicked.connect(lambda: self._on_play_next(self.index))
            layout.addWidget(btn_next)
        btn_subir = self._criar_botao("arrow_up", "Mover para cima")
        btn_subir.setEnabled(self.index > 0)
        btn_subir.clicked.connect(lambda: self._on_move(self.index, self.index - 1))
        layout.addWidget(btn_subir)
        btn_descer = self._criar_botao("arrow_down", "Mover para baixo")
        btn_descer.setEnabled(self.index < self._track_count - 1)
        btn_descer.clicked.connect(lambda: self._on_move(self.index, self.index + 1))
        layout.addWidget(btn_descer)
        btn_remover = self._criar_botao("trash", "Remover da fila")
        btn_remover.clicked.connect(lambda: self._on_remove(self.index))
        layout.addWidget(btn_remover)

    def _criar_botao(self, icon_name: str, tooltip: str) -> QPushButton:
        button = QPushButton()
        button.setToolTip(tooltip)
        button.setObjectName("queueActionButton")
        button.setIcon(get_svg_icon(icon_name, color=self._icon_color, size=48))
        button.setIconSize(QSize(17, 17))
        button.setFixedSize(30, 30)
        return button

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_play(self.index)
        super().mouseDoubleClickEvent(event)

    def _mostrar_menu_contexto(self, pos: QPoint):
        menu = QMenu(self)
        acao_play = QAction("Reproduzir Agora (Duplo Clique)", self)
        acao_play.triggered.connect(lambda: self._on_play(self.index))
        menu.addAction(acao_play)
        if not self.is_current:
            acao_next = QAction("Tocar a Seguir (Definir como Próxima)", self)
            acao_next.triggered.connect(lambda: self._on_play_next(self.index))
            menu.addAction(acao_next)
        menu.addSeparator()
        if self.index > 0:
            acao_up = QAction("Mover para Cima", self)
            acao_up.triggered.connect(lambda: self._on_move(self.index, self.index - 1))
            menu.addAction(acao_up)
        if self.index < self._track_count - 1:
            acao_down = QAction("Mover para Baixo", self)
            acao_down.triggered.connect(lambda: self._on_move(self.index, self.index + 1))
            menu.addAction(acao_down)
        acao_del = QAction("Remover da Fila", self)
        acao_del.triggered.connect(lambda: self._on_remove(self.index))
        menu.addAction(acao_del)
        menu.exec(self.mapToGlobal(pos))

    @staticmethod
    def _formatar_duracao(segundos) -> str:
        segundos = int(segundos)
        return f"{segundos // 60:02d}:{segundos % 60:02d}"
