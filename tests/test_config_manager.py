from pathlib import Path
import sys

from PySide6.QtCore import QCoreApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from core.config_manager import ConfigManager


def test_config_manager_defaults():
    # Cria uma aplicação Qt se não existir
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])

    cm = ConfigManager(organization="TestMusicPlayerOrg", application="TestAppDefaults")
    cm.reset_to_defaults()

    assert cm.get("playback/default_volume") == 80
    assert cm.get("appearance/theme") == "dark"
    assert cm.get("karaoke/font_size") == 26
    assert isinstance(cm.get("playback/audio_extensions"), list)
    assert ".mp3" in cm.get("playback/audio_extensions")


def test_config_manager_set_and_get():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])

    cm = ConfigManager(organization="TestMusicPlayerOrg", application="TestAppCustom")
    cm.set("playback/default_volume", 45)
    cm.set("appearance/theme", "midnight")
    cm.set("playback/repeat_enabled", True)

    assert cm.get("playback/default_volume") == 45
    assert cm.get("appearance/theme") == "midnight"
    assert cm.get("playback/repeat_enabled") is True


def test_config_manager_update_multiple():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])

    cm = ConfigManager(organization="TestMusicPlayerOrg", application="TestAppMultiple")
    sinal_recebido = []
    cm.settings_changed.connect(lambda: sinal_recebido.append(True))

    cm.update_multiple({
        "karaoke/font_size": 32,
        "karaoke/highlight_color": "#00ff00",
    })

    assert cm.get("karaoke/font_size") == 32
    assert cm.get("karaoke/highlight_color") == "#00ff00"
    assert len(sinal_recebido) == 1
