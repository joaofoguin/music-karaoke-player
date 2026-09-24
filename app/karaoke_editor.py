from pathlib import Path
import re

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QKeySequence, QShortcut, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.lyrics import (
    CHORD_TOKEN_PATTERN,
    LyricLine,
    convert_chord_sheet_to_lyric_lines,
    extract_chords_and_lyrics,
    format_timestamp_ms,
    is_chord_line,
    load_lrc,
    parse_timestamp_ms,
    save_lrc,
)
from core.lyrics_storage import get_save_lyrics_path, resolve_lyrics_path
from core.icons import get_stateful_icon, get_svg_icon
from core.clickable_slider import ClickableSlider
from core.theme_manager import ThemeManager
from karaoke_window import KaraokeWindow


class KaraokeEditorWindow(QMainWindow):
    """Janela profissional para importação de cifras completas, edição de versos limpos e sincronização ao vivo clicando nas linhas."""

    def __init__(self, audio_engine, config_manager=None, parent=None):
        super().__init__(parent)
        self.audio_engine = audio_engine
        self.config_manager = config_manager
        self.current_track = None
        self.target_lrc_path = None
        self._ignorar_clique_interno = False
        self.editor_model = "stagebox"

        self.setWindowTitle("Editor de Karaoke e Cifras")
        self.resize(1120, 740)
        self.setMinimumSize(860, 540)

        self._criar_interface()
        self._criar_atalhos()
        self._aplicar_estilo()
        self._carregar_modelo_editor()

        if self.config_manager is not None:
            self.config_manager.settings_changed.connect(self._atualizar_tema)

        # Conexões com o motor de áudio
        self.audio_engine.position_changed.connect(self._on_audio_position_changed)
        self.audio_engine.playback_started.connect(self._atualizar_botao_play)
        self.audio_engine.playback_paused.connect(self._atualizar_botao_play)
        self.audio_engine.playback_stopped.connect(self._atualizar_botao_play)

    def _atualizar_tema(self):
        """Atualiza tema e modelo de cifras enquanto o editor permanece aberto."""
        self._carregar_modelo_editor()
        self._aplicar_estilo()

    def _aplicar_estilo(self):
        tema = self.config_manager.get("appearance/theme", "dark") if self.config_manager else "dark"
        ThemeManager.aplicar_barra_titulo(self, tema)
        if tema == "midnight":
            self.setStyleSheet("""
                QMainWindow { background: #0b0d11; color: #f3f4f6; }
                QFrame#topBar { background: #131720; border: 1px solid #1f2937; border-radius: 8px; }
                QFrame#bottomBar { background: #131720; border: 1px solid #1f2937; border-radius: 8px; }
                QTableWidget { background: #0b0d11; color: #e5e7eb; gridline-color: #1f2937; border: 1px solid #1f2937; selection-background-color: #1e3a8a; }
                QHeaderView::section { background: #131720; color: #9ca3af; border: 1px solid #1f2937; padding: 8px; font-weight: bold; }
                QPushButton { background: #1f2937; color: #f3f4f6; border: 1px solid #374151; border-radius: 4px; padding: 6px 12px; font-weight: 500; }
                QPushButton:hover { background: #374151; }
                QPushButton#btnSync { background: #2563eb; color: #ffffff; font-weight: bold; font-size: 13px; border: 0; }
                QPushButton#btnSync:hover { background: #3b82f6; }
                QPushButton#btnRowAction { background: transparent; border: none; padding: 0; border-radius: 4px; }
                QPushButton#btnRowAction:hover { background: #1e3a8a; border: none; }\n                QPushButton#btnRowAction { background: transparent; border: none; padding: 0; border-radius: 0; }\n                QPushButton#btnRowAction:hover { background: transparent; border: none; }\n                QPushButton#btnRowAction { background: transparent; border: none; padding: 0; border-radius: 0; }\n                QPushButton#btnRowAction:hover { background: transparent; border: none; }\n                QPushButton#btnTopAction { background: #047857; color: #ffffff; font-weight: bold; font-size: 13px; border: 0; padding: 6px 14px; }
                QPushButton#btnTopAction:hover { background: #059669; }
                QPushButton#btnPlay { background: #2563eb; border-radius: 18px; min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px; }
                QSlider::groove:horizontal { height: 6px; background: #1f2937; border-radius: 3px; }
                QSlider::handle:horizontal { width: 14px; margin: -4px 0; background: #60a5fa; border-radius: 7px; }
            """)
        elif tema == "light":
            self.setStyleSheet("""
                QMainWindow { background: #f3f4f6; color: #111827; }
                QFrame#topBar { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; }
                QFrame#bottomBar { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; }
                QTableWidget { background: #ffffff; color: #111827; gridline-color: #e5e7eb; border: 1px solid #d1d5db; selection-background-color: #bfdbfe; }
                QHeaderView::section { background: #f3f4f6; color: #4b5563; border: 1px solid #e5e7eb; padding: 8px; font-weight: bold; }
                QPushButton { background: #ffffff; color: #1f2937; border: 1px solid #d1d5db; border-radius: 4px; padding: 6px 12px; font-weight: 500; }
                QPushButton:hover { background: #e5e7eb; }
                QPushButton#btnSync { background: #2563eb; color: #ffffff; font-weight: bold; font-size: 13px; border: 0; }
                QPushButton#btnSync:hover { background: #1d4ed8; }
                QPushButton#btnTopAction { background: #059669; color: #ffffff; font-weight: bold; font-size: 13px; border: 0; padding: 6px 14px; }
                QPushButton#btnTopAction:hover { background: #047857; }
                QPushButton#btnPlay { background: #2563eb; border-radius: 18px; min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px; }
                QSlider::groove:horizontal { height: 6px; background: #e5e7eb; border-radius: 3px; }
                QSlider::handle:horizontal { width: 14px; margin: -4px 0; background: #2563eb; border-radius: 7px; }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow { background: #171717; color: #f4f4f4; }
                QFrame#topBar { background: #242424; border: 1px solid #3f3f3f; border-radius: 8px; }
                QFrame#bottomBar { background: #242424; border: 1px solid #3f3f3f; border-radius: 8px; }
                QTableWidget { background: #1d1d1d; color: #d8d8d8; gridline-color: #333333; border: 1px solid #393939; selection-background-color: #1e3a8a; }
                QHeaderView::section { background: #2c2c2c; color: #bdbdbd; border: 1px solid #3c3c3c; padding: 8px; font-weight: bold; }
                QPushButton { background: #363636; color: #f2f2f2; border: 1px solid #4d4d4d; border-radius: 4px; padding: 6px 12px; font-weight: 500; }
                QPushButton:hover { background: #4a4a4a; }
                QPushButton#btnSync { background: #2563eb; color: #ffffff; font-weight: bold; font-size: 13px; border: 0; }
                QPushButton#btnSync:hover { background: #3b82f6; }
                QPushButton#btnTopAction { background: #059669; color: #ffffff; font-weight: bold; font-size: 13px; border: 0; padding: 6px 14px; }
                QPushButton#btnTopAction:hover { background: #10b981; }
                QPushButton#btnPlay { background: #ffffff; border-radius: 18px; min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px; }
                QSlider::groove:horizontal { height: 6px; background: #4a4a4a; border-radius: 3px; }
                QSlider::handle:horizontal { width: 14px; margin: -4px 0; background: #e0e0e0; border-radius: 7px; }
            """)
        cor_titulo = "#111827" if tema == "light" else "#f3f4f6"
        self.lbl_faixa.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {cor_titulo};"
        )
        cor_tempo = "#111827" if tema == "light" else "#e5e7eb"
        self.lbl_tempo.setStyleSheet(
            f'font-size: 13px; font-family: "Poppins", monospace; font-weight: 600; color: {cor_tempo};'
        )
        cor_destino = "#6b7280" if tema == "light" else "#9ca3af"
        self.lbl_destino.setStyleSheet(f"color: {cor_destino}; font-size: 12px;")
        self.chk_click_to_sync.setStyleSheet(
            f"color: {'#2563eb' if tema == 'light' else '#60a5fa'}; font-weight: bold;"
        )
        self._atualizar_icones()

    def _atualizar_icones(self):
        tema = self.config_manager.get("appearance/theme", "dark") if self.config_manager else "dark"
        cor = "#374151" if tema == "light" else "#e5e7eb"
        self.btn_voltar5.setIcon(get_svg_icon("rewind_5", color=cor))
        self.btn_avancar5.setIcon(get_svg_icon("forward_5", color=cor))
        self.btn_play.setIcon(get_svg_icon("pause" if self.audio_engine.is_playing() else "play", color="#ffffff" if tema != "dark" else "#171717"))
        self.btn_play.setIconSize(QSize(18, 18))
        for row in range(self.tabela.rowCount()):
            widget = self.tabela.cellWidget(row, 3)
            if widget is None:
                continue
            for button in widget.findChildren(QPushButton):
                icon_name = "timer" if button.toolTip() == "Marcar tempo" else "play"
                button.setIcon(get_stateful_icon(icon_name, normal_color=cor, hover_color="#2563eb", active_color="#2563eb"))
        self.btn_salvar.setIcon(get_svg_icon("save", color=cor))
        icones = {
            "Adicionar verso": "plus",
            "Remover verso": "minus",
            "Mover verso para cima": "arrow_up",
            "Mover verso para baixo": "arrow_down",
            "Ajustar offset geral": "settings",
        }
        for button in self.findChildren(QPushButton):
            nome_icone = icones.get(button.toolTip())
            if nome_icone:
                button.setIcon(get_svg_icon(nome_icone, color=cor))

    def _criar_interface(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout_principal = QVBoxLayout(central)
        layout_principal.setContentsMargins(16, 16, 16, 16)
        layout_principal.setSpacing(12)

        # ----------------------------------------------------
        # PAINEL SUPERIOR: CONTROLES DE ÁUDIO E COLAR MÚSICA
        # ----------------------------------------------------
        painel_topo = QFrame()
        painel_topo.setObjectName("topBar")
        layout_topo = QVBoxLayout(painel_topo)
        layout_topo.setContentsMargins(14, 12, 14, 12)
        layout_topo.setSpacing(10)

        linha1 = QHBoxLayout()
        self.lbl_faixa = QLabel("Nenhuma música carregada")
        self.lbl_faixa.setStyleSheet(
            "font-size: 16px; font-weight: 600; color: #111827;"
        )
        linha1.addWidget(self.lbl_faixa, 1)

        linha1.addStretch()

        self.btn_preview = QPushButton("Preview")
        self.btn_preview.setObjectName("btnTopAction")
        self.btn_preview.setIcon(get_svg_icon("play", color="#ffffff"))
        self.btn_preview.setIconSize(QSize(18, 18))
        self.btn_preview.setFixedHeight(36)
        self.btn_preview.setToolTip("Pré-visualizar a letra no Karaoke")
        self.btn_preview.clicked.connect(self._abrir_preview_karaoke)
        linha1.addWidget(self.btn_preview)

        self.btn_colar_musica = QPushButton("Importar")
        self.btn_colar_musica.setObjectName("btnTopAction")
        self.btn_colar_musica.setIcon(get_stateful_icon("paste", normal_color="#ffffff", hover_color="#ffffff"))
        self.btn_colar_musica.setIconSize(QSize(18, 18))
        self.btn_colar_musica.setFixedHeight(36)
        self.btn_colar_musica.setToolTip("Importar letra e cifras")
        self.btn_colar_musica.clicked.connect(self._abrir_dialogo_colar_cifra_completa)
        linha1.addWidget(self.btn_colar_musica)

        self.btn_sync = QPushButton("Marcar")
        self.btn_sync.setIcon(get_stateful_icon("timer", normal_color="#ffffff", hover_color="#ffffff"))
        self.btn_sync.setIconSize(QSize(18, 18))
        self.btn_sync.setObjectName("btnSync")
        self.btn_sync.setFixedHeight(36)
        self.btn_sync.setMinimumWidth(104)
        self.btn_sync.setToolTip("Marcar o verso atual no editor (F5)")
        self.btn_sync.clicked.connect(self._marcar_verso_atual)
        linha1.addWidget(self.btn_sync)

        layout_topo.addLayout(linha1)

        # Controles de áudio com ClickableSlider
        linha2 = QHBoxLayout()
        linha2.setSpacing(10)

        self.btn_voltar5 = QPushButton()
        self.btn_voltar5.setIcon(get_svg_icon("rewind_5", color="#e5e7eb"))
        self.btn_voltar5.setIconSize(QSize(18, 18))
        self.btn_voltar5.setFixedSize(38, 36)
        self.btn_voltar5.setToolTip("Voltar 5 segundos")
        self.btn_voltar5.clicked.connect(lambda: self._avancar_tempo(-5000))
        linha2.addWidget(self.btn_voltar5)

        self.btn_play = QPushButton()
        self.btn_play.setObjectName("btnPlay")
        self.btn_play.clicked.connect(self._alternar_play_audio)
        self._atualizar_botao_play()
        linha2.addWidget(self.btn_play)

        self.btn_avancar5 = QPushButton()
        self.btn_avancar5.setIcon(get_svg_icon("forward_5", color="#e5e7eb"))
        self.btn_avancar5.setIconSize(QSize(18, 18))
        self.btn_avancar5.setFixedSize(38, 36)
        self.btn_avancar5.setToolTip("Avançar 5 segundos")
        self.btn_avancar5.clicked.connect(lambda: self._avancar_tempo(5000))
        linha2.addWidget(self.btn_avancar5)

        self.lbl_tempo = QLabel("00:00.00 / 00:00.00")
        cor_tempo = "#111827" if (self.config_manager and self.config_manager.get("appearance/theme", "dark") == "light") else "#e5e7eb"
        self.lbl_tempo.setStyleSheet(
            f"font-size: 13px; font-family: monospace; font-weight: bold; color: {cor_tempo};"
        )
        # Largura mínima fixa para que a barra de progresso não se mova ao atualizar o tempo
        self.lbl_tempo.setFixedWidth(148)
        linha2.addWidget(self.lbl_tempo)

        # Barra de reprodução com clique direto!
        self.slider_posicao = ClickableSlider(Qt.Orientation.Horizontal)
        self.slider_posicao.sliderMoved.connect(self.audio_engine.set_position)
        self.slider_posicao.clicked_position.connect(self.audio_engine.set_position)
        linha2.addWidget(self.slider_posicao, 1)

        layout_topo.addLayout(linha2)

        # Dica / Opção de clique na linha
        linha_dica = QHBoxLayout()
        self.chk_click_to_sync = QCheckBox("Modo de Marcação Rápida: clicar em qualquer linha grava o tempo atual do áudio nela")
        self.chk_click_to_sync.setChecked(False)
        self.chk_click_to_sync.setStyleSheet("color: #60a5fa; font-weight: bold;")
        linha_dica.addWidget(self.chk_click_to_sync)
        linha_dica.addStretch()

        layout_topo.addLayout(linha_dica)
        layout_principal.addWidget(painel_topo)

        # ----------------------------------------------------
        # ÁREA CENTRAL: TABELA DE VERSOS LIMPOS E CIFRAS SEPARADAS
        # ----------------------------------------------------
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels([
            "Tempo (LRC)",
            "Cifras / Acordes",
            "Letra do Verso (Frase Limpa)",
            "Ações",
        ])
        self.tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabela.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.tabela.setAlternatingRowColors(True)

        self.editor_texto = QPlainTextEdit()
        self.editor_texto.setObjectName("winampEditor")
        self.editor_texto.setFont(QFont("Consolas", 11))
        self.editor_texto.setPlaceholderText("      C             G\n[00:12]Quando eu te encontrar\n\n      Am            F\n[00:18]E então...")
        self.editor_texto.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.editor_texto.setTabStopDistance(32)
        self.editor_texto.setToolTip(
            "Posicione o cursor no verso e pressione F5 ou clique em Marcar para registrar o tempo atual."
        )
        self.editor_texto.textChanged.connect(self._on_editor_text_changed)
        self.editor_texto.cursorPositionChanged.connect(self._atualizar_linha_winamp_selecionada)

        self.tabela.cellClicked.connect(self._on_cell_clicked)
        self.tabela.itemChanged.connect(self._on_table_item_changed)

        layout_principal.addWidget(self.tabela, 1)
        layout_principal.addWidget(self.editor_texto, 1)

        self.lbl_modelo_preview = QLabel()
        self.lbl_modelo_preview.setObjectName("lyricsModelPreview")
        self.lbl_modelo_preview.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_modelo_preview.setMinimumHeight(72)
        self.lbl_modelo_preview.setWordWrap(False)
        layout_principal.addWidget(self.lbl_modelo_preview)
        self.tabela.currentCellChanged.connect(
            lambda row, _col, _prev_row, _prev_col: self._atualizar_preview_modelo(row)
        )

        # ----------------------------------------------------
        # BARRA DE FERRAMENTAS INFERIORES DE LINHAS
        # ----------------------------------------------------
        painel_linhas = QHBoxLayout()
        painel_linhas.setSpacing(8)

        btn_add_linha = QPushButton()
        btn_add_linha.setIcon(get_svg_icon("plus"))
        btn_add_linha.setIconSize(QSize(18, 18))
        btn_add_linha.setFixedSize(38, 34)
        btn_add_linha.setToolTip("Adicionar verso")
        btn_add_linha.clicked.connect(self._adicionar_linha)
        painel_linhas.addWidget(btn_add_linha)

        btn_remover_linha = QPushButton()
        btn_remover_linha.setIcon(get_svg_icon("minus"))
        btn_remover_linha.setIconSize(QSize(18, 18))
        btn_remover_linha.setFixedSize(38, 34)
        btn_remover_linha.setToolTip("Remover verso")
        btn_remover_linha.clicked.connect(self._remover_linha)
        painel_linhas.addWidget(btn_remover_linha)

        btn_subir = QPushButton()
        btn_subir.setIcon(get_svg_icon("arrow_up"))
        btn_subir.setIconSize(QSize(18, 18))
        btn_subir.setFixedSize(38, 34)
        btn_subir.setToolTip("Mover verso para cima")
        btn_subir.clicked.connect(lambda: self._mover_linha(-1))
        painel_linhas.addWidget(btn_subir)

        btn_descer = QPushButton()
        btn_descer.setIcon(get_svg_icon("arrow_down"))
        btn_descer.setIconSize(QSize(18, 18))
        btn_descer.setFixedSize(38, 34)
        btn_descer.setToolTip("Mover verso para baixo")
        btn_descer.clicked.connect(lambda: self._mover_linha(1))
        painel_linhas.addWidget(btn_descer)

        painel_linhas.addStretch()

        btn_ajustar_offset = QPushButton()
        btn_ajustar_offset.setIcon(get_svg_icon("settings"))
        btn_ajustar_offset.setIconSize(QSize(18, 18))
        btn_ajustar_offset.setFixedSize(38, 34)
        btn_ajustar_offset.setToolTip("Ajustar offset geral")
        btn_ajustar_offset.clicked.connect(self._ajustar_offset_geral)
        painel_linhas.addWidget(btn_ajustar_offset)

        layout_principal.addLayout(painel_linhas)

        # ----------------------------------------------------
        # PAINEL INFERIOR: DESTINO DO ARQUIVO E SALVAR
        # ----------------------------------------------------
        painel_rodape = QFrame()
        painel_rodape.setObjectName("bottomBar")
        layout_rodape = QHBoxLayout(painel_rodape)
        layout_rodape.setContentsMargins(14, 10, 14, 10)
        layout_rodape.setSpacing(12)

        self.lbl_destino = QLabel("Destino: Pasta Central de Karaoke")
        self.lbl_destino.setStyleSheet("color: #9ca3af; font-size: 12px;")
        layout_rodape.addWidget(self.lbl_destino, 1)

        self.btn_salvar = QPushButton()
        self.btn_salvar.setIcon(get_svg_icon("save", color="#e5e7eb"))
        self.btn_salvar.setIconSize(QSize(20, 20))
        self.btn_salvar.setFixedSize(42, 36)
        self.btn_salvar.setToolTip("Salvar letra e cifras (Ctrl+S)")
        self.btn_salvar.setStyleSheet("font-weight: bold;")
        self.btn_salvar.clicked.connect(self.salvar_letra)
        layout_rodape.addWidget(self.btn_salvar)

        layout_principal.addWidget(painel_rodape)

    def _criar_atalhos(self):
        self.shortcut_play_pause = QShortcut(QKeySequence("Space"), self)
        self.shortcut_play_pause.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_play_pause.activated.connect(self._alternar_play_audio)

        self.shortcut_marcar = QShortcut(QKeySequence("F5"), self)
        self.shortcut_marcar.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_marcar.activated.connect(self._marcar_verso_atual)

        self.shortcut_salvar = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_salvar.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_salvar.activated.connect(self.salvar_letra)

        self.shortcut_adicionar = QShortcut(QKeySequence("Insert"), self)
        self.shortcut_adicionar.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_adicionar.activated.connect(self._adicionar_linha)

        self.shortcut_remover = QShortcut(QKeySequence("Delete"), self)
        self.shortcut_remover.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.shortcut_remover.activated.connect(self._remover_linhas_selecionadas)

    def carregar_faixa(self, track):
        """Carrega a música atual e busca a letra existente na pasta central ou local."""
        self.current_track = track
        if track is None:
            self.lbl_faixa.setText("Nenhuma música carregada")
            self.tabela.setRowCount(0)
            return

        artista = track.artist or "Artista Desconhecido"
        self.lbl_faixa.setText(f"{track.title} — {artista}")
        self._carregar_modelo_editor()

        lrc_existente = resolve_lyrics_path(track, self.config_manager)
        self.target_lrc_path = get_save_lyrics_path(track, self.config_manager)
        self.lbl_destino.setText(f"Salvo em: {self.target_lrc_path}")

        # Usa o caminho de salvamento como fallback para restaurar um LRC existente.
        if not lrc_existente and self.target_lrc_path.is_file():
            lrc_existente = self.target_lrc_path

        linhas = []
        if lrc_existente and lrc_existente.is_file():
            linhas = load_lrc(lrc_existente)

        self._popular_tabela(linhas)
        if self.editor_model == "winamp":
            self.editor_texto.blockSignals(True)
            self.editor_texto.setPlainText(self._linhas_para_texto_winamp(linhas))
            self.editor_texto.blockSignals(False)

    def _linhas_para_texto_winamp(self, linhas):
        blocos = []
        for line in linhas:
            chord_line = self._formatar_cifras_editor(line.chords or "")
            timestamp = format_timestamp_ms(line.timestamp_ms).split(".")[0]
            blocos.append(f"{chord_line}\n[{timestamp}]{line.clean_lyrics}")
        return "\n\n".join(blocos)

    def _linhas_do_texto_winamp(self):
        linhas = []
        pending_chords = ""
        for raw in self.editor_texto.toPlainText().splitlines():
            linha = raw.rstrip()
            if not linha.strip():
                continue
            if not linha.lstrip().startswith("["):
                pending_chords = self._normalizar_cifras_editor(linha)
                continue
            match = re.match(r"^\[(\d{1,2}:\d{2}(?:\.\d{1,3})?)\](.*)$", linha)
            if not match:
                continue
            linhas.append(LyricLine(
                timestamp_ms=parse_timestamp_ms(match.group(1)),
                text=match.group(2),
                chords=pending_chords,
            ))
            pending_chords = ""
        return linhas

    def _atualizar_linha_winamp_selecionada(self):
        """Mantém a seleção lógica do verso sob o cursor para a marcação rápida."""
        if self.editor_model != "winamp":
            return
        block = self.editor_texto.textCursor().block()
        if block.isValid() and is_chord_line(block.text()):
            block = block.next()
            while block.isValid() and not block.text().strip():
                block = block.next()
        if block.isValid():
            self.editor_texto.ensureCursorVisible()

    def _bloco_winamp_para_marcacao(self):
        """Resolve o verso correspondente ao cursor, ignorando linhas de cifras."""
        if self.editor_model != "winamp":
            return None

        block = self.editor_texto.textCursor().block()
        if not block.isValid():
            return None

        if is_chord_line(block.text()):
            candidate = block.next()
            while candidate.isValid() and not candidate.text().strip():
                candidate = candidate.next()
            if candidate.isValid():
                block = candidate

        if not block.text().strip():
            candidate = block.next()
            while candidate.isValid():
                if candidate.text().strip() and not is_chord_line(candidate.text()):
                    block = candidate
                    break
                candidate = candidate.next()

        return block if block.isValid() and block.text().strip() else None

    def _gravar_tempo_winamp(self):
        """Marca o verso sob o cursor com a posição atual do áudio."""
        block = self._bloco_winamp_para_marcacao()
        if block is None:
            return False

        posicao_ms = max(0, int(self.audio_engine.position()))
        timestamp = format_timestamp_ms(posicao_ms).split(".")[0]
        texto = block.text()
        texto_sem_tempo = re.sub(r"^[d{1,2}:d{2}(?:.d{1,3})?]", "", texto)
        novo_texto = f"[{timestamp}]{texto_sem_tempo}"

        cursor = QTextCursor(block)
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        cursor.insertText(novo_texto)
        self.editor_texto.setTextCursor(cursor)
        self.editor_texto.ensureCursorVisible()
        return True

    def _marcar_verso_atual(self):
        """Marca o verso atual no modelo ativo usando o relógio ou F5."""
        if self.editor_model == "winamp":
            if self._gravar_tempo_winamp():
                return
            return
        self._gravar_tempo_linha_selecionada()

    def _on_editor_text_changed(self):
        if self.editor_model == "winamp":
            self.lbl_modelo_preview.setText(
                '<span style="color:#9ca3af;">Editor Winamp — texto tradicional. '
                'As cifras ficam acima da letra e respeitam os espaços digitados.</span>'
            )

    def _abrir_preview_karaoke(self):
        linhas = self._linhas_do_texto_winamp() if self.editor_model == "winamp" else [
            LyricLine(
                timestamp_ms=int(self.tabela.item(r, 0).data(Qt.ItemDataRole.UserRole) or 0),
                text=self.tabela.item(r, 2).text(),
                chords=self.tabela.item(r, 1).data(Qt.ItemDataRole.UserRole) or "",
            )
            for r in range(self.tabela.rowCount())
        ]
        if not linhas:
            QMessageBox.information(self, "Preview", "Não há versos válidos para pré-visualizar.")
            return
        if not hasattr(self, "_preview_karaoke") or self._preview_karaoke is None:
            self._preview_karaoke = KaraokeWindow(
                audio_engine=self.audio_engine,
                config_manager=self.config_manager,
                parent=self,
            )
        self._preview_karaoke.definir_preview(self.current_track, linhas)
        self._preview_karaoke.show()
        self._preview_karaoke.raise_()
        self._preview_karaoke.activateWindow()

    def _carregar_modelo_editor(self):
        self.editor_model = self.config_manager.get("karaoke/editor_model", "stagebox") if self.config_manager else "stagebox"
        winamp = self.editor_model == "winamp"
        self.tabela.setVisible(not winamp)
        self.editor_texto.setVisible(winamp)
        self.lbl_modelo_preview.setVisible(not winamp)
        self._atualizar_preview_modelo(self.tabela.currentRow())

    def _formatar_cifras_editor(self, chords):
        if self.editor_model != "winamp":
            return chords
        partes = []
        ultima = 0
        for token in chords.split():
            if "@" in token:
                acorde, raw_pos = token.rsplit("@", 1)
                try:
                    pos = max(0, int(raw_pos))
                except ValueError:
                    pos = ultima
            else:
                acorde = token
                pos = ultima
            partes.append(" " * max(0, pos - ultima) + acorde)
            ultima = pos + len(acorde)
        return "".join(partes)

    def _normalizar_cifras_editor(self, texto):
        if self.editor_model != "winamp":
            return texto.strip()
        tokens = []
        for match in CHORD_TOKEN_PATTERN.finditer(texto):
            tokens.append(f"{match.group(0)}@{match.start()}")
        return " ".join(tokens)

    def _atualizar_preview_modelo(self, row):
        if row < 0 or row >= self.tabela.rowCount():
            self.lbl_modelo_preview.setText("")
            return
        tempo = self.tabela.item(row, 0)
        cifra = self.tabela.item(row, 1)
        texto = self.tabela.item(row, 2)
        if not tempo or not texto:
            return
        raw = cifra.data(Qt.ItemDataRole.UserRole) if cifra else ""
        raw = raw or (cifra.text() if cifra else "")
        chord_line = self._formatar_cifras_editor(raw)
        ms = int(tempo.data(Qt.ItemDataRole.UserRole) or 0)
        ts = format_timestamp_ms(ms)
        if self.editor_model == "winamp":
            total_seconds = ms // 1000
            ts = f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"
            self.lbl_modelo_preview.setText(
                f'<pre style="margin:0; color:#f59e0b; font-weight:700;">{chord_line}</pre>'
                f'<pre style="margin:0; color:#d1d5db;">[{ts}]{texto.text()}</pre>'
            )
        else:
            self.lbl_modelo_preview.setText(
                f'<span style="color:#9ca3af;">Modelo StageBox</span><br>'
                f'<span style="color:#f59e0b; font-weight:700;">{chord_line}</span> '
                f'<span style="color:#d1d5db;">[{ts}]{texto.text()}</span>'
            )

    def _popular_tabela(self, linhas: list[LyricLine]):
        self.tabela.blockSignals(True)
        self.tabela.setRowCount(0)

        for idx, line in enumerate(linhas):
            self._inserir_linha_tabela(idx, line.timestamp_ms, line.clean_lyrics, line.chords)

        self.tabela.blockSignals(False)
        if self.tabela.rowCount() > 0:
            self.tabela.selectRow(0)

    def _inserir_linha_tabela(self, row: int, timestamp_ms: int, text: str, chords: str = ""):
        self.tabela.insertRow(row)

        # Col 0: Tempo
        item_tempo = QTableWidgetItem(format_timestamp_ms(timestamp_ms))
        item_tempo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item_tempo.setData(Qt.ItemDataRole.UserRole, timestamp_ms)
        item_tempo.setToolTip("Clique aqui para carimbar o tempo atual da música neste verso")
        self.tabela.setItem(row, 0, item_tempo)

        # Col 2: Cifras / Acordes separados
        item_cifras = QTableWidgetItem(self._formatar_cifras_editor(chords))
        item_cifras.setForeground(QColor("#f59e0b"))
        item_cifras.setFont(QFont("Monospace", 10, QFont.Weight.Bold))
        item_cifras.setData(Qt.ItemDataRole.UserRole, chords)
        self.tabela.setItem(row, 1, item_cifras)

        # Col 3: Frase limpa do verso
        item_texto = QTableWidgetItem(text)
        self.tabela.setItem(row, 2, item_texto)

        # Col 4: Botões de ação
        widget_acoes = QWidget()
        layout_acoes = QHBoxLayout(widget_acoes)
        layout_acoes.setContentsMargins(4, 2, 4, 2)
        layout_acoes.setSpacing(2)

        btn_marcar = QPushButton()
        btn_marcar.setObjectName("btnRowAction")
        btn_marcar.setIcon(get_stateful_icon("timer", normal_color="#bdbdbd", hover_color="#60a5fa", active_color="#60a5fa"))
        btn_marcar.setIconSize(QSize(17, 17))
        btn_marcar.setFixedSize(28, 28)
        btn_marcar.setFlat(True)
        btn_marcar.setToolTip("Marcar tempo")
        btn_marcar.clicked.connect(lambda checked=False, r=row: self._gravar_tempo_linha(r))
        layout_acoes.addWidget(btn_marcar)

        btn_ouvir = QPushButton()
        btn_ouvir.setObjectName("btnRowAction")
        btn_ouvir.setIcon(get_stateful_icon("play", normal_color="#bdbdbd", hover_color="#60a5fa", active_color="#60a5fa"))
        btn_ouvir.setIconSize(QSize(16, 16))
        btn_ouvir.setFixedSize(28, 28)
        btn_ouvir.setFlat(True)
        btn_ouvir.setToolTip("Ouvir a partir desta linha")
        btn_ouvir.clicked.connect(lambda checked=False, r=row: self._ouvir_linha(r))
        layout_acoes.addWidget(btn_ouvir)

        self.tabela.setCellWidget(row, 3, widget_acoes)

    def _on_cell_clicked(self, row: int, col: int):
        """Disparado quando o usuário clica em qualquer célula da tabela."""
        if self._ignorar_clique_interno:
            return

        if self.chk_click_to_sync.isChecked() and self.audio_engine.is_playing():
            self._gravar_tempo_linha(row)
        elif col == 1:
            self._gravar_tempo_linha(row)

    def _gravar_tempo_linha(self, row: int):
        """Grava a posição atual do áudio na linha especificada."""
        if not (0 <= row < self.tabela.rowCount()):
            return

        posicao_ms = self.audio_engine.position()
        item_tempo = self.tabela.item(row, 0)
        if item_tempo:
            item_tempo.setText(format_timestamp_ms(posicao_ms))
            item_tempo.setData(Qt.ItemDataRole.UserRole, posicao_ms)

        self._ignorar_clique_interno = True
        self.tabela.selectRow(row)
        self._ignorar_clique_interno = False

    def _gravar_tempo_linha_selecionada(self):
        """Grava o tempo na linha selecionada e avança para a próxima automaticamente."""
        linha_atual = self.tabela.currentRow()
        if linha_atual < 0:
            if self.tabela.rowCount() > 0:
                linha_atual = 0
            else:
                return

        self._gravar_tempo_linha(linha_atual)

        if linha_atual < self.tabela.rowCount() - 1:
            self._ignorar_clique_interno = True
            self.tabela.selectRow(linha_atual + 1)
            self.tabela.scrollToItem(self.tabela.item(linha_atual + 1, 0))
            self._ignorar_clique_interno = False

    def _on_table_item_changed(self, item):
        row = item.row()
        col = item.column()

        if col == 0:
            ms = parse_timestamp_ms(item.text())
            item.setData(Qt.ItemDataRole.UserRole, ms)
        elif col == 1:
            item.setData(Qt.ItemDataRole.UserRole, self._normalizar_cifras_editor(item.text()))
        self._atualizar_preview_modelo(row)

    def _ouvir_linha(self, row: int):
        if not (0 <= row < self.tabela.rowCount()):
            return

        item_tempo = self.tabela.item(row, 0)
        if item_tempo is None:
            return

        ms = item_tempo.data(Qt.ItemDataRole.UserRole)
        if ms is None:
            return

        self.audio_engine.set_position(int(ms))
        self.audio_engine.play()

    def _adicionar_linha(self):
        row = self.tabela.currentRow()
        if row < 0:
            row = self.tabela.rowCount()
        else:
            row += 1

        posicao = self.audio_engine.position()
        self._inserir_linha_tabela(row, posicao, "Novo verso...", "")
        self._renumerar_e_reconstruir_acoes()
        self.tabela.selectRow(row)

    def _remover_linha(self):
        row = self.tabela.currentRow()
        if 0 <= row < self.tabela.rowCount():
            self.tabela.removeRow(row)
            self._renumerar_e_reconstruir_acoes()

    def _remover_linhas_selecionadas(self):
        linhas = sorted({index.row() for index in self.tabela.selectionModel().selectedRows()}, reverse=True)
        if not linhas:
            return

        for row in linhas:
            self.tabela.removeRow(row)

        self._renumerar_e_reconstruir_acoes()

        if self.tabela.rowCount() > 0:
            self.tabela.selectRow(min(linhas[-1], self.tabela.rowCount() - 1))

    def _mover_linha(self, delta: int):
        row = self.tabela.currentRow()
        destino = row + delta
        if 0 <= row < self.tabela.rowCount() and 0 <= destino < self.tabela.rowCount():
            tempo_ms = self.tabela.item(row, 0).data(Qt.ItemDataRole.UserRole)
            item_chords = self.tabela.item(row, 1)
            chords = (
                item_chords.data(Qt.ItemDataRole.UserRole)
                if item_chords and item_chords.data(Qt.ItemDataRole.UserRole)
                else (item_chords.text() if item_chords else "")
            )
            texto = self.tabela.item(row, 2).text()

            self.tabela.removeRow(row)
            self._inserir_linha_tabela(destino, tempo_ms, texto, chords)
            self._renumerar_e_reconstruir_acoes()
            self.tabela.selectRow(destino)

    def _renumerar_e_reconstruir_acoes(self):
        for r in range(self.tabela.rowCount()):
            widget_acoes = QWidget()
            layout_acoes = QHBoxLayout(widget_acoes)
            layout_acoes.setContentsMargins(2, 1, 2, 1)
            layout_acoes.setSpacing(2)

            btn_marcar = QPushButton()
            btn_marcar.setObjectName("btnRowAction")
            btn_marcar.setIcon(get_svg_icon("timer", color="#e5e7eb"))
            btn_marcar.setIconSize(QSize(17, 17))
            btn_marcar.setFixedSize(28, 28)
            btn_marcar.setFlat(True)
            btn_marcar.setToolTip("Marcar tempo")
            btn_marcar.clicked.connect(lambda checked=False, row_idx=r: self._gravar_tempo_linha(row_idx))
            layout_acoes.addWidget(btn_marcar)

            btn_ouvir = QPushButton()
            btn_ouvir.setObjectName("btnRowAction")
            btn_ouvir.setIcon(get_svg_icon("play", color="#e5e7eb"))
            btn_ouvir.setIconSize(QSize(16, 16))
            btn_ouvir.setFixedSize(28, 28)
            btn_ouvir.setFlat(True)
            btn_ouvir.setToolTip("Ouvir a partir desta linha")
            btn_ouvir.clicked.connect(lambda checked=False, row_idx=r: self._ouvir_linha(row_idx))
            layout_acoes.addWidget(btn_ouvir)

            self.tabela.setCellWidget(r, 3, widget_acoes)

    def _abrir_dialogo_colar_cifra_completa(self):
        """Abre caixa de diálogo para colar a música completa com cifras copiadas da internet."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Colar Música Completa com Cifras")
        dialog.resize(700, 530)
        layout = QVBoxLayout(dialog)

        lbl = QLabel(
            "<b>Cole a música completa abaixo:</b><br>"
            "<span style='color:#9ca3af;'>O sistema detectará automaticamente as linhas de cifras e as colocará separadas dos versos, mantendo as frases 100% limpas.</span>"
        )
        layout.addWidget(lbl)

        txt_edit = QPlainTextEdit()
        txt_edit.setPlaceholderText(
            "[Intro] C  Am  F  G\n\n"
            "C                  Am\n"
            "A letra da música aparecerá aqui\n"
            "G                  F\n"
            "quando houver um arquivo de karaoke\n"
        )
        txt_edit.setFont(QFont("Monospace", 10))
        layout.addWidget(txt_edit, 1)

        layout_btn = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(dialog.reject)

        btn_aplicar = QPushButton("Importar")
        btn_aplicar.setIcon(get_svg_icon("paste", color="#ffffff"))
        btn_aplicar.setIconSize(QSize(18, 18))
        btn_aplicar.setStyleSheet("background: #059669; color: white; font-weight: bold; padding: 6px 16px;")
        btn_aplicar.setDefault(True)

        def aplicar():
            texto = txt_edit.toPlainText()
            if not texto.strip():
                dialog.reject()
                return

            linhas_convertidas = convert_chord_sheet_to_lyric_lines(texto)
            if linhas_convertidas:
                self._popular_tabela(linhas_convertidas)
                self._renumerar_e_reconstruir_acoes()
                QMessageBox.information(
                    self,
                    "Cifra Processada!",
                    f"Foram importados {len(linhas_convertidas)} versos com frases limpas e cifras organizadas.\n\n"
                    "Agora dê Play na música e clique nas linhas para carimbar o tempo de cada uma!",
                )
            dialog.accept()

        btn_aplicar.clicked.connect(aplicar)
        layout_btn.addWidget(btn_cancel)
        layout_btn.addWidget(btn_aplicar)
        layout.addLayout(layout_btn)
        dialog.exec()

    def _ajustar_offset_geral(self):
        offset, ok = QInputDialog.getInt(
            self,
            "Ajustar Offset Geral",
            "Deslocar todos os tempos em milissegundos (+ adiantar, - atrasar):",
            0,
            -60000,
            60000,
            100,
        )
        if ok and offset != 0:
            if self.editor_model == "winamp":
                linhas = self._linhas_do_texto_winamp()
                for line in linhas:
                    line.timestamp_ms = max(0, line.timestamp_ms + offset)
                self.editor_texto.blockSignals(True)
                self.editor_texto.setPlainText(self._linhas_para_texto_winamp(linhas))
                self.editor_texto.blockSignals(False)
                return
            for r in range(self.tabela.rowCount()):
                item_tempo = self.tabela.item(r, 0)
                if item_tempo:
                    ms_atual = item_tempo.data(Qt.ItemDataRole.UserRole) or 0
                    novo_ms = max(0, ms_atual + offset)
                    item_tempo.setText(format_timestamp_ms(novo_ms))
                    item_tempo.setData(Qt.ItemDataRole.UserRole, novo_ms)

    def salvar_letra(self):
        """Salva a lista de linhas na pasta centralizada de karaoke."""
        if self.current_track is None:
            QMessageBox.warning(self, "Aviso", "Nenhuma música carregada para salvar a letra.")
            return

        if self.editor_model == "winamp":
            linhas = self._linhas_do_texto_winamp()
        else:
            linhas: list[LyricLine] = []
            for r in range(self.tabela.rowCount()):
                item_tempo = self.tabela.item(r, 0)
                item_chords = self.tabela.item(r, 1)
                item_texto = self.tabela.item(r, 2)
                ms = item_tempo.data(Qt.ItemDataRole.UserRole) if item_tempo else 0
                if ms is None:
                    ms = 0
                chords = (
                    item_chords.data(Qt.ItemDataRole.UserRole)
                    if item_chords and item_chords.data(Qt.ItemDataRole.UserRole)
                    else (item_chords.text().strip() if item_chords else "")
                )
                texto = item_texto.text() if item_texto else ""
                linhas.append(LyricLine(timestamp_ms=int(ms), text=texto, chords=chords))

        destino = self.target_lrc_path or get_save_lyrics_path(self.current_track, self.config_manager)
        sucesso = save_lrc(
            path=destino,
            lines=linhas,
            title=self.current_track.title,
            artist=self.current_track.artist,
        )

        if sucesso:
            QMessageBox.information(
                self,
                "Karaoke Salvo!",
                f"Letra sincronizada gravada com sucesso na pasta central:\n\n{destino}",
            )
        else:
            QMessageBox.critical(
                self,
                "Erro",
                f"Falha ao gravar o arquivo de letra em:\n{destino}",
            )

    def _avancar_tempo(self, delta_ms: int):
        nova_pos = max(0, self.audio_engine.position() + delta_ms)
        self.audio_engine.set_position(nova_pos)

    def _alternar_play_audio(self):
        if self.audio_engine.is_playing():
            self.audio_engine.pause()
        else:
            self.audio_engine.play()

    def _atualizar_botao_play(self):
        tema = self.config_manager.get("appearance/theme", "dark") if self.config_manager else "dark"
        cor_play = "#171717" if tema == "dark" else "#ffffff"

        if self.audio_engine.is_playing():
            self.btn_play.setIcon(get_svg_icon("pause", color=cor_play))
            self.btn_play.setToolTip("Pausar (Espaço)")
        else:
            self.btn_play.setIcon(get_svg_icon("play", color=cor_play))
            self.btn_play.setToolTip("Reproduzir (Espaço)")
        self.btn_play.setIconSize(QSize(18, 18))

    def _on_audio_position_changed(self, pos_ms: int):
        duracao = self.audio_engine.duration()
        self.slider_posicao.setRange(0, duracao)
        self.slider_posicao.setValue(pos_ms)
        self.lbl_tempo.setText(f"{format_timestamp_ms(pos_ms)} / {format_timestamp_ms(duracao)}")
