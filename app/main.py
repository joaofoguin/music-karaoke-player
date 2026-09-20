import sys
from pathlib import Path

from PySide6.QtCore import Qt
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
from widgets.queue_widget import QueueWidget
from widgets.player_widget import PlayerWidget
from widgets.explorer_widget import ExplorerWidget
from widgets.main_menu import MainMenu
from widgets.main_content_widget import MainContentWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Music Player")
        self.resize(1200, 720)
        self.setMinimumSize(900, 560)

        self.config_manager = ConfigManager()
        self.queue_controller = QueueController()
        self.audio_engine = PlaybackController()
        self.playback_coordinator = PlaybackCoordinator(self.audio_engine, self.queue_controller)
        self.playback_coordinator.track_changed.connect(self._ao_mudar_faixa)
        self.karaoke_window = None
        self.karaoke_editor = None
        self._volume_anterior_mudo = None

        self.config_manager.settings_changed.connect(self.aplicar_configuracoes)

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
        self.audio_extensions = set(
            self.config_manager.get(
                "playback/audio_extensions",
                [".mp3", ".wav", ".flac", ".ogg", ".opus", ".m4a", ".aac", ".wma"],
            )
        )
        self.track_loader.set_audio_extensions(self.audio_extensions)
        self.explorer_widget.set_audio_extensions(self.audio_extensions)
        self.aplicar_estilo()

    def aplicar_estilo(self):
        tema = self.config_manager.get("appearance/theme", "dark")
        self.setStyleSheet(ThemeManager.obter_tema_qss(tema))
        self.atualizar_icones()

    def atualizar_icones(self):
        """Atualiza os ícones dos componentes visuais da janela."""
        tema = self.config_manager.get("appearance/theme", "dark")
        cor_icone = "#374151" if tema == "light" else "#e5e7eb"

        self.player_widget.atualizar_icones(tema)
        self.explorer_widget.atualizar_icones(tema)

        if hasattr(self, "btn_add_arquivos"):
            self.btn_add_arquivos.setIcon(get_svg_icon("plus", color=cor_icone, size=64))
        if hasattr(self, "botao_limpar_fila"):
            self.botao_limpar_fila.setIcon(get_svg_icon("trash", color=cor_icone, size=64))

    def atualizar_botao_play(self):
        self.player_widget.atualizar_botao_play()

    def atualizar_icone_volume(self, valor: int):
        self.player_widget.atualizar_icone_volume(valor)

    def criar_interface(self):
        self.main_menu = MainMenu(self)
        self.main_menu.open_files_requested.connect(self.abrir_arquivos_dialogo)
        self.main_menu.open_folder_requested.connect(self.abrir_pasta_dialogo)
        self.main_menu.exit_requested.connect(self.close)
        self.main_menu.clear_queue_requested.connect(self.limpar_fila)
        self.main_menu.remove_current_requested.connect(self.remover_faixa_atual)
        self.main_menu.karaoke_requested.connect(self.abrir_tela_karaoke)
        self.main_menu.fullscreen_requested.connect(self.alternar_tela_cheia)
        self.main_menu.karaoke_editor_requested.connect(self.abrir_editor_karaoke)
        self.main_menu.play_pause_requested.connect(self.alternar_reproducao)
        self.main_menu.previous_requested.connect(self.faixa_anterior)
        self.main_menu.next_requested.connect(self.faixa_proxima)
        self.main_menu.volume_up_requested.connect(self.aumentar_volume)
        self.main_menu.volume_down_requested.connect(self.diminuir_volume)
        self.main_menu.mute_requested.connect(self.alternar_mudo)
        self.main_menu.repeat_requested.connect(self.alternar_repetir)
        self.main_menu.preferences_requested.connect(self.abrir_dialogo_configuracoes)
        self.main_menu.shortcuts_requested.connect(self.mostrar_atalhos)
        self.main_menu.about_requested.connect(self.mostrar_sobre)
        self.setMenuBar(self.main_menu)

        self.main_content = MainContentWidget(
            self.audio_engine,
            self.queue_controller,
            self.audio_extensions,
            self.config_manager,
            self,
        )
        self.main_content.open_files_requested.connect(self.abrir_arquivos_dialogo)
        self.main_content.open_folder_requested.connect(self.abrir_pasta_dialogo)
        self.main_content.file_selected.connect(self.arquivo_selecionado)
        self.main_content.play_requested.connect(self.selecionar_e_reproduzir_faixa)
        self.main_content.play_next_requested.connect(self.definir_tocar_a_seguir)
        self.main_content.move_requested.connect(self.mover_faixa)
        self.main_content.remove_requested.connect(self.remover_faixa)
        self.main_content.clear_requested.connect(self.limpar_fila)
        self.main_content.previous_requested.connect(self.faixa_anterior)
        self.main_content.play_pause_requested.connect(self.alternar_reproducao)
        self.main_content.next_requested.connect(self.faixa_proxima)
        self.main_content.repeat_changed.connect(self._on_repeat_clicked)
        self.main_content.karaoke_requested.connect(self.abrir_tela_karaoke)
        self.main_content.mute_requested.connect(self.alternar_mudo)
        self.main_content.volume_changed.connect(self._on_volume_changed)
        self.main_content.karaoke_position_changed.connect(self.atualizar_karaoke_posicao)

        self.explorer_widget = self.main_content.explorer_widget
        self.queue_widget = self.main_content.queue_widget
        self.player_widget = self.main_content.player_widget

        self.btn_add_arquivos = self.main_content.btn_add_arquivos
        self.botao_limpar_fila = self.main_content.botao_limpar_fila
        self.queue_scroll = self.main_content.queue_scroll
        self.queue_content = self.main_content.queue_content
        self.queue_layout = self.main_content.queue_layout

        self.capa = self.main_content.capa
        self.titulo_musica = self.main_content.titulo_musica
        self.artista_musica = self.main_content.artista_musica
        self.album_musica = self.main_content.album_musica
        self.botao_anterior = self.main_content.botao_anterior
        self.botao_play = self.main_content.botao_play
        self.botao_proximo = self.main_content.botao_proximo
        self.botao_repetir = self.main_content.botao_repetir
        self.slider_progresso = self.main_content.slider_progresso
        self.tempo_atual = self.main_content.tempo_atual
        self.tempo_total = self.main_content.tempo_total
        self.botao_karaoke = self.main_content.botao_karaoke
        self.btn_vol_icon = self.main_content.btn_vol_icon
        self.volume = self.main_content.volume

        self.setCentralWidget(self.main_content)

    def carregar_estado_inicial(self):
        """Carrega pasta padrão, volume e modo de repetição das configurações."""
        # Volume
        remember_vol = self.config_manager.get("playback/remember_volume", True)
        if remember_vol:
            vol = self.config_manager.get("playback/last_volume", 80)
        else:
            vol = self.config_manager.get("playback/default_volume", 80)
        self.volume.setValue(vol)
        self.audio_engine.set_volume(vol)
        self.atualizar_icone_volume(vol)

        # Repetir
        repeat_def = self.config_manager.get("playback/repeat_enabled", False)
        self.botao_repetir.setChecked(repeat_def)
        self.playback_coordinator.repeat = repeat_def

        # Diretório do explorador
        restaurar = self.config_manager.get("general/restore_last_folder", True)
        pasta = ""
        if restaurar:
            pasta = self.config_manager.get("general/last_opened_folder", "")
        if not pasta or not Path(pasta).is_dir():
            pasta = self.config_manager.get("general/default_music_dir", "")

        if pasta and Path(pasta).is_dir():
            self.definir_diretorio_explorador(pasta)

    def definir_diretorio_explorador(self, pasta: str):
        if Path(pasta).is_dir():
            self.explorer_widget.definir_diretorio(pasta)

    def _on_repeat_clicked(self, checked=None):
        ativo = self.botao_repetir.isChecked() if checked is None else checked
        self.playback_coordinator.repeat = ativo
        self.config_manager.set("playback/repeat_enabled", ativo)

    def _on_volume_changed(self, valor):
        self.audio_engine.set_volume(valor)
        self.config_manager.set("playback/last_volume", valor)
        self.atualizar_icone_volume(valor)

    # ==================================================
    # DIÁLOGOS E MENUS
    # ==================================================

    def abrir_editor_karaoke(self):
        """Abre a janela do Editor de Karaoke e Cifras sincronizada com a faixa atual."""
        if self.karaoke_editor is None:
            self.karaoke_editor = KaraokeEditorWindow(self.audio_engine, self.config_manager)

        faixa_atual = self.queue_controller.current()
        if faixa_atual is not None:
            self.karaoke_editor.carregar_faixa(faixa_atual)

        self.karaoke_editor.show()
        self.karaoke_editor.raise_()
        self.karaoke_editor.activateWindow()

    def abrir_dialogo_configuracoes(self):
        dialog = SettingsDialog(self.config_manager, self)
        if dialog.exec():
            self.aplicar_configuracoes()

    def abrir_arquivos_dialogo(self):
        filtro_exts = " ".join(f"*{ext}" for ext in sorted(self.audio_extensions))
        filtro = f"Arquivos de Áudio ({filtro_exts});;Todos os Arquivos (*.*)"
        caminhos, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar Arquivos de Música",
            self.config_manager.get("general/last_opened_folder", "") or str(Path.home()),
            filtro,
        )
        if not caminhos:
            return

        primeira_adicionada = len(self.queue_controller.tracks) == 0
        for arq in caminhos:
            self._adicionar_caminho_fila(Path(arq))

        if primeira_adicionada and self.queue_controller.tracks:
            self.selecionar_faixa(0)
            if self.config_manager.get("playback/auto_play_on_add", False):
                self.audio_engine.play()

    def abrir_pasta_dialogo(self):
        pasta = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Pasta de Músicas",
            self.config_manager.get("general/last_opened_folder", "") or str(Path.home()),
        )
        if not pasta:
            return

        self.definir_diretorio_explorador(pasta)

    def alternar_tela_cheia(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def alternar_repetir(self):
        self.botao_repetir.setChecked(not self.botao_repetir.isChecked())
        self._on_repeat_clicked()

    def aumentar_volume(self):
        novo = min(100, self.volume.value() + 5)
        self.volume.setValue(novo)

    def diminuir_volume(self):
        novo = max(0, self.volume.value() - 5)
        self.volume.setValue(novo)

    def alternar_mudo(self):
        if self.volume.value() > 0:
            self._volume_anterior_mudo = self.volume.value()
            self.volume.setValue(0)
        else:
            restaurar = self._volume_anterior_mudo if self._volume_anterior_mudo else 50
            self.volume.setValue(restaurar)

    def mostrar_atalhos(self):
        texto = """
        <h3>Atalhos do Teclado</h3>
        <table>
            <tr><td><b>Espaço</b></td><td>Reproduzir / Pausar</td></tr>
            <tr><td><b>Ctrl + Right</b></td><td>Próxima faixa</td></tr>
            <tr><td><b>Ctrl + Left</b></td><td>Faixa anterior / Recomeçar</td></tr>
            <tr><td><b>Ctrl + Up / Down</b></td><td>Aumentar / Diminuir volume</td></tr>
            <tr><td><b>Ctrl + M</b></td><td>Alternar mudo</td></tr>
            <tr><td><b>Ctrl + R</b></td><td>Alternar repetição de faixa</td></tr>
            <tr><td><b>Ctrl + K</b></td><td>Abrir tela de Karaoke</td></tr>
            <tr><td><b>Ctrl + E</b></td><td>Abrir Editor de Karaoke e Cifras</td></tr>
            <tr><td><b>Ctrl + O</b></td><td>Abrir arquivo(s) de áudio</td></tr>
            <tr><td><b>Ctrl + Shift + O</b></td><td>Abrir pasta de músicas</td></tr>
            <tr><td><b>Ctrl + L</b></td><td>Limpar fila de reprodução</td></tr>
            <tr><td><b>Ctrl + ,</b></td><td>Abrir Configurações / Preferências</td></tr>
            <tr><td><b>F11</b></td><td>Alternar tela cheia</td></tr>
            <tr><td><b>Ctrl + Q</b></td><td>Sair do aplicativo</td></tr>
        </table>
        """
        QMessageBox.information(self, "Atalhos do Teclado", texto)

    def mostrar_sobre(self):
        texto = """
        <h3>Music Player</h3>
        <p>Um reprodutor de áudio moderno e elegante desenvolvido com Python e PySide6 (Qt).</p>
        <p><b>Recursos:</b></p>
        <ul>
            <li>Suporte a múltiplos formatos (MP3, FLAC, M4A, OGG, WAV, etc.)</li>
            <li>Editor completo de Karaoke com frases limpas e suporte a cifras</li>
            <li>Pasta centralizada para salvar e gerenciar letras sem poluir pastas de álbuns</li>
            <li>Leitor avançado de tags e capas embutidas</li>
            <li>Fila dinâmica com duplo clique para reproduzir e recurso 'Tocar a Seguir'</li>
        </ul>
        """
        QMessageBox.about(self, "Sobre o Music Player", texto)

    # ==================================================
    # REPRODUÇÃO & KARAOKE
    # ==================================================

    def abrir_tela_karaoke(self):
        if self.karaoke_window is None:
            self.karaoke_window = KaraokeWindow(self.audio_engine, self.config_manager)
            self.karaoke_window.editar_solicitado.connect(self.abrir_editor_karaoke)
            self.karaoke_window.faixa_anterior_solicitada.connect(self.faixa_anterior)
            self.karaoke_window.faixa_proxima_solicitada.connect(self.faixa_proxima)

        faixa_atual = self.queue_controller.current()
        if faixa_atual is not None:
            self.karaoke_window.atualizar_faixa(faixa_atual)
            self.karaoke_window.atualizar_posicao(self.audio_engine.position())

        self.karaoke_window.show()
        self.karaoke_window.raise_()
        self.karaoke_window.activateWindow()

    def atualizar_karaoke_posicao(self, position):
        """Atualiza a sincronização e o aviso da próxima faixa no Karaoke."""
        if self.karaoke_window is not None and self.karaoke_window.isVisible():
            self.karaoke_window.atualizar_posicao(position)

    def selecionar_faixa(self, index):
        self.playback_coordinator.select(index)

    def selecionar_e_reproduzir_faixa(self, index):
        """Seleciona e inicia a reprodução imediatamente."""
        self.playback_coordinator.select_and_play(index)

    def _ao_mudar_faixa(self, track):
        self.atualizar_fila()
        self.atualizar_player(track)
        if self.karaoke_editor is not None and self.karaoke_editor.isVisible():
            self.karaoke_editor.carregar_faixa(track)

    def definir_tocar_a_seguir(self, index: int):
        """Move a faixa escolhida para a posição seguinte à música atual e destaca em laranja."""
        self.queue_controller.set_play_next(index)

    def _adicionar_caminho_fila(self, caminho: Path):
        track = self.track_loader.carregar(caminho)
        if track is not None:
            self.queue_controller.add(track)

    def definir_modo_exibicao(self, modo: str):
        self.explorer_widget.definir_modo_exibicao(modo)

    def arquivo_selecionado(self, caminho):
        fila_estava_vazia = not self.queue_controller.tracks
        self._adicionar_caminho_fila(caminho)

        if fila_estava_vazia and self.queue_controller.tracks:
            self.selecionar_faixa(0)
            if self.config_manager.get("playback/auto_play_on_add", False):
                self.audio_engine.play()

    def atualizar_player(self, track):
        if track is None:
            return

        self.player_widget.atualizar_faixa(track)

        if self.karaoke_window is not None:
            self.karaoke_window.atualizar_faixa(track)
            indice_atual = self.queue_controller.current_index
            proxima = None
            if indice_atual >= 0 and indice_atual + 1 < len(self.queue_controller.tracks):
                proxima = self.queue_controller.tracks[indice_atual + 1]
            self.karaoke_window.definir_proxima_faixa(proxima)

    def atualizar_fila(self):
        self.queue_widget.atualizar_fila()

    def mover_faixa(self, index, destino):
        self.queue_controller.move(index, destino)

    def remover_faixa(self, index):
        faixa_atual = self.queue_controller.current_index
        estava_reproduzindo = self.audio_engine.is_playing()
        removeu_atual = index == faixa_atual

        if self.queue_controller.remove(index) is None:
            return

        if removeu_atual:
            self.audio_engine.stop()
            nova_atual = self.queue_controller.current()
            if nova_atual is None:
                self.limpar_player()
            else:
                self.audio_engine.load(nova_atual.path)
                self.atualizar_player(nova_atual)
                if estava_reproduzindo:
                    self.audio_engine.play()

        self.queue_widget.atualizar_fila()

    def remover_faixa_atual(self):
        if self.queue_controller.current_index >= 0:
            self.remover_faixa(self.queue_controller.current_index)

    def limpar_fila(self):
        self.audio_engine.stop()
        self.queue_controller.clear()
        self.limpar_player()

    def limpar_player(self):
        self.player_widget.limpar_faixa()

        if self.karaoke_window is not None:
            self.karaoke_window.limpar()

        if self.karaoke_editor is not None:
            self.karaoke_editor.carregar_faixa(None)

    def faixa_anterior(self):
        self.playback_coordinator.previous()

    def faixa_proxima(self):
        self.playback_coordinator.next()

    def alternar_reproducao(self):
        self.playback_coordinator.toggle_playback()

    def formatar_duracao(self, segundos):
        segundos = int(segundos)
        minutos = segundos // 60
        segundos = segundos % 60
        return f"{minutos:02d}:{segundos:02d}"

    def closeEvent(self, event):
        """Salva configurações e encerra recursos ao fechar o player."""
        if self.config_manager.get("playback/remember_volume", True):
            self.config_manager.set("playback/last_volume", self.volume.value())

        if self.karaoke_window is not None:
            self.karaoke_window.close()

        if self.karaoke_editor is not None:
            self.karaoke_editor.close()

        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()