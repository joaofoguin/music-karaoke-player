from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from widgets.explorer_widget import ExplorerWidget
from widgets.player_widget import PlayerWidget
from widgets.queue_widget import QueueWidget


class MainContentWidget(QFrame):
    """Composição visual principal do player, sem regras de domínio."""

    open_files_requested = Signal()
    open_folder_requested = Signal()
    file_selected = Signal(object)
    play_requested = Signal(int)
    play_next_requested = Signal(int)
    move_requested = Signal(int, int)
    remove_requested = Signal(int)
    clear_requested = Signal()
    previous_requested = Signal()
    play_pause_requested = Signal()
    next_requested = Signal()
    repeat_changed = Signal(bool)
    karaoke_requested = Signal()
    mute_requested = Signal()
    volume_changed = Signal(int)
    karaoke_position_changed = Signal(int)

    def __init__(self, audio_engine, queue_controller, audio_extensions, config_manager, parent=None):
        super().__init__(parent)
        self.audio_engine = audio_engine
        self.queue_controller = queue_controller
        self.audio_extensions = set(audio_extensions or [])
        self.config_manager = config_manager
        self._build_ui()

    def _build_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(18, 18, 18, 18)
        layout_principal.setSpacing(12)

        layout_superior = QHBoxLayout()
        layout_superior.setSpacing(16)

        self.explorer_widget = ExplorerWidget(self.audio_extensions, self)
        self.explorer_widget.set_open_folder_callback(self.open_folder_requested.emit)
        self.explorer_widget.file_selected.connect(self.file_selected)
        self.explorer_widget.directory_changed.connect(
            lambda pasta: self.config_manager.set("general/last_opened_folder", pasta)
        )

        self.queue_widget = QueueWidget(self.queue_controller, self)
        self.queue_widget.set_add_files_callback(self.open_files_requested.emit)
        self.queue_widget.play_requested.connect(self.play_requested)
        self.queue_widget.play_next_requested.connect(self.play_next_requested)
        self.queue_widget.move_requested.connect(self.move_requested)
        self.queue_widget.remove_requested.connect(self.remove_requested)
        self.queue_widget.clear_requested.connect(self.clear_requested)

        self.btn_add_arquivos = self.queue_widget.btn_add_arquivos
        self.botao_limpar_fila = self.queue_widget.botao_limpar_fila
        self.queue_scroll = self.queue_widget.queue_scroll
        self.queue_content = self.queue_widget.queue_content
        self.queue_layout = self.queue_widget.queue_layout

        self.player_widget = PlayerWidget(self.audio_engine)
        self.player_widget.previous_requested.connect(self.previous_requested)
        self.player_widget.play_requested.connect(self.play_pause_requested)
        self.player_widget.next_requested.connect(self.next_requested)
        self.player_widget.repeat_changed.connect(self.repeat_changed)
        self.player_widget.karaoke_requested.connect(self.karaoke_requested)
        self.player_widget.mute_requested.connect(self.mute_requested)
        self.player_widget.volume_changed.connect(self.volume_changed)
        self.audio_engine.position_changed.connect(self.karaoke_position_changed)

        self.capa = self.player_widget.capa
        self.titulo_musica = self.player_widget.titulo_musica
        self.artista_musica = self.player_widget.artista_musica
        self.album_musica = self.player_widget.album_musica
        self.botao_anterior = self.player_widget.botao_anterior
        self.botao_play = self.player_widget.botao_play
        self.botao_proximo = self.player_widget.botao_proximo
        self.botao_repetir = self.player_widget.botao_repetir
        self.slider_progresso = self.player_widget.slider_progresso
        self.tempo_atual = self.player_widget.tempo_atual
        self.tempo_total = self.player_widget.tempo_total
        self.botao_karaoke = self.player_widget.botao_karaoke
        self.btn_vol_icon = self.player_widget.btn_vol_icon
        self.volume = self.player_widget.volume

        layout_superior.addWidget(self.explorer_widget, 1)
        layout_superior.addWidget(self.queue_widget, 1)
        layout_principal.addLayout(layout_superior, 5)
        layout_principal.addWidget(self.player_widget, 1)

    def set_audio_extensions(self, extensions):
        self.audio_extensions = set(extensions or [])
        self.explorer_widget.set_audio_extensions(self.audio_extensions)
