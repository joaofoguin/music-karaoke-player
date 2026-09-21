from html import escape
from pathlib import Path

from PySide6.QtCore import QTimer, QSize, Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QShortcut
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


class MarqueeLabel(QLabel):
    """Exibe um texto em uma única linha e o desloca quando ele não cabe."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._texto_original = text
        self._offset = 0
        self._animacao = QTimer(self)
        self._animacao.setInterval(120)
        self._animacao.timeout.connect(self._avancar)
        self.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.setMinimumWidth(0)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

    def setText(self, text):
        self._texto_original = text or ""
        self._offset = 0
        self._atualizar_exibicao()
        self._reiniciar_animacao()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._atualizar_exibicao()
        self._reiniciar_animacao()

    def _texto_cabe(self):
        return self.fontMetrics().horizontalAdvance(self._texto_original) <= max(0, self.width())

    def _reiniciar_animacao(self):
        self._animacao.stop()
        if self._texto_original and not self._texto_cabe():
            self._animacao.start()

    def _avancar(self):
        if self._texto_cabe():
            self._animacao.stop()
            self._offset = 0
            self._atualizar_exibicao()
            return

        texto = self._texto_original + "     "
        self._offset = (self._offset + 1) % len(texto)
        self._atualizar_exibicao()

    def _atualizar_exibicao(self):
        if not self._texto_original or self._texto_cabe():
            super().setText(self._texto_original)
            return

        texto = self._texto_original + "     "
        rotacao = texto[self._offset:] + texto[:self._offset]
        largura = self.width()
        if largura <= 0:
            super().setText(self._texto_original)
            return

        fim = 0
        while fim < len(rotacao) and self.fontMetrics().horizontalAdvance(rotacao[:fim + 1]) <= largura:
            fim += 1
        super().setText(rotacao[:fim])


class KaraokeWindow(QMainWindow):
    """Janela secundária para exibição de letras e cifras sincronizadas com mini player integrado no topo."""

    editar_solicitado = Signal()
    faixa_anterior_solicitada = Signal()
    faixa_proxima_solicitada = Signal()

    MENSAGEM_SEM_LETRA = (
        "Nenhum arquivo de letra/karaoke encontrado para esta faixa\n\n"
        "Clique no ícone de edição acima para criar ou sincronizar\n"
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
        self._theme = "dark"
        self.highlight_color = "#ffffff"
        self.context_color = "#8f8f8f"
        self.chords_color = "#f59e0b"
        self.show_chords = True
        self.context_lines = 2
        self.bg_color = "#1d1d1d"

        self.lines = []
        self.current_index = -1
        self.proxima_track = None
        self._aviso_proxima_ms = 30000

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

        # Linha única: título em letreiro + controles do player
        linha_player = QHBoxLayout()
        linha_player.setSpacing(10)

        self.faixa_atual = MarqueeLabel("Nenhuma música selecionada")
        self.faixa_atual.setObjectName("trackTitle")
        self.faixa_atual.setStyleSheet("font-size: 16px; font-weight: bold;")
        linha_player.addWidget(self.faixa_atual, 1)

        # Controles rápidos de tamanho de letra
        self.btn_font_dec = QPushButton()
        self.btn_font_dec.setToolTip("Diminuir tamanho da letra (Ctrl+-)")
        self.btn_font_dec.setObjectName("iconBtn")
        self.btn_font_dec.clicked.connect(self._diminuir_fonte)
        linha_player.addWidget(self.btn_font_dec)

        self.lbl_font_size = QLabel("32px")
        self.lbl_font_size.setStyleSheet("font-size: 13px; font-weight: bold; color: #a3a3a3;")
        linha_player.addWidget(self.lbl_font_size)

        self.btn_font_inc = QPushButton()
        self.btn_font_inc.setToolTip("Aumentar tamanho da letra (Ctrl+=)")
        self.btn_font_inc.setObjectName("iconBtn")
        self.btn_font_inc.clicked.connect(self._aumentar_fonte)
        linha_player.addWidget(self.btn_font_inc)

        self.btn_editar = QPushButton()
        self.btn_editar.setObjectName("iconBtn")
        self.btn_editar.setToolTip("Editar letra (Ctrl+E)")
        self.btn_editar.clicked.connect(self.editar_solicitado.emit)
        linha_player.addWidget(self.btn_editar)

        self.botao_tela_cheia = QPushButton()
        self.botao_tela_cheia.setObjectName("iconBtn")
        self.botao_tela_cheia.setToolTip("Tela cheia (F11)")
        self.botao_tela_cheia.clicked.connect(self.alternar_tela_cheia)
        linha_player.addWidget(self.botao_tela_cheia)

        # Controles do player na mesma linha do nome da faixa.
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

        # Aviso flutuante da próxima faixa, exibido apenas no fim da música.
        self.popup_proxima = QFrame(self)
        self.popup_proxima.setObjectName("nextTrackPopup")
        popup_layout = QVBoxLayout(self.popup_proxima)
        popup_layout.setContentsMargins(14, 10, 14, 10)
        popup_layout.setSpacing(2)
        self.popup_titulo = QLabel("Próxima música")
        self.popup_titulo.setObjectName("nextTrackLabel")
        self.popup_faixa = QLabel()
        self.popup_faixa.setObjectName("nextTrackTitle")
        self.popup_artista = QLabel()
        self.popup_artista.setObjectName("nextTrackArtist")
        popup_layout.addWidget(self.popup_titulo)
        popup_layout.addWidget(self.popup_faixa)
        popup_layout.addWidget(self.popup_artista)
        self.popup_proxima.hide()

        self._criar_atalhos()

    def _criar_atalhos(self):
        self._atalho_diminuir = QShortcut(QKeySequence("Ctrl+-"), self)
        self._atalho_diminuir.activated.connect(self._diminuir_fonte)
        self._atalho_aumentar = QShortcut(QKeySequence("Ctrl+="), self)
        self._atalho_aumentar.activated.connect(self._aumentar_fonte)
        self._atalho_editar = QShortcut(QKeySequence("Ctrl+E"), self)
        self._atalho_editar.activated.connect(self.editar_solicitado.emit)
        self._atalho_fullscreen = QShortcut(QKeySequence("F11"), self)
        self._atalho_fullscreen.activated.connect(self.alternar_tela_cheia)
        self._atalho_escape = QShortcut(QKeySequence("Escape"), self)
        self._atalho_escape.activated.connect(self._sair_tela_cheia)
        self._atalho_anterior = QShortcut(QKeySequence("Ctrl+Left"), self)
        self._atalho_anterior.activated.connect(self.faixa_anterior_solicitada.emit)
        self._atalho_play = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        self._atalho_play.activated.connect(self._alternar_reproducao)
        self._atalho_proximo = QShortcut(QKeySequence("Ctrl+Right"), self)
        self._atalho_proximo.activated.connect(self.faixa_proxima_solicitada.emit)

    def _sair_tela_cheia(self):
        if self.isFullScreen():
            self.alternar_tela_cheia()

    def definir_proxima_faixa(self, track):
        self.proxima_track = track
        if track is None:
            self.popup_proxima.hide()
            return
        self.popup_faixa.setText(track.title or "Título desconhecido")
        self.popup_artista.setText(track.artist or "Artista desconhecido")
        self.popup_proxima.adjustSize()
        self._posicionar_popup()

    def _posicionar_popup(self):
        if self.popup_proxima is None:
            return
        margem = 20
        self.popup_proxima.move(
            max(margem, self.width() - self.popup_proxima.width() - margem),
            max(margem, self.height() - self.popup_proxima.height() - margem),
        )

    def _atualizar_popup_proxima(self, position_ms):
        if self.proxima_track is None or self.audio_engine is None:
            self.popup_proxima.hide()
            return
        duration = self.audio_engine.duration()
        restante = duration - position_ms
        if 0 < restante <= self._aviso_proxima_ms:
            self._posicionar_popup()
            self.popup_proxima.show()
            self.popup_proxima.raise_()
        else:
            self.popup_proxima.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._posicionar_popup()

    def carregar_configuracoes(self):
        if self.config_manager is not None:
            self.font_size = self.config_manager.get("karaoke/font_size", 32)
            self.highlight_color = self.config_manager.get("karaoke/highlight_color", "#ffffff")
            self.context_color = self.config_manager.get("karaoke/context_color", "#8f8f8f")
            self.chords_color = self.config_manager.get("karaoke/chords_color", "#f59e0b")
            self.show_chords = self.config_manager.get("karaoke/show_chords", True)
            self.context_lines = self.config_manager.get("karaoke/context_lines", 2)
            theme = self.config_manager.get("appearance/theme", "dark")
            self._theme = theme
            if theme == "midnight":
                self.bg_color = "#0e1117"
            elif theme == "light":
                self.bg_color = "#f5f5f7"
            else:
                self.bg_color = "#1d1d1d"

            if theme == "light":
                self.highlight_color = self._cor_visivel(self.highlight_color, "#111827")
                self.context_color = self._cor_visivel(self.context_color, "#6b7280")
                self.chords_color = self._cor_visivel(self.chords_color, "#b45309")

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

    @staticmethod
    def _cor_visivel(cor: str, fallback: str) -> str:
        try:
            base = QColor(cor)
            fundo = QColor("#f5f5f7")
            def luminancia(c):
                return (
                    0.2126 * (c.red() / 255) ** 2.2
                    + 0.7152 * (c.green() / 255) ** 2.2
                    + 0.0722 * (c.blue() / 255) ** 2.2
                )
            lb = luminancia(base)
            lf = luminancia(fundo)
            contraste = (max(lb, lf) + 0.05) / (min(lb, lf) + 0.05)
            return cor if contraste >= 4.0 else fallback
        except (TypeError, ValueError):
            return fallback

    def aplicar_estilo(self):
        tema = self._theme
        text_header = "#111827" if tema == "light" else "#f3f4f6"
        btn_bg = "#ffffff" if tema == "light" else "#242424" if tema == "midnight" else "#2e2e2e"
        btn_color = "#1f2937" if tema == "light" else "#f5f5f5"
        cor_icone = "#374151" if tema == "light" else "#e5e7eb"
        painel_bg = "#ffffff" if tema == "light" else "#131720" if tema == "midnight" else "#242424"
        painel_border = "#d1d5db" if tema == "light" else "#1f2937" if tema == "midnight" else "#383838"
        border = "#d1d5db" if tema == "light" else "#374151" if tema == "midnight" else "#4a4a4a"
        slider_bg = "#e5e7eb" if tema == "light" else "#1f2937" if tema == "midnight" else "#3a3a3a"

        self.setStyleSheet(
            f"""
            QMainWindow {{ background: {self.bg_color}; color: {text_header}; }}
            QFrame#topPanel {{ background: {painel_bg}; border: 1px solid {painel_border}; border-radius: 8px; }}
            QLabel#trackTitle {{ color: {text_header}; font-size: 15px; font-weight: 600; }}
            QLabel#lyrics {{ line-height: 1.8; }}
            QPushButton {{ background: {btn_bg}; color: {btn_color}; border: 1px solid {border}; border-radius: 4px; padding: 5px 12px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ opacity: 0.85; }}
            QPushButton#mediaBtn {{ background: transparent; border: 0; min-width: 32px; max-width: 32px; min-height: 32px; max-height: 32px; border-radius: 16px; padding: 2px; }}
            QPushButton#mediaBtn:hover {{ background: {("#e5e7eb" if tema == "light" else "#1f2937")}; }}
            QPushButton#iconBtn {{ background: transparent; border: 0; min-width: 32px; max-width: 32px; min-height: 32px; max-height: 32px; border-radius: 6px; padding: 2px; }}
            QPushButton#iconBtn:hover {{ background: {("#e5e7eb" if tema == "light" else "#1f2937")}; }}
            QPushButton#iconBtn:pressed {{ background: {("#d1d5db" if tema == "light" else "#374151")}; }}
            QPushButton#playBtn {{ background: #2563eb; color: #ffffff; border: 0; border-radius: 17px; min-width: 34px; max-width: 34px; min-height: 34px; max-height: 34px; padding: 0; }}
            QPushButton#playBtn:hover {{ background: #3b82f6; }}
            QFrame#nextTrackPopup {{ background: {painel_bg}; border: 1px solid #f59e0b; border-radius: 10px; }}
            QLabel#nextTrackLabel {{ color: #f59e0b; font-size: 11px; font-weight: 700; }}
            QLabel#nextTrackTitle {{ color: {text_header}; font-size: 14px; font-weight: 700; }}
            QLabel#nextTrackArtist {{ color: {("#6b7280" if tema == "light" else "#9ca3af")}; font-size: 11px; }}

            QSlider::groove:horizontal {{ height: 5px; background: {slider_bg}; border-radius: 2px; }}
            QSlider::handle:horizontal {{ width: 12px; margin: -4px 0; background: #3b82f6; border-radius: 6px; }}
            """
        )

        self.btn_font_dec.setIcon(get_svg_icon("font_decrease", color=cor_icone, size=48))
        self.btn_font_dec.setIconSize(QSize(18, 18))
        self.btn_font_inc.setIcon(get_svg_icon("font_increase", color=cor_icone, size=48))
        self.btn_font_inc.setIconSize(QSize(18, 18))
        self.btn_editar.setIcon(get_svg_icon("edit", color=cor_icone, size=48))
        self.btn_editar.setIconSize(QSize(18, 18))
        self.botao_tela_cheia.setIcon(get_svg_icon("fullscreen", color=cor_icone, size=48))
        self.botao_tela_cheia.setIconSize(QSize(18, 18))
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
        self._atualizar_popup_proxima(position_ms)
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
        self.definir_proxima_faixa(None)
        self.faixa_atual.setText("Nenhuma música selecionada")
        self.letra.setText(self.MENSAGEM_SEM_LETRA)

    def alternar_tela_cheia(self):
        if self.isFullScreen():
            self.showNormal()
            self.botao_tela_cheia.setIcon(get_svg_icon("fullscreen", color="#e5e7eb", size=48))
            self.botao_tela_cheia.setIconSize(QSize(18, 18))
            self.botao_tela_cheia.setToolTip("Tela cheia")
        else:
            self.showFullScreen()
            self.botao_tela_cheia.setIcon(get_svg_icon("fullscreen_exit", color="#e5e7eb", size=48))
            self.botao_tela_cheia.setIconSize(QSize(18, 18))
            self.botao_tela_cheia.setToolTip("Sair da tela cheia")
