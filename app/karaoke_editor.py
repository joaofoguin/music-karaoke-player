from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QKeySequence, QShortcut
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
    LyricLine,
    convert_chord_sheet_to_lyric_lines,
    extract_chords_and_lyrics,
    format_timestamp_ms,
    load_lrc,
    parse_timestamp_ms,
    save_lrc,
)
from core.lyrics_storage import get_save_lyrics_path, resolve_lyrics_path
from core.icons import get_svg_icon
from core.clickable_slider import ClickableSlider


class KaraokeEditorWindow(QMainWindow):
    """Janela profissional para importação de cifras completas, edição de versos limpos e sincronização ao vivo clicando nas linhas."""

    def __init__(self, audio_engine, config_manager=None, parent=None):
        super().__init__(parent)
        self.audio_engine = audio_engine
        self.config_manager = config_manager
        self.current_track = None
        self.target_lrc_path = None
        self._ignorar_clique_interno = False

        self.setWindowTitle("Editor de Karaoke e Cifras")
        self.resize(1120, 740)
        self.setMinimumSize(860, 540)

        self._criar_interface()
        self._criar_atalhos()
        self._aplicar_estilo()

        # Conexões com o motor de áudio
        self.audio_engine.position_changed.connect(self._on_audio_position_changed)
        self.audio_engine.playback_started.connect(self._atualizar_botao_play)
        self.audio_engine.playback_paused.connect(self._atualizar_botao_play)
        self.audio_engine.playback_stopped.connect(self._atualizar_botao_play)

    def _aplicar_estilo(self):
        tema = self.config_manager.get("appearance/theme", "dark") if self.config_manager else "dark"
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
                QPushButton#btnRowAction { background: transparent; border: none; padding: 0; border-radius: 0; }\n                QPushButton#btnRowAction:hover { background: transparent; border: none; }\n                QPushButton#btnRowAction { background: transparent; border: none; padding: 0; border-radius: 0; }\n                QPushButton#btnRowAction:hover { background: transparent; border: none; }\n                QPushButton#btnRowAction { background: transparent; border: none; padding: 0; border-radius: 0; }\n                QPushButton#btnRowAction:hover { background: transparent; border: none; }\n                QPushButton#btnTopAction { background: #047857; color: #ffffff; font-weight: bold; font-size: 13px; border: 0; padding: 6px 14px; }
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
        self.lbl_faixa.setStyleSheet("font-size: 16px; font-weight: bold;")
        linha1.addWidget(self.lbl_faixa, 1)

        self.btn_colar_musica = QPushButton("Importar")
        self.btn_colar_musica.setObjectName("btnTopAction")
        self.btn_colar_musica.setIcon(get_svg_icon("paste", color="#ffffff"))
        self.btn_colar_musica.setIconSize(QSize(18, 18))
        self.btn_colar_musica.setToolTip("Importar letra e cifras")
        self.btn_colar_musica.clicked.connect(self._abrir_dialogo_colar_cifra_completa)
        linha1.addWidget(self.btn_colar_musica)

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
        self.lbl_tempo.setStyleSheet("font-size: 13px; font-family: monospace; font-weight: bold;")
        linha2.addWidget(self.lbl_tempo)

        # Barra de reprodução com clique direto!
        self.slider_posicao = ClickableSlider(Qt.Orientation.Horizontal)
        self.slider_posicao.sliderMoved.connect(self.audio_engine.set_position)
        self.slider_posicao.clicked_position.connect(self.audio_engine.set_position)
        linha2.addWidget(self.slider_posicao, 1)

        self.btn_sync = QPushButton("Marcar")
        self.btn_sync.setIcon(get_svg_icon("timer", color="#ffffff"))
        self.btn_sync.setIconSize(QSize(18, 18))
        self.btn_sync.setObjectName("btnSync")
        self.btn_sync.setFixedHeight(36)
        self.btn_sync.setToolTip("Marcar tempo da linha selecionada (F5)")
        self.btn_sync.clicked.connect(self._gravar_tempo_linha_selecionada)
        linha2.addWidget(self.btn_sync)

        layout_topo.addLayout(linha2)

        # Dica / Opção de clique na linha
        linha_dica = QHBoxLayout()
        self.chk_click_to_sync = QCheckBox("Modo de Marcação Rápida: clicar em qualquer linha grava o tempo atual do áudio nela")
        self.chk_click_to_sync.setChecked(True)
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

        self.tabela.cellClicked.connect(self._on_cell_clicked)
        self.tabela.itemChanged.connect(self._on_table_item_changed)

        layout_principal.addWidget(self.tabela, 1)

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
        self.btn_salvar.setIcon(get_svg_icon("save"))
        self.btn_salvar.setIconSize(QSize(20, 20))
        self.btn_salvar.setFixedSize(42, 36)
        self.btn_salvar.setToolTip("Salvar letra e cifras (Ctrl+S)")
        self.btn_salvar.setStyleSheet("font-weight: bold;")
        self.btn_salvar.clicked.connect(self.salvar_letra)
        layout_rodape.addWidget(self.btn_salvar)

        layout_principal.addWidget(painel_rodape)

    def _criar_atalhos(self):
        self.shortcut_play_pause = QShortcut(QKeySequence("Space"), self)
        self.shortcut_play_pause.setContext(Qt.ShortcutContext.WindowShortcut)
        self.shortcut_play_pause.activated.connect(self._alternar_play_audio)

        self.shortcut_marcar = QShortcut(QKeySequence("F5"), self)
        self.shortcut_marcar.setContext(Qt.ShortcutContext.WindowShortcut)
        self.shortcut_marcar.activated.connect(self._gravar_tempo_linha_selecionada)

        self.shortcut_salvar = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_salvar.setContext(Qt.ShortcutContext.WindowShortcut)
        self.shortcut_salvar.activated.connect(self.salvar_letra)

        self.shortcut_adicionar = QShortcut(QKeySequence("Insert"), self)
        self.shortcut_adicionar.setContext(Qt.ShortcutContext.WindowShortcut)
        self.shortcut_adicionar.activated.connect(self._adicionar_linha)

        self.shortcut_remover = QShortcut(QKeySequence("Delete"), self)
        self.shortcut_remover.setContext(Qt.ShortcutContext.WindowShortcut)
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
        item_cifras = QTableWidgetItem(chords)
        item_cifras.setForeground(QColor("#f59e0b"))
        item_cifras.setFont(QFont("Monospace", 10, QFont.Weight.Bold))
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
        btn_marcar.setIcon(get_svg_icon("timer"))
        btn_marcar.setIconSize(QSize(17, 17))
        btn_marcar.setFixedSize(28, 28)
        btn_marcar.setFlat(True)
        btn_marcar.setToolTip("Marcar tempo")
        btn_marcar.clicked.connect(lambda checked=False, r=row: self._gravar_tempo_linha(r))
        layout_acoes.addWidget(btn_marcar)

        btn_ouvir = QPushButton()
        btn_ouvir.setObjectName("btnRowAction")
        btn_ouvir.setIcon(get_svg_icon("play"))
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

        if col == 1:
            ts_str = item.text()
            ms = parse_timestamp_ms(ts_str)
            item.setData(Qt.ItemDataRole.UserRole, ms)

    def _ouvir_linha(self, row: int):
        item_tempo = self.tabela.item(row, 1)
        if item_tempo:
            ms = item_tempo.data(Qt.ItemDataRole.UserRole)
            if ms is not None:
                self.audio_engine.set_position(ms)
                if not self.audio_engine.is_playing():
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
            chords = self.tabela.item(row, 1).text()
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
            btn_marcar.setIcon(get_svg_icon("timer"))
            btn_marcar.setIconSize(QSize(17, 17))
            btn_marcar.setFixedSize(28, 28)
            btn_marcar.setFlat(True)
            btn_marcar.setToolTip("Marcar tempo")
            btn_marcar.clicked.connect(lambda checked=False, row_idx=r: self._gravar_tempo_linha(row_idx))
            layout_acoes.addWidget(btn_marcar)

            btn_ouvir = QPushButton()
            btn_ouvir.setObjectName("btnRowAction")
            btn_ouvir.setIcon(get_svg_icon("play"))
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

        linhas: list[LyricLine] = []
        for r in range(self.tabela.rowCount()):
            item_tempo = self.tabela.item(r, 0)
            item_chords = self.tabela.item(r, 1)
            item_texto = self.tabela.item(r, 2)
            ms = item_tempo.data(Qt.ItemDataRole.UserRole) if item_tempo else 0
            if ms is None:
                ms = 0
            chords = item_chords.text().strip() if item_chords else ""
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
