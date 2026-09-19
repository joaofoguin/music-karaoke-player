import sys
from pathlib import Path

from PySide6.QtCore import QDir, QPoint, QSize, Qt
from PySide6.QtGui import QAction, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QFileSystemModel,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QStyle,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from models.track import Track
from core.queue_manager import QueueManager
from core.audio_engine import AudioEngine
from core.metadata_reader import ler_metadados
from core.config_manager import ConfigManager
from core.icons import get_svg_icon, get_stateful_icon
from core.clickable_slider import ClickableSlider
from karaoke_window import KaraokeWindow
from karaoke_editor import KaraokeEditorWindow
from settings_dialog import SettingsDialog


class QueueItemWidget(QFrame):
    """Widget de item de fila com suporte a duplo clique para reproduzir e menu de contexto."""

    def __init__(self, main_window, index, track, is_current, is_next, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.index = index
        self.track = track
        self.is_current = is_current
        self.is_next = is_next

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._mostrar_menu_contexto)

        self._montar_layout()

    def _montar_layout(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)

        # Informações da faixa
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        titulo = self.track.title
        artista = self.track.artist if self.track.artist else "Artista desconhecido"
        duracao = self.main_window.formatar_duracao(self.track.duration)

        if self.is_current:
            prefixo = "▶ "
            tag = " [Tocando Agora]"
        elif self.is_next:
            prefixo = "⏭ "
            tag = " [A Seguir]"
        else:
            prefixo = ""
            tag = ""

        lbl_titulo = QLabel(f"{prefixo}{self.index + 1:02d}. {titulo}{tag}")
        lbl_titulo.setStyleSheet("font-weight: bold; font-size: 13px;")

        lbl_sub = QLabel(f"{artista}  •  {duracao}")
        lbl_sub.setStyleSheet("font-size: 11px; opacity: 0.85;")

        info_layout.addWidget(lbl_titulo)
        info_layout.addWidget(lbl_sub)
        layout.addLayout(info_layout, 1)

        # Estilização
        if self.is_current:
            self.setStyleSheet(
                "QueueItemWidget { background-color: #1f7300; color: #ffffff; border-radius: 6px; border-left: 5px solid #4ade80; }"
                "QLabel { color: #ffffff; }"
            )
        elif self.is_next:
            self.setStyleSheet(
                "QueueItemWidget { background-color: #735600; color: #ffffff; border-radius: 6px; border-left: 5px solid #f59e0b; }"
                "QLabel { color: #ffffff; }"
            )
        else:
            self.setStyleSheet(
                "QueueItemWidget { background-color: #242424; color: #d8d8d8; border: 1px solid #383838; border-radius: 6px; }"
                "QueueItemWidget:hover { background-color: #2e2e2e; border-color: #4b5563; }"
                "QLabel { color: #e5e7eb; }"
            )

        # Botão "Tocar a seguir"
        if not self.is_current:
            btn_next = QPushButton("⏭")
            btn_next.setToolTip("Tocar a seguir (Definir como próxima na fila)")
            btn_next.setFixedWidth(28)
            btn_next.clicked.connect(lambda: self.main_window.definir_tocar_a_seguir(self.index))
            layout.addWidget(btn_next)

        # Botão subir
        btn_subir = QPushButton("↑")
        btn_subir.setToolTip("Mover para cima")
        btn_subir.setFixedWidth(26)
        btn_subir.setEnabled(self.index > 0)
        btn_subir.clicked.connect(lambda: self.main_window.mover_faixa(self.index, self.index - 1))
        layout.addWidget(btn_subir)

        # Botão descer
        btn_descer = QPushButton("↓")
        btn_descer.setToolTip("Mover para baixo")
        btn_descer.setFixedWidth(26)
        btn_descer.setEnabled(self.index < len(self.main_window.queue_manager.tracks) - 1)
        btn_descer.clicked.connect(lambda: self.main_window.mover_faixa(self.index, self.index + 1))
        layout.addWidget(btn_descer)

        # Botão remover
        btn_remover = QPushButton("×")
        btn_remover.setToolTip("Remover da fila")
        btn_remover.setFixedWidth(26)
        btn_remover.clicked.connect(lambda: self.main_window.remover_faixa(self.index))
        layout.addWidget(btn_remover)

    def mouseDoubleClickEvent(self, event):
        """Ao dar duplo clique em qualquer ponto do item, reproduz a música imediatamente."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.main_window.selecionar_e_reproduzir_faixa(self.index)
        super().mouseDoubleClickEvent(event)

    def _mostrar_menu_contexto(self, pos: QPoint):
        menu = QMenu(self)

        acao_play = QAction("▶ Reproduzir Agora (Duplo Clique)", self)
        acao_play.triggered.connect(lambda: self.main_window.selecionar_e_reproduzir_faixa(self.index))
        menu.addAction(acao_play)

        if not self.is_current:
            acao_next = QAction("⏭ Tocar a Seguir (Definir como Próxima)", self)
            acao_next.triggered.connect(lambda: self.main_window.definir_tocar_a_seguir(self.index))
            menu.addAction(acao_next)

        menu.addSeparator()

        if self.index > 0:
            acao_up = QAction("↑ Mover para Cima", self)
            acao_up.triggered.connect(lambda: self.main_window.mover_faixa(self.index, self.index - 1))
            menu.addAction(acao_up)

        if self.index < len(self.main_window.queue_manager.tracks) - 1:
            acao_down = QAction("↓ Mover para Baixo", self)
            acao_down.triggered.connect(lambda: self.main_window.mover_faixa(self.index, self.index + 1))
            menu.addAction(acao_down)

        acao_del = QAction("× Remover da Fila", self)
        acao_del.triggered.connect(lambda: self.main_window.remover_faixa(self.index))
        menu.addAction(acao_del)

        menu.exec(self.mapToGlobal(pos))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Music Player")
        self.resize(1200, 720)
        self.setMinimumSize(900, 560)

        self.config_manager = ConfigManager()
        self.queue_manager = QueueManager()
        self.audio_engine = AudioEngine()
        self.karaoke_window = None
        self.karaoke_editor = None
        self._volume_anterior_mudo = None
        self._anterior_ja_reiniciou = False

        self.audio_engine.playback_finished.connect(self.faixa_terminou)
        self.config_manager.settings_changed.connect(self.aplicar_configuracoes)

        self.audio_extensions = set(
            self.config_manager.get(
                "playback/audio_extensions",
                [".mp3", ".wav", ".flac", ".ogg", ".opus", ".m4a", ".aac", ".wma"],
            )
        )

        self.criar_interface()
        self.criar_atalhos()
        self.aplicar_estilo()
        self.carregar_estado_inicial()

    def aplicar_configuracoes(self):
        """Atualiza o comportamento e aparência do player conforme as configurações salvas."""
        self.audio_extensions = set(
            self.config_manager.get(
                "playback/audio_extensions",
                [".mp3", ".wav", ".flac", ".ogg", ".opus", ".m4a", ".aac", ".wma"],
            )
        )
        self.aplicar_estilo()

    def obter_tema_qss(self, tema: str) -> str:
        if tema == "midnight":
            return """
            QMainWindow { background: #0b0d11; color: #f3f4f6; }
            QMenuBar { background: #131720; color: #e5e7eb; border-bottom: 1px solid #1f2937; padding: 4px 8px; }
            QMenuBar::item:selected, QMenu::item:selected { background: #2563eb; color: #ffffff; }
            QMenu { background: #131720; color: #f3f4f6; border: 1px solid #374151; }
            QFrame#panel { background: #131720; border: 1px solid #1f2937; border-radius: 8px; }
            QFrame#playerBar { background: #0f131a; border: 1px solid #1f2937; border-radius: 8px; }
            QLabel#sectionTitle { color: #60a5fa; font-size: 12px; font-weight: 700; letter-spacing: 1px; padding: 4px; }
            QLabel#trackTitle { color: #ffffff; font-size: 16px; font-weight: 700; }
            QLabel#trackMetadata { color: #9ca3af; font-size: 12px; }
            QTreeView, QScrollArea { background: #0b0d11; border: 1px solid #1f2937; color: #e5e7eb; border-radius: 4px; }
            QTreeView::item:selected { background: #2563eb; color: #ffffff; }
            QHeaderView::section { background: #131720; color: #9ca3af; border: 0; border-bottom: 1px solid #1f2937; padding: 6px; }
            QPushButton { background: #1f2937; color: #f3f4f6; border: 1px solid #374151; border-radius: 4px; min-height: 28px; padding: 2px 10px; font-weight: 500; }
            QPushButton:hover { background: #374151; border-color: #4b5563; }
            QPushButton:pressed { background: #111827; }
            QPushButton:disabled { color: #6b7280; background: #131720; border-color: #1f2937; }
            QPushButton#mediaButton { background: transparent; border: 0; min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px; padding: 4px; border-radius: 18px; }
            QPushButton#mediaButton:hover { background: #1f2937; }
            QPushButton#mediaButton:pressed { background: #111827; }
            QPushButton#mediaButton:checked { background: rgba(37, 99, 235, 0.3); border: 1px solid #3b82f6; }
            QPushButton#mainPlayButton { background: #2563eb; color: #ffffff; border: 0; border-radius: 20px; min-width: 40px; max-width: 40px; min-height: 40px; max-height: 40px; padding: 0; }
            QPushButton#mainPlayButton:hover { background: #3b82f6; }
            QPushButton#mainPlayButton:pressed { background: #1d4ed8; }
            QSlider::groove:horizontal { height: 6px; background: #1f2937; border-radius: 3px; }
            QSlider::handle:horizontal { width: 14px; margin: -4px 0; background: #60a5fa; border-radius: 7px; }
            QScrollBar:vertical { background: #0b0d11; width: 10px; }
            QScrollBar::handle:vertical { background: #374151; border-radius: 4px; min-height: 24px; }
            """
        elif tema == "light":
            return """
            QMainWindow { background: #f3f4f6; color: #111827; }
            QMenuBar { background: #ffffff; color: #374151; border-bottom: 1px solid #e5e7eb; padding: 4px 8px; }
            QMenuBar::item:selected, QMenu::item:selected { background: #e5e7eb; }
            QMenu { background: #ffffff; color: #111827; border: 1px solid #d1d5db; }
            QFrame#panel { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; }
            QFrame#playerBar { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; }
            QLabel#sectionTitle { color: #2563eb; font-size: 12px; font-weight: 700; letter-spacing: 1px; padding: 4px; }
            QLabel#trackTitle { color: #111827; font-size: 16px; font-weight: 700; }
            QLabel#trackMetadata { color: #6b7280; font-size: 12px; }
            QTreeView, QScrollArea { background: #f9fafb; border: 1px solid #e5e7eb; color: #111827; border-radius: 4px; }
            QTreeView::item:selected { background: #2563eb; color: #ffffff; }
            QHeaderView::section { background: #f3f4f6; color: #4b5563; border: 0; border-bottom: 1px solid #e5e7eb; padding: 6px; }
            QPushButton { background: #f9fafb; color: #1f2937; border: 1px solid #d1d5db; border-radius: 4px; min-height: 28px; padding: 2px 10px; font-weight: 500; }
            QPushButton:hover { background: #e5e7eb; }
            QPushButton:pressed { background: #d1d5db; }
            QPushButton:disabled { color: #9ca3af; background: #f3f4f6; border-color: #e5e7eb; }
            QPushButton#mediaButton { background: transparent; border: 0; min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px; padding: 4px; border-radius: 18px; }
            QPushButton#mediaButton:hover { background: #e5e7eb; }
            QPushButton#mediaButton:pressed { background: #d1d5db; }
            QPushButton#mediaButton:checked { background: rgba(37, 99, 235, 0.15); border: 1px solid #2563eb; }
            QPushButton#mainPlayButton { background: #2563eb; color: #ffffff; border: 0; border-radius: 20px; min-width: 40px; max-width: 40px; min-height: 40px; max-height: 40px; padding: 0; }
            QPushButton#mainPlayButton:hover { background: #1d4ed8; }
            QPushButton#mainPlayButton:pressed { background: #1e40af; }
            QSlider::groove:horizontal { height: 6px; background: #e5e7eb; border-radius: 3px; }
            QSlider::handle:horizontal { width: 14px; margin: -4px 0; background: #2563eb; border-radius: 7px; }
            QScrollBar:vertical { background: #f3f4f6; width: 10px; }
            QScrollBar::handle:vertical { background: #cbd5e1; border-radius: 4px; min-height: 24px; }
            """
        else:
            # Tema Escuro Moderno Padrão
            return """
            QMainWindow { background: #171717; color: #f4f4f4; }
            QMenuBar { background: #242424; color: #d8d8d8; border-bottom: 1px solid #3c3c3c; padding: 3px 8px; }
            QMenuBar::item:selected, QMenu::item:selected { background: #3c3c3c; }
            QMenu { background: #242424; color: #f4f4f4; border: 1px solid #4a4a4a; }
            QFrame#panel { background: #242424; border: 1px solid #3f3f3f; border-radius: 6px; }
            QFrame#playerBar { background: #181818; border: 1px solid #303030; border-radius: 6px; }
            QLabel#sectionTitle { color: #f0f0f0; font-size: 12px; font-weight: 700; letter-spacing: 1px; padding: 4px; }
            QLabel#trackTitle { color: #ffffff; font-size: 16px; font-weight: 700; }
            QLabel#trackMetadata { color: #a8a8a8; font-size: 12px; }
            QTreeView, QScrollArea { background: #1d1d1d; border: 1px solid #393939; color: #d8d8d8; }
            QTreeView::item:selected { background: #365d8d; color: #ffffff; }
            QHeaderView::section { background: #2c2c2c; color: #bdbdbd; border: 0; border-bottom: 1px solid #454545; padding: 5px; }
            QPushButton { background: #363636; color: #f2f2f2; border: 1px solid #4d4d4d; border-radius: 4px; min-height: 26px; padding: 2px 8px; }
            QPushButton:hover { background: #4a4a4a; }
            QPushButton:pressed { background: #2b2b2b; }
            QPushButton:disabled { color: #777777; background: #2a2a2a; }
            QPushButton#mediaButton { background: transparent; border: 0; min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px; padding: 4px; border-radius: 18px; }
            QPushButton#mediaButton:hover { background: rgba(255, 255, 255, 0.12); }
            QPushButton#mediaButton:pressed { background: rgba(255, 255, 255, 0.2); }
            QPushButton#mediaButton:checked { background: rgba(59, 130, 246, 0.25); border: 1px solid #3b82f6; }
            QPushButton#mainPlayButton { background: #f4f4f4; border: 0; border-radius: 20px; min-width: 40px; max-width: 40px; min-height: 40px; max-height: 40px; padding: 0; }
            QPushButton#mainPlayButton:hover { background: #ffffff; }
            QPushButton#mainPlayButton:pressed { background: #e0e0e0; }
            QSlider::groove:horizontal { height: 6px; background: #4a4a4a; border-radius: 3px; }
            QSlider::handle:horizontal { width: 14px; margin: -4px 0; background: #e0e0e0; border-radius: 7px; }
            QScrollBar:vertical { background: #1d1d1d; width: 10px; }
            QScrollBar::handle:vertical { background: #555555; border-radius: 4px; min-height: 24px; }
            """

    def aplicar_estilo(self):
        tema = self.config_manager.get("appearance/theme", "dark")
        self.setStyleSheet(self.obter_tema_qss(tema))
        self.atualizar_icones()

    def atualizar_icones(self):
        """Aplica ícones vetoriais em alta resolução e contraste adequado aos botões do reprodutor."""
        tema = self.config_manager.get("appearance/theme", "dark")
        cor_icone = "#374151" if tema == "light" else "#e5e7eb"
        cor_destaque = "#2563eb" if tema == "light" else "#3b82f6"

        self.botao_anterior.setIcon(get_svg_icon("previous", color=cor_icone, size=64))
        self.botao_anterior.setIconSize(QSize(20, 20))
        self.botao_anterior.setText("")

        self.botao_proximo.setIcon(get_svg_icon("next", color=cor_icone, size=64))
        self.botao_proximo.setIconSize(QSize(20, 20))
        self.botao_proximo.setText("")

        self.botao_repetir.setIcon(
            get_stateful_icon("repeat", normal_color=cor_icone, active_color=cor_destaque, size=64)
        )
        self.botao_repetir.setIconSize(QSize(18, 18))
        self.botao_repetir.setText("")

        self.botao_karaoke.setIcon(get_svg_icon("microphone", color=cor_icone, size=64))
        self.botao_karaoke.setIconSize(QSize(18, 18))
        self.botao_karaoke.setText("")

        self.atualizar_botao_play()
        self.atualizar_icone_volume(self.volume.value())

    def atualizar_botao_play(self):
        tema = self.config_manager.get("appearance/theme", "dark")
        cor_play = "#171717" if tema == "dark" else "#ffffff"

        if self.audio_engine.is_playing():
            self.botao_play.setIcon(get_svg_icon("pause", color=cor_play, size=64))
            self.botao_play.setToolTip("Pausar (Espaço)")
        else:
            self.botao_play.setIcon(get_svg_icon("play", color=cor_play, size=64))
            self.botao_play.setToolTip("Reproduzir (Espaço)")

        self.botao_play.setIconSize(QSize(20, 20))
        self.botao_play.setText("")

    def atualizar_icone_volume(self, valor: int):
        tema = self.config_manager.get("appearance/theme", "dark")
        cor_icone = "#374151" if tema == "light" else "#e5e7eb"

        if valor == 0:
            self.btn_vol_icon.setIcon(get_svg_icon("volume_mute", color=cor_icone, size=64))
        elif valor < 45:
            self.btn_vol_icon.setIcon(get_svg_icon("volume_low", color=cor_icone, size=64))
        else:
            self.btn_vol_icon.setIcon(get_svg_icon("volume_high", color=cor_icone, size=64))

        self.btn_vol_icon.setIconSize(QSize(18, 18))
        self.btn_vol_icon.setText("")

    def criar_atalhos(self):
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self.alternar_reproducao)
        QShortcut(QKeySequence("Ctrl+Right"), self, self.faixa_proxima)
        QShortcut(QKeySequence("Ctrl+Left"), self, self.faixa_anterior)
        QShortcut(QKeySequence("Ctrl+Up"), self, self.aumentar_volume)
        QShortcut(QKeySequence("Ctrl+Down"), self, self.diminuir_volume)
        QShortcut(QKeySequence("Ctrl+M"), self, self.alternar_mudo)
        QShortcut(QKeySequence("Ctrl+R"), self, self.alternar_repetir)
        QShortcut(QKeySequence("Ctrl+K"), self, self.abrir_tela_karaoke)
        QShortcut(QKeySequence("Ctrl+E"), self, self.abrir_editor_karaoke)
        QShortcut(QKeySequence("Ctrl+O"), self, self.abrir_arquivos_dialogo)
        QShortcut(QKeySequence("Ctrl+Shift+O"), self, self.abrir_pasta_dialogo)
        QShortcut(QKeySequence("Ctrl+L"), self, self.limpar_fila)
        QShortcut(QKeySequence("Ctrl+,"), self, self.abrir_dialogo_configuracoes)
        QShortcut(QKeySequence("F11"), self, self.alternar_tela_cheia)

    def criar_interface(self):
        # ==================================================
        # MENU SUPERIOR
        # ==================================================
        menu_bar = QMenuBar()

        # Menu Arquivo
        menu_arquivo = menu_bar.addMenu("&Arquivo")
        acao_abrir_arquivos = QAction("Abrir Arquivo(s)...", self)
        acao_abrir_arquivos.setShortcut(QKeySequence("Ctrl+O"))
        acao_abrir_arquivos.triggered.connect(self.abrir_arquivos_dialogo)
        menu_arquivo.addAction(acao_abrir_arquivos)

        acao_abrir_pasta = QAction("Abrir Pasta...", self)
        acao_abrir_pasta.setShortcut(QKeySequence("Ctrl+Shift+O"))
        acao_abrir_pasta.triggered.connect(self.abrir_pasta_dialogo)
        menu_arquivo.addAction(acao_abrir_pasta)

        menu_arquivo.addSeparator()

        acao_sair = QAction("Sair", self)
        acao_sair.setShortcut(QKeySequence("Ctrl+Q"))
        acao_sair.triggered.connect(self.close)
        menu_arquivo.addAction(acao_sair)

        # Menu Editar
        menu_editar = menu_bar.addMenu("&Editar")
        acao_limpar_fila = QAction("Limpar Fila", self)
        acao_limpar_fila.setShortcut(QKeySequence("Ctrl+L"))
        acao_limpar_fila.triggered.connect(self.limpar_fila)
        menu_editar.addAction(acao_limpar_fila)

        acao_remover_atual = QAction("Remover Faixa Atual", self)
        acao_remover_atual.triggered.connect(self.remover_faixa_atual)
        menu_editar.addAction(acao_remover_atual)

        # Menu Exibir
        menu_exibir = menu_bar.addMenu("&Exibir")
        acao_karaoke = QAction("Abrir Tela de Karaoke", self)
        acao_karaoke.setShortcut(QKeySequence("Ctrl+K"))
        acao_karaoke.triggered.connect(self.abrir_tela_karaoke)
        menu_exibir.addAction(acao_karaoke)

        acao_tela_cheia = QAction("Alternar Tela Cheia", self)
        acao_tela_cheia.setShortcut(QKeySequence("F11"))
        acao_tela_cheia.triggered.connect(self.alternar_tela_cheia)
        menu_exibir.addAction(acao_tela_cheia)

        # Menu Ferramentas
        menu_ferramentas = menu_bar.addMenu("&Ferramentas")
        acao_editor_karaoke = QAction("Editor de Karaoke e Cifras...", self)
        acao_editor_karaoke.setShortcut(QKeySequence("Ctrl+E"))
        acao_editor_karaoke.triggered.connect(self.abrir_editor_karaoke)
        menu_ferramentas.addAction(acao_editor_karaoke)

        # Menu Controles
        menu_controles = menu_bar.addMenu("&Controles")
        acao_play_pause = QAction("Reproduzir / Pausar", self)
        acao_play_pause.setShortcut(QKeySequence("Space"))
        acao_play_pause.triggered.connect(self.alternar_reproducao)
        menu_controles.addAction(acao_play_pause)

        acao_anterior = QAction("Faixa Anterior", self)
        acao_anterior.setShortcut(QKeySequence("Ctrl+Left"))
        acao_anterior.triggered.connect(self.faixa_anterior)
        menu_controles.addAction(acao_anterior)

        acao_proxima = QAction("Próxima Faixa", self)
        acao_proxima.setShortcut(QKeySequence("Ctrl+Right"))
        acao_proxima.triggered.connect(self.faixa_proxima)
        menu_controles.addAction(acao_proxima)

        menu_controles.addSeparator()

        acao_vol_up = QAction("Aumentar Volume", self)
        acao_vol_up.setShortcut(QKeySequence("Ctrl+Up"))
        acao_vol_up.triggered.connect(self.aumentar_volume)
        menu_controles.addAction(acao_vol_up)

        acao_vol_down = QAction("Diminuir Volume", self)
        acao_vol_down.setShortcut(QKeySequence("Ctrl+Down"))
        acao_vol_down.triggered.connect(self.diminuir_volume)
        menu_controles.addAction(acao_vol_down)

        acao_mudo = QAction("Alternar Mudo", self)
        acao_mudo.setShortcut(QKeySequence("Ctrl+M"))
        acao_mudo.triggered.connect(self.alternar_mudo)
        menu_controles.addAction(acao_mudo)

        acao_repetir_toggle = QAction("Repetir Faixa Atual", self)
        acao_repetir_toggle.setShortcut(QKeySequence("Ctrl+R"))
        acao_repetir_toggle.triggered.connect(self.alternar_repetir)
        menu_controles.addAction(acao_repetir_toggle)

        # Menu Configurações
        menu_config = menu_bar.addMenu("&Configurações")
        acao_preferencias = QAction("Preferências...", self)
        acao_preferencias.setShortcut(QKeySequence("Ctrl+,"))
        acao_preferencias.triggered.connect(self.abrir_dialogo_configuracoes)
        menu_config.addAction(acao_preferencias)

        # Menu Ajuda
        menu_ajuda = menu_bar.addMenu("&Ajuda")
        acao_atalhos = QAction("Atalhos do Teclado", self)
        acao_atalhos.triggered.connect(self.mostrar_atalhos)
        menu_ajuda.addAction(acao_atalhos)

        acao_sobre = QAction("Sobre o Music Player", self)
        acao_sobre.triggered.connect(self.mostrar_sobre)
        menu_ajuda.addAction(acao_sobre)

        self.setMenuBar(menu_bar)

        # ==================================================
        # WIDGET CENTRAL
        # ==================================================
        central = QWidget()
        self.setCentralWidget(central)

        layout_principal = QVBoxLayout(central)
        layout_principal.setContentsMargins(18, 18, 18, 18)
        layout_principal.setSpacing(16)

        # ==================================================
        # ÁREA SUPERIOR
        # ==================================================
        layout_superior = QHBoxLayout()
        layout_superior.setSpacing(16)

        # ==================================================
        # EXPLORADOR
        # ==================================================
        explorer = QFrame()
        explorer.setObjectName("panel")
        explorer.setFrameShape(QFrame.Shape.StyledPanel)

        layout_explorer = QVBoxLayout(explorer)

        cabecalho_explorer = QHBoxLayout()
        titulo_explorer = QLabel("EXPLORADOR DE ARQUIVOS")
        titulo_explorer.setObjectName("sectionTitle")
        cabecalho_explorer.addWidget(titulo_explorer, 1)

        btn_abrir_pasta_exp = QPushButton("Abrir Pasta...")
        btn_abrir_pasta_exp.setToolTip("Alterar pasta do explorador")
        btn_abrir_pasta_exp.clicked.connect(self.abrir_pasta_dialogo)
        cabecalho_explorer.addWidget(btn_abrir_pasta_exp)
        layout_explorer.addLayout(cabecalho_explorer)

        self.file_model = QFileSystemModel()
        self.file_model.setFilter(
            QDir.Filter.AllDirs |
            QDir.Filter.Files |
            QDir.Filter.NoDotAndDotDot
        )
        self.file_model.setRootPath("")

        self.file_tree = QTreeView()
        self.file_tree.doubleClicked.connect(self.arquivo_selecionado)
        self.file_tree.setModel(self.file_model)
        self.file_tree.setRootIndex(self.file_model.index(""))

        layout_explorer.addWidget(self.file_tree)

        # ==================================================
        # FILA DE REPRODUÇÃO (COM DUPLO CLIQUE E TOCAR A SEGUIR)
        # ==================================================
        queue = QFrame()
        queue.setObjectName("panel")
        queue.setFrameShape(QFrame.Shape.StyledPanel)

        layout_queue = QVBoxLayout(queue)

        titulo_queue = QLabel("FILA DE REPRODUÇÃO")
        titulo_queue.setObjectName("sectionTitle")

        cabecalho_fila = QHBoxLayout()
        cabecalho_fila.addWidget(titulo_queue, 1)

        self.btn_add_arquivos = QPushButton("+ Arquivos")
        self.btn_add_arquivos.setToolTip("Adicionar arquivos à fila (Ctrl+O)")
        self.btn_add_arquivos.clicked.connect(self.abrir_arquivos_dialogo)
        cabecalho_fila.addWidget(self.btn_add_arquivos)

        self.botao_limpar_fila = QPushButton("Limpar fila")
        self.botao_limpar_fila.clicked.connect(self.limpar_fila)
        cabecalho_fila.addWidget(self.botao_limpar_fila)
        layout_queue.addLayout(cabecalho_fila)

        self.queue_scroll = QScrollArea()
        self.queue_scroll.setWidgetResizable(True)
        self.queue_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.queue_content = QWidget()
        self.queue_layout = QVBoxLayout(self.queue_content)
        self.queue_layout.setContentsMargins(0, 0, 0, 0)
        self.queue_layout.setSpacing(6)
        self.queue_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.queue_scroll.setWidget(self.queue_content)
        layout_queue.addWidget(self.queue_scroll)

        # ==================================================
        # PLAYER BAR
        # ==================================================
        player = QFrame()
        player.setObjectName("playerBar")
        player.setFrameShape(QFrame.Shape.StyledPanel)

        layout_player = QHBoxLayout(player)
        layout_player.setContentsMargins(14, 10, 14, 10)
        layout_player.setSpacing(16)

        # ==================================================
        # LATERAL ESQUERDA: CAPA E INFORMAÇÕES
        # ==================================================
        self.capa = QLabel()
        self.capa.setFixedSize(58, 58)
        self.capa.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.capa.setText("CAPA")
        self.capa.setStyleSheet(
            "background: #2b2b2b; border: 1px solid #444444; border-radius: 6px; font-size: 11px;"
        )

        faixa_atual = QHBoxLayout()
        faixa_atual.setSpacing(12)
        faixa_atual.addWidget(self.capa)

        informacoes = QVBoxLayout()
        informacoes.setSpacing(2)

        self.titulo_musica = QLabel("Nenhuma música selecionada")
        self.artista_musica = QLabel("Artista")
        self.album_musica = QLabel("Álbum")

        self.titulo_musica.setObjectName("trackTitle")
        self.artista_musica.setObjectName("trackMetadata")
        self.album_musica.setObjectName("trackMetadata")

        informacoes.addWidget(self.titulo_musica)
        informacoes.addWidget(self.artista_musica)
        informacoes.addWidget(self.album_musica)

        faixa_atual.addLayout(informacoes)
        layout_player.addLayout(faixa_atual, 3)

        # ==================================================
        # CENTRO: CONTROLES PRINCIPAIS E PROGRESSO
        # ==================================================
        player_central = QVBoxLayout()
        player_central.setSpacing(4)

        controles = QHBoxLayout()
        controles.setSpacing(10)
        controles.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.botao_anterior = QPushButton()
        self.botao_play = QPushButton()
        self.botao_proximo = QPushButton()
        self.botao_repetir = QPushButton()

        self.botao_repetir.setCheckable(True)
        self.botao_repetir.setToolTip("Repetir a música atual (Ctrl+R)")

        self.botao_anterior.setObjectName("mediaButton")
        self.botao_proximo.setObjectName("mediaButton")
        self.botao_repetir.setObjectName("mediaButton")
        self.botao_play.setObjectName("mainPlayButton")

        self.botao_anterior.setToolTip("Faixa anterior / Recomeçar (Ctrl+Left)")
        self.botao_play.setToolTip("Reproduzir ou pausar (Espaço)")
        self.botao_proximo.setToolTip("Próxima faixa (Ctrl+Right)")

        controles.addWidget(self.botao_anterior)
        controles.addWidget(self.botao_play)
        controles.addWidget(self.botao_proximo)
        controles.addWidget(self.botao_repetir)

        self.botao_anterior.clicked.connect(self.faixa_anterior)
        self.botao_proximo.clicked.connect(self.faixa_proxima)
        self.botao_play.clicked.connect(self.alternar_reproducao)
        self.botao_repetir.clicked.connect(self._on_repeat_clicked)

        self.audio_engine.playback_started.connect(self.atualizar_botao_play)
        self.audio_engine.playback_paused.connect(self.atualizar_botao_play)
        self.audio_engine.playback_stopped.connect(self.atualizar_botao_play)

        player_central.addLayout(controles)

        # PROGRESSO COM CLIQUE DIRETO (ClickableSlider)
        progresso = QHBoxLayout()
        progresso.setSpacing(8)

        self.slider_progresso = ClickableSlider(Qt.Orientation.Horizontal)
        self.slider_progresso.sliderMoved.connect(self.audio_engine.set_position)
        self.slider_progresso.clicked_position.connect(self.audio_engine.set_position)

        self.tempo_atual = QLabel("00:00")
        self.tempo_total = QLabel("00:00")
        self.tempo_atual.setObjectName("trackMetadata")
        self.tempo_total.setObjectName("trackMetadata")

        progresso.addWidget(self.tempo_atual)
        progresso.addWidget(self.slider_progresso, 1)
        progresso.addWidget(self.tempo_total)

        player_central.addLayout(progresso)
        layout_player.addLayout(player_central, 5)

        self.audio_engine.position_changed.connect(self.atualizar_posicao)
        self.audio_engine.position_changed.connect(self.atualizar_karaoke_posicao)
        self.audio_engine.duration_changed.connect(self.atualizar_duracao)

        # ==================================================
        # LATERAL DIREITA: BOTÃO KARAOKE & VOLUME
        # ==================================================
        layout_direita = QHBoxLayout()
        layout_direita.setSpacing(8)
        layout_direita.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.botao_karaoke = QPushButton()
        self.botao_karaoke.setObjectName("mediaButton")
        self.botao_karaoke.setToolTip("Abrir tela de Karaoke (Ctrl+K)")
        self.botao_karaoke.clicked.connect(self.abrir_tela_karaoke)

        self.btn_vol_icon = QPushButton()
        self.btn_vol_icon.setObjectName("mediaButton")
        self.btn_vol_icon.setToolTip("Alternar mudo (Ctrl+M)")
        self.btn_vol_icon.clicked.connect(self.alternar_mudo)

        self.volume = ClickableSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setFixedWidth(90)
        self.volume.valueChanged.connect(self._on_volume_changed)
        self.volume.clicked_position.connect(self._on_volume_changed)

        layout_direita.addWidget(self.botao_karaoke)
        layout_direita.addWidget(self.btn_vol_icon)
        layout_direita.addWidget(self.volume)
        layout_player.addLayout(layout_direita, 2)

        # ==================================================
        # MONTAR INTERFACE
        # ==================================================
        layout_superior.addWidget(explorer, 1)
        layout_superior.addWidget(queue, 1)

        layout_principal.addLayout(layout_superior, 5)
        layout_principal.addWidget(player, 1)

    def carregar_estado_inicial(self):
        """Carrega pasta padrão, volume e modo de repetição das configurações."""
        # Volume
        remember_vol = self.config_manager.get("playback/remember_volume", True)
        if remember_vol:
            vol = self.config_manager.get("playback/last_volume", 80)
        else:
            vol = self.config_manager.get("playback/default_volume", 80)
        self.volume.setValue(vol)
        self.audio_engine.set_volume(vol)
        self.atualizar_icone_volume(vol)

        # Repetir
        repeat_def = self.config_manager.get("playback/repeat_enabled", False)
        self.botao_repetir.setChecked(repeat_def)

        # Diretório do explorador
        restaurar = self.config_manager.get("general/restore_last_folder", True)
        pasta = ""
        if restaurar:
            pasta = self.config_manager.get("general/last_opened_folder", "")
        if not pasta or not Path(pasta).is_dir():
            pasta = self.config_manager.get("general/default_music_dir", "")

        if pasta and Path(pasta).is_dir():
            self.definir_diretorio_explorador(pasta)

    def definir_diretorio_explorador(self, pasta: str):
        if Path(pasta).is_dir():
            idx = self.file_model.setRootPath(pasta)
            self.file_tree.setRootIndex(self.file_model.index(pasta))
            self.config_manager.set("general/last_opened_folder", pasta)

    def _on_repeat_clicked(self):
        self.config_manager.set("playback/repeat_enabled", self.botao_repetir.isChecked())

    def _on_volume_changed(self, valor):
        self.audio_engine.set_volume(valor)
        self.config_manager.set("playback/last_volume", valor)
        self.atualizar_icone_volume(valor)

    # ==================================================
    # DIÁLOGOS E MENUS
    # ==================================================

    def abrir_editor_karaoke(self):
        """Abre a janela do Editor de Karaoke e Cifras sincronizada com a faixa atual."""
        if self.karaoke_editor is None:
            self.karaoke_editor = KaraokeEditorWindow(self.audio_engine, self.config_manager)

        faixa_atual = self.queue_manager.current()
        if faixa_atual is not None:
            self.karaoke_editor.carregar_faixa(faixa_atual)

        self.karaoke_editor.show()
        self.karaoke_editor.raise_()
        self.karaoke_editor.activateWindow()

    def abrir_dialogo_configuracoes(self):
        dialog = SettingsDialog(self.config_manager, self)
        if dialog.exec():
            self.aplicar_configuracoes()

    def abrir_arquivos_dialogo(self):
        filtro_exts = " ".join(f"*{ext}" for ext in sorted(self.audio_extensions))
        filtro = f"Arquivos de Áudio ({filtro_exts});;Todos os Arquivos (*.*)"
        caminhos, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar Arquivos de Música",
            self.config_manager.get("general/last_opened_folder", "") or str(Path.home()),
            filtro,
        )
        if not caminhos:
            return

        primeira_adicionada = len(self.queue_manager.tracks) == 0
        for arq in caminhos:
            self._adicionar_caminho_fila(Path(arq))

        if primeira_adicionada and self.queue_manager.tracks:
            self.selecionar_faixa(0)
            if self.config_manager.get("playback/auto_play_on_add", False):
                self.audio_engine.play()

    def abrir_pasta_dialogo(self):
        pasta = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Pasta de Músicas",
            self.config_manager.get("general/last_opened_folder", "") or str(Path.home()),
        )
        if not pasta:
            return

        self.definir_diretorio_explorador(pasta)

    def alternar_tela_cheia(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def alternar_repetir(self):
        self.botao_repetir.setChecked(not self.botao_repetir.isChecked())
        self._on_repeat_clicked()

    def aumentar_volume(self):
        novo = min(100, self.volume.value() + 5)
        self.volume.setValue(novo)

    def diminuir_volume(self):
        novo = max(0, self.volume.value() - 5)
        self.volume.setValue(novo)

    def alternar_mudo(self):
        if self.volume.value() > 0:
            self._volume_anterior_mudo = self.volume.value()
            self.volume.setValue(0)
        else:
            restaurar = self._volume_anterior_mudo if self._volume_anterior_mudo else 50
            self.volume.setValue(restaurar)

    def mostrar_atalhos(self):
        texto = """
        <h3>Atalhos do Teclado</h3>
        <table>
            <tr><td><b>Espaço</b></td><td>Reproduzir / Pausar</td></tr>
            <tr><td><b>Ctrl + Right</b></td><td>Próxima faixa</td></tr>
            <tr><td><b>Ctrl + Left</b></td><td>Faixa anterior / Recomeçar</td></tr>
            <tr><td><b>Ctrl + Up / Down</b></td><td>Aumentar / Diminuir volume</td></tr>
            <tr><td><b>Ctrl + M</b></td><td>Alternar mudo</td></tr>
            <tr><td><b>Ctrl + R</b></td><td>Alternar repetição de faixa</td></tr>
            <tr><td><b>Ctrl + K</b></td><td>Abrir tela de Karaoke</td></tr>
            <tr><td><b>Ctrl + E</b></td><td>Abrir Editor de Karaoke e Cifras</td></tr>
            <tr><td><b>Ctrl + O</b></td><td>Abrir arquivo(s) de áudio</td></tr>
            <tr><td><b>Ctrl + Shift + O</b></td><td>Abrir pasta de músicas</td></tr>
            <tr><td><b>Ctrl + L</b></td><td>Limpar fila de reprodução</td></tr>
            <tr><td><b>Ctrl + ,</b></td><td>Abrir Configurações / Preferências</td></tr>
            <tr><td><b>F11</b></td><td>Alternar tela cheia</td></tr>
            <tr><td><b>Ctrl + Q</b></td><td>Sair do aplicativo</td></tr>
        </table>
        """
        QMessageBox.information(self, "Atalhos do Teclado", texto)

    def mostrar_sobre(self):
        texto = """
        <h3>Music Player</h3>
        <p>Um reprodutor de áudio moderno e elegante desenvolvido com Python e PySide6 (Qt).</p>
        <p><b>Recursos:</b></p>
        <ul>
            <li>Suporte a múltiplos formatos (MP3, FLAC, M4A, OGG, WAV, etc.)</li>
            <li>Editor completo de Karaoke com frases limpas e suporte a cifras</li>
            <li>Pasta centralizada para salvar e gerenciar letras sem poluir pastas de álbuns</li>
            <li>Leitor avançado de tags e capas embutidas</li>
            <li>Fila dinâmica com duplo clique para reproduzir e recurso 'Tocar a Seguir'</li>
        </ul>
        """
        QMessageBox.about(self, "Sobre o Music Player", texto)

    # ==================================================
    # REPRODUÇÃO & KARAOKE
    # ==================================================

    def abrir_tela_karaoke(self):
        if self.karaoke_window is None:
            self.karaoke_window = KaraokeWindow(self.audio_engine, self.config_manager)
            self.karaoke_window.editar_solicitado.connect(self.abrir_editor_karaoke)
            self.karaoke_window.faixa_anterior_solicitada.connect(self.faixa_anterior)
            self.karaoke_window.faixa_proxima_solicitada.connect(self.faixa_proxima)

        faixa_atual = self.queue_manager.current()
        if faixa_atual is not None:
            self.karaoke_window.atualizar_faixa(faixa_atual)
            self.karaoke_window.atualizar_posicao(self.audio_engine.position())

        self.karaoke_window.show()
        self.karaoke_window.raise_()
        self.karaoke_window.activateWindow()

    def atualizar_karaoke_posicao(self, position):
        """Atualiza a sincronização do karaoke em tempo real conforme a posição da música."""
        if self.karaoke_window is not None and self.karaoke_window.isVisible():
            self.karaoke_window.atualizar_posicao(position)

    def selecionar_faixa(self, index):
        track = self.queue_manager.set_current(index)
        if track is None:
            return

        # Uma nova música começa um novo ciclo do botão "voltar".
        self._anterior_ja_reiniciou = False

        self.audio_engine.load(track.path)
        self.atualizar_fila()
        self.atualizar_player(track)

        if self.karaoke_editor is not None and self.karaoke_editor.isVisible():
            self.karaoke_editor.carregar_faixa(track)

    def selecionar_e_reproduzir_faixa(self, index):
        """Seleciona e inicia a reprodução imediatamente (disparado pelo duplo clique na fila)."""
        self.selecionar_faixa(index)
        self.audio_engine.play()

    def definir_tocar_a_seguir(self, index: int):
        """Move a faixa escolhida para a posição seguinte à música atual e destaca em laranja."""
        if self.queue_manager.set_play_next(index):
            self.atualizar_fila()

    def _adicionar_caminho_fila(self, caminho: Path):
        if not caminho.is_file() or caminho.suffix.lower() not in self.audio_extensions:
            return

        metadados = ler_metadados(caminho)
        track = Track(
            path=caminho,
            title=metadados["title"],
            artist=metadados["artist"],
            album=metadados["album"],
            cover=metadados["cover"],
            format=metadados["format"],
            duration=metadados["duration"],
        )
        self.queue_manager.add(track)
        self.atualizar_fila()

    def arquivo_selecionado(self, index):
        caminho = Path(self.file_model.filePath(index))

        if not caminho.is_file():
            return

        if caminho.suffix.lower() not in self.audio_extensions:
            return

        fila_estava_vazia = not self.queue_manager.tracks
        self._adicionar_caminho_fila(caminho)

        if fila_estava_vazia:
            self.selecionar_faixa(0)
            if self.config_manager.get("playback/auto_play_on_add", False):
                self.audio_engine.play()

    def atualizar_player(self, track):
        if track is None:
            return

        if self.karaoke_window is not None:
            self.karaoke_window.atualizar_faixa(track)

        self.titulo_musica.setText(track.title)
        self.artista_musica.setText(track.artist if track.artist else "Artista desconhecido")
        self.album_musica.setText(track.album if track.album else "Álbum desconhecido")

        if track.cover:
            pixmap = QPixmap()
            pixmap.loadFromData(track.cover)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    self.capa.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.capa.setPixmap(pixmap)
                return

        self.capa.clear()
        self.capa.setText("CAPA")

    def atualizar_fila(self):
        """Atualiza a lista visual da fila de reprodução."""
        while self.queue_layout.count():
            item = self.queue_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for index, track in enumerate(self.queue_manager.tracks):
            is_current = (index == self.queue_manager.current_index)
            is_next = (index == self.queue_manager.current_index + 1)

            item_widget = QueueItemWidget(
                main_window=self,
                index=index,
                track=track,
                is_current=is_current,
                is_next=is_next,
            )
            self.queue_layout.addWidget(item_widget)

        self.botao_limpar_fila.setEnabled(bool(self.queue_manager.tracks))

    def mover_faixa(self, index, destino):
        if self.queue_manager.move(index, destino):
            self.atualizar_fila()

    def remover_faixa(self, index):
        faixa_atual = self.queue_manager.current_index
        estava_reproduzindo = self.audio_engine.is_playing()
        removeu_atual = index == faixa_atual

        if self.queue_manager.remove(index) is None:
            return

        if removeu_atual:
            self.audio_engine.stop()
            nova_atual = self.queue_manager.current()
            if nova_atual is None:
                self.limpar_player()
            else:
                self.audio_engine.load(nova_atual.path)
                self.atualizar_player(nova_atual)
                if estava_reproduzindo:
                    self.audio_engine.play()

        self.atualizar_fila()

    def remover_faixa_atual(self):
        if self.queue_manager.current_index >= 0:
            self.remover_faixa(self.queue_manager.current_index)

    def limpar_fila(self):
        self.audio_engine.stop()
        self.queue_manager.clear()
        self.limpar_player()
        self.atualizar_fila()

    def limpar_player(self):
        if self.karaoke_window is not None:
            self.karaoke_window.limpar()

        if self.karaoke_editor is not None:
            self.karaoke_editor.carregar_faixa(None)

        self.titulo_musica.setText("Nenhuma música selecionada")
        self.artista_musica.setText("Artista")
        self.album_musica.setText("Álbum")
        self.capa.clear()
        self.capa.setText("CAPA")
        self.slider_progresso.setRange(0, 0)
        self.tempo_atual.setText("00:00")
        self.tempo_total.setText("00:00")

    def faixa_anterior(self):
        """Primeiro clique reinicia a faixa atual; o segundo volta para a anterior."""
        if not self._anterior_ja_reiniciou:
            self.audio_engine.set_position(0)
            self._anterior_ja_reiniciou = True
            return

        track = self.queue_manager.previous()

        if track is None:
            self.audio_engine.set_position(0)
            self._anterior_ja_reiniciou = False
            return

        self._anterior_ja_reiniciou = False

        self.audio_engine.load(track.path)
        self.atualizar_fila()
        self.atualizar_player(track)
        self.audio_engine.play()

    def faixa_proxima(self):
        self._anterior_ja_reiniciou = False

        track = self.queue_manager.next()
        if track is None:
            return

        self.audio_engine.load(track.path)
        self.atualizar_fila()
        self.atualizar_player(track)
        self.audio_engine.play()

    def alternar_reproducao(self):
        track = self.queue_manager.current()
        if track is None:
            return

        if self.audio_engine.is_playing():
            self.audio_engine.pause()
        else:
            self.audio_engine.play()

    def atualizar_posicao(self, position):
        self.slider_progresso.setValue(position)
        self.atualizar_tempo()

    def atualizar_duracao(self, duration):
        self.slider_progresso.setRange(0, duration)
        self.atualizar_tempo()

    def atualizar_tempo(self):
        position = self.audio_engine.position()
        duration = self.audio_engine.duration()
        self.tempo_atual.setText(self.formatar_tempo(position))
        self.tempo_total.setText(self.formatar_tempo(duration))

    def formatar_tempo(self, milliseconds):
        segundos = milliseconds // 1000
        minutos = segundos // 60
        segundos = segundos % 60
        return f"{minutos:02d}:{segundos:02d}"

    def formatar_duracao(self, segundos):
        segundos = int(segundos)
        minutos = segundos // 60
        segundos = segundos % 60
        return f"{minutos:02d}:{segundos:02d}"

    def faixa_terminou(self):
        if self.botao_repetir.isChecked():
            faixa_atual = self.queue_manager.current()
            if faixa_atual is not None:
                self.audio_engine.load(faixa_atual.path)
                self.audio_engine.play()
            return

        proxima = self.queue_manager.next()
        if proxima is None:
            return

        self.atualizar_fila()
        self.atualizar_player(proxima)
        self.audio_engine.load(proxima.path)
        self.audio_engine.play()

    def closeEvent(self, event):
        """Salva configurações e encerra recursos ao fechar o player."""
        if self.config_manager.get("playback/remember_volume", True):
            self.config_manager.set("playback/last_volume", self.volume.value())

        if self.karaoke_window is not None:
            self.karaoke_window.close()

        if self.karaoke_editor is not None:
            self.karaoke_editor.close()

        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
