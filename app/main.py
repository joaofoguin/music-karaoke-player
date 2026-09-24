import os
import sys
import time
from pathlib import Path

# QAudioBufferOutput (usado pelo pipeline de efeitos PCM) depende do backend FFmpeg no Qt 6.8.
os.environ.setdefault("QT_MEDIA_BACKEND", "ffmpeg")

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon
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
from audio_effects_dialog import AudioEffectsDialog
from widgets.queue_widget import QueueWidget
from widgets.player_widget import PlayerWidget
from widgets.explorer_widget import ExplorerWidget
from widgets.main_menu import MainMenu
from widgets.main_content_widget import MainContentWidget
from core.branding import APP_DISPLAY_NAME, APP_LAST_UPDATE, APP_VERSION, create_splash_screen, load_branding, resource_path, set_interface_font_size
from core.updater import UpdateChecker, UpdateDownloader, UpdateInfo, open_installer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setWindowIcon(QIcon(str(resource_path("assets/logo.svg"))))
        self.resize(1200, 720)
        self.setMinimumSize(900, 560)

        self.config_manager = ConfigManager()
        self.queue_controller = QueueController()
        self.audio_engine = PlaybackController()
        self.audio_engine.set_configured_output_device_id(
            self.config_manager.get("audio/output_device_id", "")
        )
        self.audio_engine.set_output_device(
            self.config_manager.get("audio/output_device_id", "")
        )
        self.audio_engine.set_gain_db(
            self.config_manager.get("audio/effects/gain_db", 0.0)
        )
        self.audio_engine.set_normalize_enabled(
            self.config_manager.get("audio/effects/normalize_enabled", False)
        )
        self.audio_engine.set_mono_enabled(
            self.config_manager.get("audio/effects/mono_enabled", False)
        )
        self.audio_engine.set_noise_reduction_settings(
            self.config_manager.get("audio/effects/noise_threshold_db", -45.0),
            self.config_manager.get("audio/effects/noise_reduction_db", 18.0),
        )
        self.audio_engine.set_noise_reduction_enabled(
            self.config_manager.get("audio/effects/noise_reduction_enabled", False)
        )
        self.audio_engine.set_equalizer_settings(
            self.config_manager.get("audio/effects/equalizer_bass_db", 0.0),
            self.config_manager.get("audio/effects/equalizer_mid_db", 0.0),
            self.config_manager.get("audio/effects/equalizer_treble_db", 0.0),
        )
        self.audio_engine.set_equalizer_enabled(
            self.config_manager.get("audio/effects/equalizer_enabled", False)
        )
        self.audio_engine.set_reverb_delay_settings(
            self.config_manager.get("audio/effects/reverb_delay_ms", 120.0),
            self.config_manager.get("audio/effects/reverb_feedback", 0.35),
            self.config_manager.get("audio/effects/reverb_mix", 0.25),
        )
        self.audio_engine.set_reverb_delay_enabled(
            self.config_manager.get("audio/effects/reverb_delay_enabled", False)
        )
        self.playback_coordinator = PlaybackCoordinator(self.audio_engine, self.queue_controller)
        self.playback_coordinator.track_changed.connect(self._ao_mudar_faixa)
        self.karaoke_window = None
        self.karaoke_editor = None
        self.audio_effects_dialog = None
        self._volume_anterior_mudo = None
        self._update_checker = None
        self._update_downloader = None
        self._update_info_pendente = None

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
        QTimer.singleShot(2500, self.verificar_atualizacao)
        QTimer.singleShot(500, self.verificar_atualizacao_concluida)

    def verificar_atualizacao(self):
        """Consulta novas versões Beta sem bloquear a interface."""
        if self._update_checker is not None and self._update_checker.isRunning():
            return

        self._update_checker = UpdateChecker(self)
        self._update_checker.update_available.connect(self._mostrar_atualizacao)
        self._update_checker.finished.connect(self._update_checker.deleteLater)
        self._update_checker.start()

    def _mostrar_atualizacao(self, update: UpdateInfo):
        resposta = QMessageBox.question(
            self,
            "Nova versão disponível",
            (
                f"Uma nova versão do StageBox está disponível: {update.version}.\n\n"
                f"Versão atual: {APP_VERSION}\n\n"
                "Deseja baixar e instalar a atualização agora?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if resposta != QMessageBox.Yes:
            return

        self.statusBar().showMessage("Baixando atualização...")
        self._update_info_pendente = update
        self._update_downloader = UpdateDownloader(update.installer_url, self)
        self._update_downloader.downloaded.connect(self._instalador_baixado)
        self._update_downloader.failed.connect(self._download_atualizacao_falhou)
        self._update_downloader.finished.connect(self._update_downloader.deleteLater)
        self._update_downloader.start()

    def _instalador_baixado(self, path):
        self.statusBar().clearMessage()
        try:
            open_installer(path, self._update_info_pendente)
        except OSError as exc:
            QMessageBox.warning(
                self,
                "Atualização",
                f"Não foi possível iniciar o instalador.\n\n{exc}",
            )
            return
        self.close()


    def verificar_atualizacao_concluida(self):
        """Exibe as novidades da versão após uma atualização automática."""
        if "--update-complete" not in sys.argv:
            return

        try:
            indice = sys.argv.index("--update-complete")
            marker = Path(sys.argv[indice + 1])
            import json
            dados = json.loads(marker.read_text(encoding="utf-8"))
            marker.unlink(missing_ok=True)
        except (ValueError, IndexError, OSError, json.JSONDecodeError):
            return

        versao = str(dados.get("version", "")).strip()
        notas = str(dados.get("release_notes", "")).strip()
        if not versao:
            return

        linhas = []
        for linha in notas.splitlines():
            linha = linha.strip()
            if not linha:
                continue
            if linha.startswith("### "):
                linhas.append(f"<h4>{linha[4:]}</h4>")
            elif linha.startswith("- "):
                linhas.append(f"• {linha[2:]}")
            else:
                linhas.append(linha)

        conteudo = "<br>".join(linhas) if linhas else "Nenhuma novidade detalhada foi publicada nesta versão."
        QMessageBox.information(
            self,
            "Atualização concluída",
            f"<h3>StageBox atualizado com sucesso!</h3>"
            f"<p><b>Versão:</b> {versao}</p>"
            f"<p><b>Novidades, melhorias e correções:</b></p>"
            f"<p>{conteudo}</p>",
        )

    def _download_atualizacao_falhou(self, erro: str):
        self.statusBar().clearMessage()
        QMessageBox.warning(
            self,
            "Atualização",
            "Não foi possível baixar a atualização. Verifique sua conexão e tente novamente.",
        )

    def aplicar_configuracoes(self):
        """Atualiza o comportamento e aparência do player conforme as configurações salvas."""
        # Aplica primeiro as mudanças visuais para que o usuário veja o resultado
        # imediatamente ao salvar, antes das reconfigurações de áudio.
        self.aplicar_estilo()

        self.audio_extensions = set(
            self.config_manager.get(
                "playback/audio_extensions",
                [".mp3", ".wav", ".flac", ".ogg", ".opus", ".m4a", ".aac", ".wma"],
            )
        )
        self.track_loader.set_audio_extensions(self.audio_extensions)
        self.explorer_widget.set_audio_extensions(self.audio_extensions)

        output_device_id = self.config_manager.get("audio/output_device_id", "")
        self.audio_engine.set_configured_output_device_id(output_device_id)
        if not self.audio_engine.set_output_device(output_device_id):
            self.config_manager.set("audio/output_device_id", "")
            self.audio_engine.set_configured_output_device_id("")
            self.audio_engine.set_output_device("")

        self.audio_engine.set_gain_db(
            self.config_manager.get("audio/effects/gain_db", 0.0)
        )
        self.audio_engine.set_normalize_enabled(
            self.config_manager.get("audio/effects/normalize_enabled", False)
        )
        self.audio_engine.set_mono_enabled(
            self.config_manager.get("audio/effects/mono_enabled", False)
        )
        self.audio_engine.set_noise_reduction_settings(
            self.config_manager.get("audio/effects/noise_threshold_db", -45.0),
            self.config_manager.get("audio/effects/noise_reduction_db", 18.0),
        )
        self.audio_engine.set_noise_reduction_enabled(
            self.config_manager.get("audio/effects/noise_reduction_enabled", False)
        )
        self.audio_engine.set_equalizer_settings(
            self.config_manager.get("audio/effects/equalizer_bass_db", 0.0),
            self.config_manager.get("audio/effects/equalizer_mid_db", 0.0),
            self.config_manager.get("audio/effects/equalizer_treble_db", 0.0),
        )
        self.audio_engine.set_equalizer_enabled(
            self.config_manager.get("audio/effects/equalizer_enabled", False)
        )
        self.audio_engine.set_reverb_delay_settings(
            self.config_manager.get("audio/effects/reverb_delay_ms", 120.0),
            self.config_manager.get("audio/effects/reverb_feedback", 0.35),
            self.config_manager.get("audio/effects/reverb_mix", 0.25),
        )
        self.audio_engine.set_reverb_delay_enabled(
            self.config_manager.get("audio/effects/reverb_delay_enabled", False)
        )

    def aplicar_estilo(self):
        tema = self.config_manager.get("appearance/theme", "dark")
        self.setStyleSheet(ThemeManager.obter_tema_qss(tema))
        ThemeManager.aplicar_barra_titulo(self, tema)

        tamanho_fonte = self.config_manager.get(
            "appearance/font_size",
            self.config_manager.get("appearance/explorer_font_size", 9.0),
        )
        app = QApplication.instance()
        if app is not None:
            set_interface_font_size(app, tamanho_fonte)
        self.setFont(app.font() if app is not None else self.font())
        self.explorer_widget.set_font_size(tamanho_fonte)
        self.atualizar_icones()

    def atualizar_icones(self):
        """Atualiza os ícones dos componentes visuais da janela."""
        tema = self.config_manager.get("appearance/theme", "dark")
        cor_icone = "#374151" if tema == "light" else "#e5e7eb"

        self.player_widget.atualizar_icones(tema)
        self.explorer_widget.atualizar_icones(tema)
        self.queue_widget.atualizar_icones(tema)

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
        self.main_menu.audio_effects_requested.connect(self.abrir_ajustes_efeitos_audio)
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
        self.main_menu.setFixedHeight(28)
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
        dialog = SettingsDialog(self.config_manager, self.audio_engine, self)
        if dialog.exec():
            self.aplicar_configuracoes()

    def abrir_ajustes_efeitos_audio(self):
        """Abre a janela centralizada de ajustes e efeitos de áudio."""
        from core.theme_manager import ThemeManager
        if self.audio_effects_dialog is None:
            self.audio_effects_dialog = AudioEffectsDialog(self.config_manager, self)

        self.audio_effects_dialog._carregar_valores()
        # Garante que o tema atual seja aplicado (pode ter mudado desde a última abertura)
        tema = self.config_manager.get("appearance/theme", "dark")
        self.audio_effects_dialog.setStyleSheet(ThemeManager.obter_tema_qss(tema))
        self.audio_effects_dialog.show()
        self.audio_effects_dialog.raise_()
        self.audio_effects_dialog.activateWindow()

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
            self._abrir_karaoke_se_configurado()

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
        texto = f"""
        <h3>Sobre o StageBox</h3>
        <p>Um reprodutor de áudio moderno e elegante desenvolvido com Python e PySide6 (Qt).</p>
        <p><b>Versão:</b> {APP_VERSION}</p>
        <p><b>Última atualização:</b> {APP_LAST_UPDATE}</p>
        <p><b>Recursos:</b></p>
        <ul>
            <li>Suporte a múltiplos formatos (MP3, FLAC, M4A, OGG, WAV, etc.)</li>
            <li>Editor completo de Karaoke com frases limpas e suporte a cifras</li>
            <li>Pasta centralizada para salvar e gerenciar letras sem poluir pastas de álbuns</li>
            <li>Leitor avançado de tags e capas embutidas</li>
            <li>Fila dinâmica com duplo clique para reproduzir e recurso 'Tocar a Seguir'</li>
        </ul>
        """
        QMessageBox.about(self, "Sobre o StageBox", texto)

    # ==================================================
    # REPRODUÇÃO & KARAOKE
    # ==================================================

    def _abrir_karaoke_se_configurado(self):
        """Abre o Karaokê automaticamente quando a preferência estiver ativa."""
        if self.config_manager.get("karaoke/open_automatically_on_open", False):
            self.abrir_tela_karaoke()

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
        return track

    def definir_modo_exibicao(self, modo: str):
        self.explorer_widget.definir_modo_exibicao(modo)

    def arquivo_selecionado(self, caminho):
        """Adiciona a faixa selecionada por duplo clique e respeita o autoplay configurado."""
        caminho = Path(caminho)

        for indice, faixa in enumerate(self.queue_controller.tracks):
            if Path(faixa.path).resolve() == caminho.resolve():
                self.selecionar_faixa(indice)
                if self.config_manager.get("playback/auto_play_on_add", False):
                    self.audio_engine.play()
                self._abrir_karaoke_se_configurado()
                return

        faixa = self._adicionar_caminho_fila(caminho)
        if faixa is None:
            return

        indice = len(self.queue_controller.tracks) - 1
        self.selecionar_faixa(indice)
        if self.config_manager.get("playback/auto_play_on_add", False):
            self.audio_engine.play()
        self._abrir_karaoke_se_configurado()

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

    def abrir_arquivos_externos(self, caminhos):
        """Adiciona arquivos recebidos pelo sistema operacional e respeita o autoplay."""
        validos = []
        for caminho in caminhos or []:
            path = Path(caminho).expanduser()
            if path.is_file() and path.suffix.lower() in self.audio_extensions:
                validos.append(path)

        if not validos:
            return

        primeira_adicionada = len(self.queue_controller.tracks) == 0
        adicionadas = []
        for caminho in validos:
            faixa = self._adicionar_caminho_fila(caminho)
            if faixa is not None:
                adicionadas.append(faixa)

        if not adicionadas:
            return

        if primeira_adicionada:
            self.selecionar_faixa(0)
            if self.config_manager.get("playback/auto_play_on_add", False):
                self.audio_engine.play()
            self._abrir_karaoke_se_configurado()
        elif self.config_manager.get("playback/auto_play_on_add", False):
            indice = len(self.queue_controller.tracks) - len(adicionadas)
            self.selecionar_faixa(indice)
            self.audio_engine.play()
            self._abrir_karaoke_se_configurado()
        elif self.config_manager.get("karaoke/open_automatically_on_open", False):
            indice = len(self.queue_controller.tracks) - len(adicionadas)
            self.selecionar_faixa(indice)
            self._abrir_karaoke_se_configurado()

    def closeEvent(self, event):
        """Salva configurações e encerra recursos ao fechar o player."""
        if self.config_manager.get("playback/remember_volume", True):
            self.config_manager.set("playback/last_volume", self.volume.value())

        if self.karaoke_window is not None:
            self.karaoke_window.close()

        if self.karaoke_editor is not None:
            self.karaoke_editor.close()

        if self.audio_effects_dialog is not None:
            self.audio_effects_dialog.close()

        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    load_branding(app)

    splash = create_splash_screen()
    splash.show()
    app.processEvents()

    window = MainWindow()

    # Arquivos abertos pelo Windows (duplo clique / "Abrir com...") entram
    # diretamente na fila e seguem a configuração de reprodução automática.
    arquivos_externos = [
        argumento for argumento in sys.argv[1:]
        if not argumento.startswith("-") and Path(argumento).is_file()
    ]
    if arquivos_externos:
        window.abrir_arquivos_externos(arquivos_externos)

    time.sleep(1.2)
    app.processEvents()
    window.show()
    splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()