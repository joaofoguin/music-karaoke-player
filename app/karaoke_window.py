from html import escape
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.lyrics import current_line_index, load_lrc, render_chord_line_html
from core.lyrics_storage import resolve_lyrics_path
from core.icons import get_svg_icon


class KaraokeWindow(QMainWindow):
    """Janela secundária para exibição de letras e cifras sincronizadas com mini player integrado no topo."""

    editar_solicitado = Signal()
    faixa_anterior_solicitada = Signal()
    faixa_proxima_solicitada = Signal()

    MENSAGEM_SEM_LETRA = (
        "Nenhum arquivo de letra/karaoke encontrado para esta faixa\n\n"
        "Clique em '✏️ Editar Letra' acima para criar ou sincronizar\n"
        "as letras e cifras diretamente no editor do reprodutor."
    )

    def __init__(self, audio_engine=None, config_manager=None, parent=None):
        super().__init__(parent)
        self.audio_engine = audio_engine
        self.config_manager = config_manager
        self.current_track = None
        self.setWindowTitle("Music Player — Karaoke")
        self.resize(1020, 660)
        self.setMinimumSize(700, 480)

        self.font_size = 32
        self.highlight_color = "#ffffff"
        self.context_color = "#8f8f8f"
        self.chords_color = "#f59e0b"
        self.show_chords = True
        self.context_lines = 2
        self.bg_color = "#1d1d1d"

        self.lines = []
        self.current_index = -1

        self._criar_interface()
        self.carregar_configuracoes()

        if self.config_manager is not None:
            self.config_manager.settings_changed.connect(self.carregar_configuracoes)

        if self.audio_engine is not None:
            self.audio_engine.position_changed.connect(self.atualizar_posicao)
            self.audio_engine.playback_started.connect(self._atualizar_botao_play)
            self.audio_engine.playback_paused.connect(self._atualizar_botao_play)
            self.audio_engine.playback_stopped.connect(self._atualizar_botao_play)

    def _criar_interface(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(32, 16, 32, 20)
        layout.setSpacing(12)

        # ----------------------------------------------------
        # PAINEL DO TOPO: CABEÇALHO + MINI PLAYER
        # ----------------------------------------------------
        painel_topo = QFrame()
        painel_topo.setObjectName("topPanel")
        layout_topo = QVBoxLayout(painel_topo)
        layout_topo.setContentsMargins(14, 10, 14, 10)
        layout_topo.setSpacing(8)

        # Linha 1: Título e Ferramentas
        linha1 = QHBoxLayout()
        linha1.setSpacing(10)

        self.faixa_atual = QLabel("Nenhuma música selecionada")
        self.faixa_atual.setObjectName("trackTitle")
        self.faixa_atual.setStyleSheet("font-size: 16px; font-weight: bold;")
        linha1.addWidget(self.faixa_atual, 1)

        # Controles rápidos de tamanho de letra
        self.btn_font_dec = QPushButton("A-")
        self.btn_font_dec.setToolTip("Diminuir tamanho da letra")
        self.btn_font_dec.setFixedWidth(36)
        self.btn_font_dec.clicked.connect(self._diminuir_fonte)
        linha1.addWidget(self.btn_font_dec)

        self.lbl_font_size = QLabel("32px")
        self.lbl_font_size.setStyleSheet("font-size: 13px; font-weight: bold; color: #a3a3a3;")
        linha1.addWidget(self.lbl_font_size)

        self.btn_font_inc = QPushButton("A+")
        self.btn_font_inc.setToolTip("Aumentar tamanho da letra")
        self.btn_font_inc.setFixedWidth(36)
        self.btn_font_inc.clicked.connect(self._aumentar_fonte)
        linha1.addWidget(self.btn_font_inc)

        self.btn_editar = QPushButton("✏️ Editar Letra")
        self.btn_editar.setToolTip("Abrir o Editor de Karaoke para ajustar tempos e cifras")
        self.btn_editar.clicked.connect(self.editar_solicitado.emit)
        linha1.addWidget(self.btn_editar)

        self.botao_tela_cheia = QPushButton("Tela cheia")
        self.botao_tela_cheia.clicked.connect(self.alternar_tela_cheia)
        linha1.addWidget(self.botao_tela_cheia)

        layout_topo.addLayout(linha1)

        # Linha 2: MINI PLAYER COMPACTO
        linha_player = QHBoxLayout()
        linha_player.setSpacing(10)

        self.btn_anterior = QPushButton()
        self.btn_anterior.setObjectName("mediaBtn")
        self.btn_anterior.setToolTip("Faixa anterior / Recomeçar (Ctrl+Left)")
        self.btn_anterior.clicked.connect(self.faixa_anterior_solicitada.emit)
        linha_player.addWidget(self.btn_anterior)

        self.btn_play = QPushButton()
        self.btn_play.setObjectName("playBtn")
        self.btn_play.setToolTip("Reproduzir / Pausar (Espaço)")
        self.btn_play.clicked.connect(self._alternar_reproducao)
        linha_player.addWidget(self.btn_play)

        self.btn_proximo = QPushButton()
        self.btn_proximo.setObjectName("mediaBtn")
        self.btn_proximo.setToolTip("Próxima faixa (Ctrl+Right)")
        self.btn_proximo.clicked.connect(self.faixa_proxima_solicitada.emit)
        linha_player.addWidget(self.btn_proximo)

        layout_topo.addLayout(linha_player)
        layout.addWidget(painel_topo)

        # ----------------------------------------------------
        # ÁREA DAS LETRAS / VERSOS
        # ----------------------------------------------------
        self.letra = QLabel(self.MENSAGEM_SEM_LETRA)
        self.letra.setObjectName("lyrics")
        self.letra.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.letra.setWordWrap(True)
        layout.addWidget(self.letra, 1)

    def carregar_configuracoes(self):
        if self.config_manager is not None:
            self.font_size = self.config_manager.get("karaoke/font_size", 32)
            self.highlight_color = self.config_manager.get("karaoke/highlight_color", "#ffffff")
            self.context_color = self.config_manager.get("karaoke/context_color", "#8f8f8f")
            self.chords_color = self.config_manager.get("karaoke/chords_color", "#f59e0b")
            self.show_chords = self.config_manager.get("karaoke/show_chords", True)
            self.context_lines = self.config_manager.get("karaoke/context_lines", 2)
            theme = self.config_manager.get("appearance/theme", "dark")
            if theme == "midnight":
                self.bg_color = "#0e1117"
            elif theme == "light":
                self.bg_color = "#f5f5f7"
            else:
                self.bg_color = "#1d1d1d"

        self.lbl_font_size.setText(f"{self.font_size}px")
        self.aplicar_estilo()
        self._mostrar_contexto()

    def _aumentar_fonte(self):
        novo = min(56, self.font_size + 2)
        self.font_size = novo
        self.lbl_font_size.setText(f"{novo}px")
        if self.config_manager:
            self.config_manager.set("karaoke/font_size", novo)
        self._mostrar_contexto()

    def _diminuir_fonte(self):
        novo = max(18, self.font_size - 2)
        self.font_size = novo
        self.lbl_font_size.setText(f"{novo}px")
        if self.config_manager:
            self.config_manager.set("karaoke/font_size", novo)
        self._mostrar_contexto()

    def aplicar_estilo(self):
        text_header = "#222222" if self.bg_color == "#f5f5f7" else "#bcbcbc"
        btn_bg = "#e0e0e0" if self.bg_color == "#f5f5f7" else "#2e2e2e"
        btn_color = "#111111" if self.bg_color == "#f5f5f7" else "#f5f5f5"
        cor_icone = "#374151" if self.bg_color == "#f5f5f7" else "#e5e7eb"

        self.setStyleSheet(
            f"""
            QMainWindow {{ background: {self.bg_color}; }}
            QFrame#topPanel {{ background: rgba(0, 0, 0, 0.25); border: 1px solid #383838; border-radius: 8px; }}
            QLabel#trackTitle {{ color: {text_header}; font-size: 15px; font-weight: 600; }}
            QLabel#lyrics {{ line-height: 1.8; }}
            QPushButton {{ background: {btn_bg}; color: {btn_color}; border: 1px solid #4a4a4a; border-radius: 4px; padding: 5px 12px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ opacity: 0.85; }}
            QPushButton#mediaBtn {{ background: transparent; border: 0; min-width: 32px; max-width: 32px; min-height: 32px; max-height: 32px; border-radius: 16px; padding: 2px; }}
            QPushButton#mediaBtn:hover {{ background: rgba(255, 255, 255, 0.12); }}
            QPushButton#playBtn {{ background: #2563eb; color: #ffffff; border: 0; border-radius: 17px; min-width: 34px; max-width: 34px; min-height: 34px; max-height: 34px; padding: 0; }}
            QPushButton#playBtn:hover {{ background: #3b82f6; }}
            QSlider::groove:horizontal {{ height: 5px; background: #3a3a3a; border-radius: 2px; }}
            QSlider::handle:horizontal {{ width: 12px; margin: -4px 0; background: #3b82f6; border-radius: 6px; }}
            """
        )

        self.btn_anterior.setIcon(get_svg_icon("previous", color=cor_icone, size=48))
        self.btn_anterior.setIconSize(QSize(16, 16))
        self.btn_proximo.setIcon(get_svg_icon("next", color=cor_icone, size=48))
        self.btn_proximo.setIconSize(QSize(16, 16))
        self._atualizar_botao_play()

    def _alternar_reproducao(self):
        if self.audio_engine:
            if self.audio_engine.is_playing():
                self.audio_engine.pause()
            else:
                self.audio_engine.play()

    def _atualizar_botao_play(self):
        cor_play = "#ffffff"
        if self.audio_engine and self.audio_engine.is_playing():
            self.btn_play.setIcon(get_svg_icon("pause", color=cor_play, size=48))
            self.btn_play.setToolTip("Pausar (Espaço)")
        else:
            self.btn_play.setIcon(get_svg_icon("play", color=cor_play, size=48))
            self.btn_play.setToolTip("Reproduzir (Espaço)")
        self.btn_play.setIconSize(QSize(16, 16))

    def atualizar_faixa(self, track):
        self.current_track = track
        if track is None:
            self.limpar()
            return

        self.carregar_letra(track)
        artista = track.artist or "Artista desconhecido"
        self.faixa_atual.setText(f"{track.title} — {artista}")

    def carregar_letra(self, track):
        caminho_lrc = resolve_lyrics_path(track, self.config_manager)
        if caminho_lrc and caminho_lrc.is_file():
            self.lines = load_lrc(caminho_lrc)
        else:
            self.lines = []

        self.current_index = -1
        if not self.lines:
            self.letra.setText(self.MENSAGEM_SEM_LETRA)
        else:
            self._mostrar_contexto()

    def recarregar_letra_atual(self):
        """Recarrega a letra caso tenha sido editada no KaraokeEditor."""
        if self.current_track is not None:
            self.carregar_letra(self.current_track)

    def atualizar_posicao(self, position_ms):
        if not self.lines:
            return

        novo_indice = current_line_index(self.lines, position_ms)
        if novo_indice == self.current_index:
            return

        self.current_index = novo_indice
        self._mostrar_contexto()

    def _mostrar_contexto(self):
        if not self.lines:
            return

        if self.current_index < 0:
            fim = min(len(self.lines), self.context_lines + 1)
            trechos = []
            for index in range(0, fim):
                trechos.append(
                    render_chord_line_html(
                        line=self.lines[index],
                        is_active=False,
                        active_color=self.highlight_color,
                        context_color=self.context_color,
                        chords_color=self.chords_color,
                        show_chords=self.show_chords,
                        font_size=self.font_size,
                    )
                )
            self.letra.setText("".join(trechos))
            return

        inicio = max(0, self.current_index - self.context_lines)
        fim = min(len(self.lines), self.current_index + self.context_lines + 1)
        trechos = []

        for index in range(inicio, fim):
            is_active = (index == self.current_index)
            trechos.append(
                render_chord_line_html(
                    line=self.lines[index],
                    is_active=is_active,
                    active_color=self.highlight_color,
                    context_color=self.context_color,
                    chords_color=self.chords_color,
                    show_chords=self.show_chords,
                    font_size=self.font_size,
                )
            )

        self.letra.setText("".join(trechos))

    def limpar(self):
        self.lines = []
        self.current_index = -1
        self.current_track = None
        self.faixa_atual.setText("Nenhuma música selecionada")
        self.letra.setText(self.MENSAGEM_SEM_LETRA)

    def alternar_tela_cheia(self):
        if self.isFullScreen():
            self.showNormal()
            self.botao_tela_cheia.setText("Tela cheia")
        else:
            self.showFullScreen()
            self.botao_tela_cheia.setText("Sair da tela cheia")
