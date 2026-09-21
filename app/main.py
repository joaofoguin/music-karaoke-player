import os
import sys
from pathlib import Path

# QAudioBufferOutput (usado pelo pipeline de efeitos PCM) depende do backend FFmpeg no Qt 6.8.
os.environ.setdefault("QT_MEDIA_BACKEND", "ffmpeg")

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QStyle,
    QToolButton,
    QWidget,
)

from core.queue_controller import QueueController
from core.playback_controller import PlaybackController
from core.playback_coordinator import PlaybackCoordinator
from core.track_loader import TrackLoader
from core.config_manager import ConfigManager
from core.theme_manager import ThemeManager
from core.icons import get_svg_icon
from core.clickable_slider import ClickableSlider
from karaoke_window import KaraokeWindow
from karaoke_editor import KaraokeEditorWindow
from settings_dialog import SettingsDialog
from audio_effects_dialog import AudioEffectsDialog
from widgets.queue_widget import QueueWidget
from widgets.player_widget import PlayerWidget
from widgets.explorer_widget import ExplorerWidget
from widgets.main_menu import MainMenu
from widgets.main_content_widget import MainContentWidget
from core.branding import APP_DISPLAY_NAME, load_branding, resource_path, set_interface_font_size


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setWindowIcon(QIcon(str(resource_path("assets/logo.svg"))))
        self.resize(1200, 720)
        self.setMinimumSize(900, 560)

        self.config_manager = ConfigManager()
        self.queue_controller = QueueController()
        self.audio_engine = PlaybackController()
        self.audio_engine.set_configured_output_device_id(
            self.config_manager.get("audio/output_device_id", "")
        )
        self.audio_engine.set_output_device(
            self.config_manager.get("audio/output_device_id", "")
        )
        self.audio_engine.set_gain_db(
            self.config_manager.get("audio/effects/gain_db", 0.0)
        )
        self.audio_engine.set_normalize_enabled(
            self.config_manager.get("audio/effects/normalize_enabled", False)
        )
        self.audio_engine.set_mono_enabled(
            self.config_manager.get("audio/effects/mono_enabled", False)
        )
        self.audio_engine.set_noise_reduction_settings(
            self.config_manager.get("audio/effects/noise_threshold_db", -45.0),
            self.config_manager.get("audio/effects/noise_reduction_db", 18.0),
        )
        self.audio_engine.set_noise_reduction_enabled(
            self.config_manager.get("audio/effects/noise_reduction_enabled", False)
        )
        self.audio_engine.set_equalizer_settings(
            self.config_manager.get("audio/effects/equalizer_bass_db", 0.0),
            self.config_manager.get("audio/effects/equalizer_mid_db", 0.0),
            self.config_manager.get("audio/effects/equalizer_treble_db", 0.0),
        )
        self.audio_engine.set_equalizer_enabled(
            self.config_manager.get("audio/effects/equalizer_enabled", False)
        )
        self.audio_engine.set_reverb_delay_settings(
            self.config_manager.get("audio/effects/reverb_delay_ms", 120.0),
            self.config_manager.get("audio/effects/reverb_feedback", 0.35),
            self.config_manager.get("audio/effects/reverb_mix", 0.25),
        )
        self.audio_engine.set_reverb_delay_enabled(
            self.config_manager.get("audio/effects/reverb_delay_enabled", False)
        )
        self.playback_coordinator = PlaybackCoordinator(self.audio_engine, self.queue_controller)
        self.playback_coordinator.track_changed.connect(self._ao_mudar_faixa)
        self.karaoke_window = None
        self.karaoke_editor = None
        self.audio_effects_dialog = None
        self._volume_anterior_mudo = None

        self.config_manager.settings_changed.connect(
            self.aplicar_configuracoes,
            Qt.ConnectionType.QueuedConnection,
        )

        self.audio_extensions = set(
            self.config_manager.get(
                "playback/audio_extensions",
                [".mp3", ".wav", ".flac", ".ogg", ".opus", ".m4a", ".aac", ".wma"],
            )
        )
        self.track_loader = TrackLoader(self.audio_extensions)

        self.criar_interface()
        self.aplicar_estilo()
        self.carregar_estado_inicial()

    def aplicar_configuracoes(self):
        """Atualiza o comportamento e aparência do player conforme as configurações salvas."""
        # Aplica primeiro as mudanças visuais para que o usuário veja o resultado
        # imediatamente ao salvar, antes das reconfigurações de áudio.
        self.aplicar_estilo()

        self.audio_extensions = set(
            self.config_manager.get(
                "playback/audio_extensions",
                [".mp3", ".wav", ".flac", ".ogg", ".opus", ".m4a", ".aac", ".wma"],
            )