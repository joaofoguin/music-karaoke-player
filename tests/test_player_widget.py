import sys
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from models.track import Track
from widgets.player_widget import PlayerWidget


class FakePlayback(QObject):
    position_changed = Signal(int)
    duration_changed = Signal(int)
    playback_started = Signal()
    playback_paused = Signal()
    playback_stopped = Signal()
    playback_finished = Signal()

    def __init__(self):
        super().__init__()
        self.calls = []
        self._position = 0
        self._duration = 0
        self._playing = False

    def play(self):
        self.calls.append(("play",))
        self._playing = True
        self.playback_started.emit()

    def pause(self):
        self.calls.append(("pause",))
        self._playing = False
        self.playback_paused.emit()

    def stop(self):
        self.calls.append(("stop",))
        self._playing = False
        self.playback_stopped.emit()

    def set_position(self, position):
        self.calls.append(("set_position", position))
        self._position = position

    def set_volume(self, volume):
        self.calls.append(("set_volume", volume))

    def position(self):
        return self._position

    def duration(self):
        return self._duration

    def is_playing(self):
        return self._playing


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


@pytest.fixture
def playback():
    return FakePlayback()


@pytest.fixture
def widget(qapp, playback):
    player = PlayerWidget(playback)
    yield player
    player.deleteLater()
    qapp.processEvents()


def test_formatar_tempo(widget):
    assert widget.formatar_tempo(0) == "00:00"
    assert widget.formatar_tempo(65_000) == "01:05"
    assert widget.formatar_tempo(3_661_000) == "61:01"


def test_limitar_texto(widget):
    assert widget._limitar_texto("Artista", 10) == "Artista"
    assert widget._limitar_texto("Nome de uma música muito longa", 10) == "Nome de..."


def test_player_buttons_emit_requests(widget):
    events = []
    widget.previous_requested.connect(lambda: events.append("previous"))
    widget.play_requested.connect(lambda: events.append("play"))
    widget.next_requested.connect(lambda: events.append("next"))
    widget.karaoke_requested.connect(lambda: events.append("karaoke"))
    widget.mute_requested.connect(lambda: events.append("mute"))

    widget.botao_anterior.click()
    widget.botao_play.click()
    widget.botao_proximo.click()
    widget.botao_karaoke.click()
    widget.btn_vol_icon.click()

    assert events == ["previous", "play", "next", "karaoke", "mute"]


def test_repeat_button_emits_checked_state(widget):
    states = []
    widget.repeat_changed.connect(states.append)

    widget.botao_repetir.setChecked(True)
    widget.botao_repetir.setChecked(False)

    assert states == [True, False]


def test_volume_changes_are_forwarded(widget, playback):
    values = []
    widget.volume_changed.connect(values.append)

    widget.volume.setValue(35)
    widget.volume.clicked_position.emit(70)

    assert values == [35, 70]


def test_progress_position_is_forwarded(widget, playback):
    widget.slider_progresso.clicked_position.emit(12_500)

    assert playback.calls == [("set_position", 12_500)]
    assert playback.position() == 12_500


def test_playback_signals_update_progress_and_time(widget, playback):
    playback._duration = 180_000
    playback.duration_changed.emit(180_000)
    playback._position = 65_000
    playback.position_changed.emit(65_000)

    assert widget.slider_progresso.minimum() == 0
    assert widget.slider_progresso.maximum() == 180_000
    assert widget.slider_progresso.value() == 65_000
    assert widget.tempo_atual.text() == "01:05"
    assert widget.tempo_total.text() == "03:00"


def test_playback_state_updates_play_button(widget, playback):
    playback.playback_started.emit()
    assert widget.botao_play.toolTip() == "Pausar (Espaço)"

    playback.playback_paused.emit()
    assert widget.botao_play.toolTip() == "Reproduzir (Espaço)"

    playback.playback_stopped.emit()
    assert widget.botao_play.toolTip() == "Reproduzir (Espaço)"


def test_atualizar_faixa_updates_metadata(widget):
    track = Track(
        path=Path("musica.mp3"),
        title="Minha Música",
        artist="Meu Artista",
        album="Meu Álbum",
    )

    widget.atualizar_faixa(track)

    assert widget.titulo_musica.text() == "Minha Música"
    assert widget.artista_musica.text() == "Meu Artista"
    assert widget.album_musica.text() == "Meu Álbum"
    assert widget.capa.text() == "CAPA"


def test_atualizar_faixa_uses_fallback_metadata(widget):
    track = Track(path=Path("musica.mp3"), title="Minha Música")

    widget.atualizar_faixa(track)

    assert widget.artista_musica.text() == "Artista desconhecido"
    assert widget.album_musica.text() == "Álbum desconhecido"


def test_limpar_faixa_resets_player(widget, playback):
    playback._duration = 180_000
    playback.duration_changed.emit(180_000)
    playback._position = 65_000
    playback.position_changed.emit(65_000)

    widget.limpar_faixa()

    assert widget.titulo_musica.text() == "Nenhuma música selecionada"
    assert widget.artista_musica.text() == "Artista"
    assert widget.album_musica.text() == "Álbum"
    assert widget.slider_progresso.minimum() == 0
    assert widget.slider_progresso.maximum() == 0
    assert widget.tempo_atual.text() == "00:00"
    assert widget.tempo_total.text() == "00:00"
    assert widget.capa.text() == "CAPA"


def test_theme_is_preserved_when_updating_icons(widget):
    widget.atualizar_icones("light")

    assert widget._tema_atual() == "light"
