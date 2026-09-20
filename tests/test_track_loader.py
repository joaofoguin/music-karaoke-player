from pathlib import Path

from core.track_loader import TrackLoader


def _metadados(caminho):
    return {
        "title": caminho.stem,
        "artist": "Artista",
        "album": "Álbum",
        "cover": b"capa",
        "format": caminho.suffix.lower().lstrip("."),
        "duration": 123.5,
    }


def test_track_loader_cria_track_com_metadados(tmp_path):
    caminho = tmp_path / "musica.MP3"
    caminho.write_bytes(b"audio")

    loader = TrackLoader([".mp3"], _metadados)
    track = loader.carregar(caminho)

    assert track is not None
    assert track.path == caminho
    assert track.title == "musica"
    assert track.artist == "Artista"
    assert track.album == "Álbum"
    assert track.cover == b"capa"
    assert track.format == "mp3"
    assert track.duration == 123.5


def test_track_loader_ignora_extensao_nao_suportada(tmp_path):
    caminho = tmp_path / "arquivo.txt"
    caminho.write_text("texto")

    loader = TrackLoader([".mp3"], _metadados)

    assert loader.carregar(caminho) is None


def test_track_loader_ignora_caminho_inexistente(tmp_path):
    loader = TrackLoader([".mp3"], _metadados)

    assert loader.carregar(tmp_path / "inexistente.mp3") is None


def test_track_loader_atualiza_extensoes():
    loader = TrackLoader([".mp3"], _metadados)

    loader.set_audio_extensions([".flac", ".OGG"])

    assert loader.audio_extensions == {".flac", ".ogg"}
