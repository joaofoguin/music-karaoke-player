from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMenuBar


class MainMenu(QMenuBar):
    """Menu principal do player, isolando a definição das ações da MainWindow."""

    open_files_requested = Signal()
    open_folder_requested = Signal()
    exit_requested = Signal()
    clear_queue_requested = Signal()
    remove_current_requested = Signal()
    karaoke_requested = Signal()
    fullscreen_requested = Signal()
    karaoke_editor_requested = Signal()
    audio_effects_requested = Signal()
    play_pause_requested = Signal()
    previous_requested = Signal()
    next_requested = Signal()
    volume_up_requested = Signal()
    volume_down_requested = Signal()
    mute_requested = Signal()
    repeat_requested = Signal()
    preferences_requested = Signal()
    shortcuts_requested = Signal()
    about_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._criar_menus()

    def _criar_menus(self):
        menu_arquivo = self.addMenu("&Arquivo")
        self._adicionar_acao(menu_arquivo, "Abrir Arquivo(s)...", "Ctrl+O", self.open_files_requested)
        self._adicionar_acao(menu_arquivo, "Abrir Pasta...", "Ctrl+Shift+O", self.open_folder_requested)
        menu_arquivo.addSeparator()
        self._adicionar_acao(menu_arquivo, "Sair", "Ctrl+Q", self.exit_requested)

        menu_editar = self.addMenu("&Editar")
        self._adicionar_acao(menu_editar, "Limpar Fila", "Ctrl+L", self.clear_queue_requested)
        self._adicionar_acao(menu_editar, "Remover Faixa Atual", None, self.remove_current_requested)

        menu_exibir = self.addMenu("&Exibir")
        self._adicionar_acao(menu_exibir, "Abrir Tela de Karaoke", "Ctrl+K", self.karaoke_requested)
        self._adicionar_acao(menu_exibir, "Alternar Tela Cheia", "F11", self.fullscreen_requested)

        menu_ferramentas = self.addMenu("&Ferramentas")
        self._adicionar_acao(menu_ferramentas, "Editor de Karaoke e Cifras...", "Ctrl+E", self.karaoke_editor_requested)
        self._adicionar_acao(menu_ferramentas, "Ajustes e Efeitos de Áudio...", "Ctrl+Shift+A", self.audio_effects_requested)

        menu_controles = self.addMenu("&Controles")
        self._adicionar_acao(menu_controles, "Reproduzir / Pausar", "Space", self.play_pause_requested)
        self._adicionar_acao(menu_controles, "Faixa Anterior", "Ctrl+Left", self.previous_requested)
        self._adicionar_acao(menu_controles, "Próxima Faixa", "Ctrl+Right", self.next_requested)
        menu_controles.addSeparator()
        self._adicionar_acao(menu_controles, "Aumentar Volume", "Ctrl+Up", self.volume_up_requested)
        self._adicionar_acao(menu_controles, "Diminuir Volume", "Ctrl+Down", self.volume_down_requested)
        self._adicionar_acao(menu_controles, "Alternar Mudo", "Ctrl+M", self.mute_requested)
        self._adicionar_acao(menu_controles, "Repetir Faixa Atual", "Ctrl+R", self.repeat_requested)

        menu_config = self.addMenu("&Configurações")
        self._adicionar_acao(menu_config, "Preferências...", "Ctrl+,", self.preferences_requested)

        menu_ajuda = self.addMenu("&Ajuda")
        self._adicionar_acao(menu_ajuda, "Atalhos do Teclado", None, self.shortcuts_requested)
        self._adicionar_acao(menu_ajuda, "Sobre o Music Player", None, self.about_requested)

    @staticmethod
    def _adicionar_acao(menu, texto, atalho, sinal):
        acao = QAction(texto, menu)
        if atalho:
            acao.setShortcut(QKeySequence(atalho))
        acao.triggered.connect(lambda _checked=False: sinal.emit())
        menu.addAction(acao)
