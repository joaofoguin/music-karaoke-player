import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from widgets.explorer_widget import ExplorerWidget


def _app():
    return QApplication.instance() or QApplication([])


def test_explorer_widget_initializes_with_details_view():
    _app()
    widget = ExplorerWidget([".mp3", ".flac"])

    assert widget.file_stack.currentWidget() is widget.file_tree
    assert widget.file_list.viewMode().name == "IconMode" or widget.file_stack.currentWidget() is widget.file_tree


def test_explorer_widget_changes_display_modes():
    _app()
    widget = ExplorerWidget([".mp3"])

    widget.definir_modo_exibicao("list")
    assert widget.file_stack.currentWidget() is widget.file_list
    assert widget.file_list.viewMode().name == "ListMode"
    assert widget.file_list.iconSize().width() == 20

    widget.definir_modo_exibicao("small")
    assert widget.file_list.viewMode().name == "IconMode"
    assert widget.file_list.iconSize().width() == 32

    widget.definir_modo_exibicao("large")
    assert widget.file_list.iconSize().width() == 64

    widget.definir_modo_exibicao("details")
    assert widget.file_stack.currentWidget() is widget.file_tree


def test_explorer_widget_emits_only_supported_files(tmp_path):
    _app()
    widget = ExplorerWidget([".mp3"])

    selected = []
    widget.file_selected.connect(selected.append)

    audio = tmp_path / "song.mp3"
    text = tmp_path / "notes.txt"
    audio.write_bytes(b"")
    text.write_text("notes", encoding="utf-8")

    widget.definir_diretorio(str(tmp_path))
    root = widget.file_model.index(str(tmp_path))

    for row in range(widget.file_model.rowCount(root)):
        index = widget.file_model.index(row, 0, root)
        widget._arquivo_selecionado(index)

    assert selected == [audio]


def test_explorer_widget_changes_directory(tmp_path):
    _app()
    widget = ExplorerWidget([".mp3"])

    changed = []
    widget.directory_changed.connect(changed.append)

    widget.definir_diretorio(str(tmp_path))

    assert changed == [str(tmp_path)]
    assert widget.file_tree.rootIndex() == widget.file_model.index(str(tmp_path))
    assert widget.file_list.rootIndex() == widget.file_model.index(str(tmp_path))
