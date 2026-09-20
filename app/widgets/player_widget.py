from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from core.clickable_slider import ClickableSlider
from core.icons import get_svg_icon, get_stateful_icon


class PlayerWidget(QFrame):
    """Painel visual de reprodução e seus controles diretos."""

    previous_requested = Signal()
    play_requested = Signal()
    next_requested = Signal()
    repeat_changed = Signal(bool)
    karaoke_requested = Signal()
    mute_requested = Signal()
    volume_changed = Signal(int)
    position_changed = Signal(int)

    def __init__(self, playback, parent=None):
        super().__init__(parent)
        self.playback = playback
        self._theme = "dark"
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        self.setObjectName("playerBar")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        self.capa = QLabel("CAPA")
        self.capa.setFixedSize(54, 54)
        self.capa.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.capa.setStyleSheet(
            "background: #2b2b2b; border: 1px solid #444444; border-radius: 6px; font-size: 11px;"
        )

        info_layout = QVBoxLayout()
        info_layout.setSpacing(0)
        self.titulo_musica = QLabel("Nenhuma música selecionada")
        self.artista_musica = QLabel("Artista")
        self.album_musica = QLabel("Álbum")
        self.titulo_musica.setObjectName("trackTitle")
        self.artista_musica.setObjectName("trackMetadata")
        self.album_musica.setObjectName("trackMetadata")
        info_layout.addWidget(self.titulo_musica)
        info_layout.addWidget(self.artista_musica)
        info_layout.addWidget(self.album_musica)

        current_layout = QHBoxLayout()
        current_layout.setSpacing(6)
        current_layout.addWidget(self.capa)
        current_layout.addLayout(info_layout)
        layout.addLayout(current_layout, 3)

        center = QVBoxLayout()
        center.setSpacing(1)
        center.setContentsMargins(8, 0, 8, 0)
        center.setAlignment(Qt.AlignmentFlag.AlignCenter)

        controls = QHBoxLayout()
        controls.setSpacing(6)
        controls.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.botao_anterior = QPushButton()
        self.botao_play = QPushButton()
        self.botao_proximo = QPushButton()
        self.botao_repetir = QPushButton()
        self.botao_repetir.setCheckable(True)

        self.botao_anterior.setObjectName("mediaButton")
        self.botao_play.setObjectName("mainPlayButton")
        self.botao_proximo.setObjectName("mediaButton")
        self.botao_repetir.setObjectName("mediaButton")

        self.botao_anterior.setToolTip("Faixa anterior / Recomeçar (Ctrl+Left)")
        self.botao_play.setToolTip("Reproduzir ou pausar (Espaço)")
        self.botao_proximo.setToolTip("Próxima faixa (Ctrl+Right)")
        self.botao_repetir.setToolTip("Repetir a música atual (Ctrl+R)")

        controls.addWidget(self.botao_anterior)
        controls.addWidget(self.botao_play)
        controls.addWidget(self.botao_proximo)
        controls.addWidget(self.botao_repetir)
        center.addLayout(controls)

        progress = QHBoxLayout()
        progress.setSpacing(4)
        self.tempo_atual = QLabel("00:00")
        self.tempo_total = QLabel("00:00")
        self.tempo_atual.setObjectName("trackMetadata")
        self.tempo_total.setObjectName("trackMetadata")

        self.slider_progresso = ClickableSlider(Qt.Orientation.Horizontal)
        self.slider_progresso.setMaximumWidth(400)
        self.slider_progresso.setMinimumWidth(180)
        progress.addWidget(self.tempo_atual)
        progress.addWidget(self.slider_progresso, 1)
        progress.addWidget(self.tempo_total)
        center.addLayout(progress)
        layout.addLayout(center, 5)

        right = QHBoxLayout()
        right.setSpacing(5)
        right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.botao_karaoke = QPushButton()
        self.botao_karaoke.setObjectName("mediaButton")
        self.botao_karaoke.setToolTip("Abrir tela de Karaoke (Ctrl+K)")

        self.btn_vol_icon = QPushButton()
        self.btn_vol_icon.setObjectName("mediaButton")
        self.btn_vol_icon.setToolTip("Alternar mudo (Ctrl+M)")

        self.volume = ClickableSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setFixedWidth(72)
        right.addWidget(self.botao_karaoke)
        right.addWidget(self.btn_vol_icon)
        right.addWidget(self.volume)
        layout.addLayout(right, 2)

    def _connect_signals(self):
        self.botao_anterior.clicked.connect(self.previous_requested.emit)
        self.botao_play.clicked.connect(self.play_requested.emit)
        self.botao_proximo.clicked.connect(self.next_requested.emit)
        self.botao_repetir.toggled.connect(self.repeat_changed.emit)
        self.botao_karaoke.clicked.connect(self.karaoke_requested.emit)
        self.btn_vol_icon.clicked.connect(self.mute_requested.emit)

        self.slider_progresso.sliderMoved.connect(self.playback.set_position)
        self.slider_progresso.clicked_position.connect(self.playback.set_position)
        self.volume.valueChanged.connect(self.volume_changed.emit)
        self.volume.clicked_position.connect(self.volume_changed.emit)

        self.playback.playback_started.connect(self.atualizar_botao_play)
        self.playback.playback_paused.connect(self.atualizar_botao_play)
        self.playback.playback_stopped.connect(self.atualizar_botao_play)
        self.playback.position_changed.connect(self.atualizar_posicao)
        self.playback.duration_changed.connect(self.atualizar_duracao)

    def atualizar_icones(self, tema: str):
        self._theme = tema
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
        tema = self._tema_atual()
        cor_play = "#171717" if tema == "dark" else "#ffffff"
        if self.playback.is_playing():
            self.botao_play.setIcon(get_svg_icon("pause", color=cor_play, size=64))
            self.botao_play.setToolTip("Pausar (Espaço)")
        else:
            self.botao_play.setIcon(get_svg_icon("play", color=cor_play, size=64))
            self.botao_play.setToolTip("Reproduzir (Espaço)")
        self.botao_play.setIconSize(QSize(20, 20))
        self.botao_play.setText("")

    def atualizar_icone_volume(self, valor: int):
        tema = self._tema_atual()
        cor_icone = "#374151" if tema == "light" else "#e5e7eb"
        nome = "volume_mute" if valor == 0 else "volume_low" if valor < 45 else "volume_high"
        self.btn_vol_icon.setIcon(get_svg_icon(nome, color=cor_icone, size=64))
        self.btn_vol_icon.setIconSize(QSize(18, 18))
        self.btn_vol_icon.setText("")

    def _tema_atual(self):
        return self._theme

    def atualizar_posicao(self, position: int):
        self.slider_progresso.setValue(position)
        self.atualizar_tempo()

    def atualizar_duracao(self, duration: int):
        self.slider_progresso.setRange(0, duration)
        self.atualizar_tempo()

    def atualizar_tempo(self):
        self.tempo_atual.setText(self.formatar_tempo(self.playback.position()))
        self.tempo_total.setText(self.formatar_tempo(self.playback.duration()))

    @staticmethod
    def formatar_tempo(milliseconds: int) -> str:
        segundos = milliseconds // 1000
        minutos = segundos // 60
        segundos %= 60
        return f"{minutos:02d}:{segundos:02d}"

    def atualizar_faixa(self, track):
        if track is None:
            return
        self.titulo_musica.setText(self._limitar_texto(track.title, 34))
        self.artista_musica.setText(
            self._limitar_texto(track.artist if track.artist else "Artista desconhecido", 30)
        )
        self.album_musica.setText(
            self._limitar_texto(track.album if track.album else "Álbum desconhecido", 30)
        )

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

        self.limpar_capa()

    def limpar_faixa(self):
        self.titulo_musica.setText("Nenhuma música selecionada")
        self.artista_musica.setText("Artista")
        self.album_musica.setText("Álbum")
        self.limpar_capa()
        self.slider_progresso.setRange(0, 0)
        self.tempo_atual.setText("00:00")
        self.tempo_total.setText("00:00")

    def limpar_capa(self):
        self.capa.clear()
        self.capa.setText("CAPA")

    @staticmethod
    def _limitar_texto(texto: str, limite: int) -> str:
        if len(texto) <= limite:
            return texto
        return texto[:max(1, limite - 3)].rstrip() + "..."
