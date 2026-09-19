import os
from pathlib import Path
from PySide6.QtCore import QObject, QSettings, Signal


class ConfigManager(QObject):
    """Gerencia a persistência e acesso às configurações do Music Player."""

    settings_changed = Signal()

    _DEFAULT_MUSIC_DIR = str(Path.home() / "Music") if (Path.home() / "Music").exists() else ""
    _DEFAULT_KARAOKE_DIR = str(Path.home() / "Music" / "Karaoke_Lyrics")

    DEFAULT_SETTINGS = {
        "general/default_music_dir": _DEFAULT_MUSIC_DIR,
        "general/restore_last_folder": True,
        "general/last_opened_folder": "",
        "playback/default_volume": 80,
        "playback/remember_volume": True,
        "playback/last_volume": 80,
        "playback/repeat_enabled": False,
        "playback/auto_play_on_add": False,
        "playback/audio_extensions": [
            ".mp3",
            ".wav",
            ".flac",
            ".ogg",
            ".opus",
            ".m4a",
            ".aac",
            ".wma",
        ],
        "appearance/theme": "dark",  # "dark", "midnight", "light"
        "karaoke/lyrics_directory": _DEFAULT_KARAOKE_DIR,
        "karaoke/save_to_central_dir": True,
        "karaoke/show_chords": True,
        "karaoke/chords_color": "#f59e0b",
        "karaoke/font_size": 26,
        "karaoke/highlight_color": "#ffffff",
        "karaoke/context_color": "#8f8f8f",
        "karaoke/context_lines": 2,
    }

    def __init__(self, organization="MusicPlayerApp", application="MusicPlayer"):
        super().__init__()
        self.settings = QSettings(organization, application)

    def get(self, key: str, default=None):
        """Retorna o valor de uma configuração com fallback para o padrão."""
        if default is None:
            default = self.DEFAULT_SETTINGS.get(key)

        expected_type = type(default) if default is not None else str

        if not self.settings.contains(key):
            return default

        val = self.settings.value(key)

        if expected_type == bool:
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.lower() in ("true", "1", "yes")
            return bool(val)

        if expected_type == int:
            try:
                return int(val)
            except (ValueError, TypeError):
                return default

        if expected_type == float:
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        if expected_type == list:
            if isinstance(val, list):
                return val
            if isinstance(val, str):
                return [item.strip() for item in val.split(",") if item.strip()]
            return default

        return str(val) if val is not None else default

    def set(self, key: str, value):
        """Define e salva um valor de configuração."""
        self.settings.setValue(key, value)
        self.settings.sync()

    def update_multiple(self, values: dict):
        """Atualiza múltiplos valores de uma vez e emite sinal de alteração."""
        for key, value in values.items():
            self.settings.setValue(key, value)
        self.settings.sync()
        self.settings_changed.emit()

    def reset_to_defaults(self):
        """Restaura todas as configurações para os padrões de fábrica."""
        self.settings.clear()
        for key, value in self.DEFAULT_SETTINGS.items():
            self.settings.setValue(key, value)
        self.settings.sync()
        self.settings_changed.emit()
