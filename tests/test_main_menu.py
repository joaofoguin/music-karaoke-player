import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from widgets.main_menu import MainMenu


def _app():
    return QApplication.instance() or QApplication([])


def test_main_menu_creates_expected_menus_and_shortcuts():
    _app()
    menu = MainMenu()

    assert [action.text() for action in menu.actions()] == [
        "&Arquivo",
        "&Editar",
        "&Exibir",
        "&Ferramentas",
        "&Controles",
        "&Configurações",
        "&Ajuda",
    ]

    arquivo = menu.actions()[0].menu()
    assert arquivo.actions()[0].text() == "Abrir Arquivo(s)..."
    assert arquivo.actions()[0].shortcut().toString() == "Ctrl+O"
    assert arquivo.actions()[1].shortcut().toString() == "Ctrl+Shift+O"
    assert arquivo.actions()[3].shortcut().toString() == "Ctrl+Q"


def test_main_menu_emits_requests():
    _app()
    menu = MainMenu()
    events = []

    menu.open_files_requested.connect(lambda: events.append("open_files"))
    menu.open_folder_requested.connect(lambda: events.append("open_folder"))
    menu.play_pause_requested.connect(lambda: events.append("play_pause"))
    menu.repeat_requested.connect(lambda: events.append("repeat"))
    menu.about_requested.connect(lambda: events.append("about"))

    menus = {action.text(): action.menu() for action in menu.actions()}
    menus["&Arquivo"].actions()[0].trigger()
    menus["&Arquivo"].actions()[1].trigger()
    menus["&Controles"].actions()[0].trigger()
    menus["&Controles"].actions()[-1].trigger()
    menus["&Ajuda"].actions()[1].trigger()

    assert events == ["open_files", "open_folder", "play_pause", "repeat", "about"]
