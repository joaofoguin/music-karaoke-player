from pathlib import Path

from PySide6.QtCore import QDir, QSize, Signal
from PySide6.QtWidgets import (
    QFrame,
    QFileSystemModel,
    QHBoxLayout,
    QLabel,
    QListView,
    QMenu,
    QStackedWidget,
    QToolButton,
    QTreeView,
    QVBoxLayout,
)

from core.icons import get_svg_icon


class ExplorerWidget(QFrame):
    """Encapsula o explorador de arquivos e seus modos de visualização."""

    file_selected = Signal(object)
    directory_changed = Signal(str)

    def __init__(self, audio_extensions=None, parent=None):
        super().__init__(parent)
        self.audio_extensions = set(audio_extensions or [])
        self._theme = "dark"
        self._open_folder_connection = None
        self.setObjectName("panel")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        self._build_ui()
        self.definir_modo_exibicao("details")

    def _build_ui(self):
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        header.setSpacing(4)

        title = QLabel("EXPLORADOR DE ARQUIVOS")
        title.setObjectName("sectionTitle")
        header.addWidget(title, 1)

        self.btn_abrir_pasta = QToolButton()
        self.btn_abrir_pasta.setObjectName("panelAction")
        self.btn_abrir_pasta.setIconSize(QSize(19, 19))
        self.btn_abrir_pasta.setToolTip("Alterar pasta do explorador")
        header.addWidget(self.btn_abrir_pasta)

        self.btn_modo = QToolButton()
        self.btn_modo.setObjectName("panelAction")
        self.btn_modo.setIconSize(QSize(19, 19))
        self.btn_modo.setToolTip("Layout e exibição")

        self.menu_modo = QMenu(self)
        for texto, modo, icone in [
            ("Detalhes", "details", "view_details"),
            ("Lista", "list", "view_list"),
            ("Ícones pequenos", "small", "view_grid"),
            ("Ícones grandes", "large", "view_large"),
        ]:
            acao = self.menu_modo.addAction(texto)
            acao.setData(modo)
            acao.triggered.connect(
                lambda checked=False, m=modo: self.definir_modo_exibicao(m)
            )

        self.btn_modo.setMenu(self.menu_modo)
        self.btn_modo.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        header.addWidget(self.btn_modo)
        layout.addLayout(header)

        self.file_model = QFileSystemModel()
        self.file_model.setFilter(
            QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot
        )
        self.file_model.setRootPath("")

        self.file_stack = QStackedWidget()

        self.file_tree = QTreeView()
        self.file_tree.setModel(self.file_model)
        self.file_tree.setRootIndex(self.file_model.index(""))
        self.file_tree.setAlternatingRowColors(True)
        self.file_tree.setSortingEnabled(True)
        self.file_tree.setColumnWidth(0, 300)
        self.file_tree.setColumnWidth(1, 90)
        self.file_tree.setColumnWidth(2, 130)
        self.file_tree.setColumnWidth(3, 165)
        self.file_tree.doubleClicked.connect(self._arquivo_selecionado)

        self.file_list = QListView()
        self.file_list.setModel(self.file_model)
        self.file_list.setRootIndex(self.file_model.index(""))
        self.file_list.doubleClicked.connect(self._arquivo_selecionado)
        self.file_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.file_list.setSpacing(6)
        self.file_list.setUniformItemSizes(True)

        self.file_stack.addWidget(self.file_tree)
        self.file_stack.addWidget(self.file_list)
        layout.addWidget(self.file_stack)

        self.atualizar_icones(self._theme)

    def set_open_folder_callback(self, callback):
        if self._open_folder_connection is not None:
            self.btn_abrir_pasta.clicked.disconnect(self._open_folder_connection)
        self._open_folder_connection = self.btn_abrir_pasta.clicked.connect(callback)

    def set_audio_extensions(self, extensions):
        self.audio_extensions = set(extensions or [])

    def set_font_size(self, size: float):
        """Define o tamanho da fonte dos nomes e detalhes do explorador."""
        font = self.file_tree.font()
        font.setPointSizeF(float(size))
        self.file_tree.setFont(font)
        self.file_list.setFont(font)

    def definir_diretorio(self, pasta: str):
        caminho = Path(pasta)
        if not caminho.is_dir():
            return

        self.file_model.setRootPath(pasta)
        index = self.file_model.index(pasta)
        self.file_tree.setRootIndex(index)
        self.file_list.setRootIndex(index)
        self.directory_changed.emit(str(caminho))

    def definir_modo_exibicao(self, modo: str):
        if modo == "details":
            self.file_stack.setCurrentWidget(self.file_tree)
            self.file_tree.setColumnHidden(1, False)
            self.file_tree.setColumnHidden(2, False)
            self.file_tree.setColumnHidden(3, False)
            self.file_tree.setColumnWidth(0, max(300, self.file_tree.width() // 2))
        else:
            self.file_stack.setCurrentWidget(self.file_list)
            self.file_tree.setColumnHidden(1, True)
            self.file_tree.setColumnHidden(2, True)
            self.file_tree.setColumnHidden(3, True)

            if modo == "list":
                self.file_list.setViewMode(QListView.ViewMode.ListMode)
                self.file_list.setFlow(QListView.Flow.LeftToRight)
                self.file_list.setWrapping(True)
                self.file_list.setGridSize(QSize(340, 34))
                self.file_list.setIconSize(QSize(20, 20))
            elif modo == "small":
                self.file_list.setViewMode(QListView.ViewMode.IconMode)
                self.file_list.setFlow(QListView.Flow.LeftToRight)
                self.file_list.setWrapping(True)
                self.file_list.setGridSize(QSize(120, 72))
                self.file_list.setIconSize(QSize(32, 32))
            else:
                self.file_list.setViewMode(QListView.ViewMode.IconMode)
                self.file_list.setFlow(QListView.Flow.LeftToRight)
                self.file_list.setWrapping(True)
                self.file_list.setGridSize(QSize(170, 110))
                self.file_list.setIconSize(QSize(64, 64))

        self._atualizar_icone_modo(modo)

    def atualizar_icones(self, tema="dark"):
        self._theme = tema
        cor = "#374151" if tema == "light" else "#e5e7eb"
        self.btn_abrir_pasta.setIcon(get_svg_icon("folder", color=cor, size=64))

        icones = {
            "details": "view_details",
            "list": "view_list",
            "small": "view_grid",
            "large": "view_large",
        }
        for acao in self.menu_modo.actions():
            modo = acao.data()
            if modo in icones:
                acao.setIcon(get_svg_icon(icones[modo], color=cor, size=48))

        self._atualizar_icone_modo(
            self._modo_atual(), cor=cor
        )

    def _modo_atual(self):
        if self.file_stack.currentWidget() is self.file_tree:
            return "details"
        view_mode = self.file_list.viewMode()
        if view_mode == QListView.ViewMode.ListMode:
            return "list"
        return "small" if self.file_list.iconSize().width() <= 32 else "large"

    def _atualizar_icone_modo(self, modo, cor=None):
        icones = {
            "details": "view_details",
            "list": "view_list",
            "small": "view_grid",
            "large": "view_large",
        }
        if cor is None:
            cor = "#374151" if self._theme == "light" else "#e5e7eb"
        self.btn_modo.setIcon(get_svg_icon(icones.get(modo, "view_details"), color=cor, size=64))

    def _arquivo_selecionado(self, index):
        caminho = Path(self.file_model.filePath(index))
        if not caminho.is_file():
            return
        if caminho.suffix.lower() not in self.audio_extensions:
            return
        self.file_selected.emit(caminho)
