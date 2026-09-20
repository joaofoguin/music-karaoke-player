from core.theme_manager import ThemeManager


def test_theme_manager_returns_styles_for_supported_themes():
    for tema in ("dark", "light", "midnight"):
        qss = ThemeManager.obter_tema_qss(tema)
        assert "QMainWindow" in qss
        assert "QPushButton" in qss


def test_theme_manager_uses_dark_style_as_fallback():
    assert ThemeManager.obter_tema_qss("unknown") == ThemeManager.obter_tema_qss("dark")
