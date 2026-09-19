from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from core.metadata_reader import ler_metadados, primeiro_valor


def test_primeiro_valor():
    assert primeiro_valor(None, "padrao") == "padrao"
    assert primeiro_valor([], "padrao") == "padrao"
    assert primeiro_valor(["Item 1", "Item 2"]) == "Item 1"
    assert primeiro_valor("Texto direto") == "Texto direto"
    assert primeiro_valor(123) == "123"


def test_ler_metadados_arquivo_inexistente():
    caminho = Path("musica_inexistente.flac")
    meta = ler_metadados(caminho)

    assert meta["title"] == "musica_inexistente"
    assert meta["artist"] == ""
    assert meta["album"] == ""
    assert meta["cover"] is None
    assert meta["format"] == "flac"
    assert meta["duration"] == 0.0
