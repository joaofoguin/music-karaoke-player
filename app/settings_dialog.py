import os
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QAbstractSpinBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.theme_manager import ThemeManager


class SettingsDialog(QDialog):
    """Diálogo completo de Preferências e Configurações do Music Player."""

    def __init__(self, config_manager, audio_engine=None, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.audio_engine = audio_engine
        self.setWindowTitle("Configurações — Music Player")
        self.resize(600, 520)
        self.setModal(True)

        self._criar_interface()
        self._carregar_valores()
        # Aplica o tema atual ao diálogo
        tema = self.config_manager.get("appearance/theme", "dark")
        self.setStyleSheet(ThemeManager.obter_tema_qss(tema))
        ThemeManager.aplicar_barra_titulo(self, tema)
        self.combo_tema.currentIndexChanged.connect(self._previsualizar_tema)
        self.config_manager.settings_changed.connect(self._atualizar_tema_salvo)

    def _criar_interface(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(16)

        self.tabs = QTabWidget()
        layout_principal.addWidget(self.tabs)

        # ----------------------------------------------------
        # ABA 1: GERAL
        # ----------------------------------------------------
        tab_geral = QWidget()
        layout_geral = QVBoxLayout(tab_geral)
        layout_geral.setSpacing(12)

        grupo_pastas = QGroupBox("Pastas e Biblioteca")
        form_pastas = QVBoxLayout(grupo_pastas)

        lbl_dir = QLabel("Diretório padrão de músicas:")
        form_pastas.addWidget(lbl_dir)

        layout_dir = QHBoxLayout()
        self.edit_default_dir = QLineEdit()
        self.edit_default_dir.setPlaceholderText("Selecione a pasta padrão de músicas...")
        self.btn_browse_dir = QPushButton("Procurar...")
        self.btn_browse_dir.clicked.connect(self._procurar_pasta_padrao)
        layout_dir.addWidget(self.edit_default_dir, 1)
        layout_dir.addWidget(self.btn_browse_dir)
        form_pastas.addLayout(layout_dir)

        self.chk_restore_last_folder = QCheckBox("Lembrar e restaurar a última pasta aberta")
        form_pastas.addWidget(self.chk_restore_last_folder)

        layout_geral.addWidget(grupo_pastas)
        layout_geral.addStretch()
        self.tabs.addTab(tab_geral, "Geral")

        # ----------------------------------------------------
        # ABA 2: REPRODUÇÃO
        # ----------------------------------------------------
        tab_reproducao = QWidget()
        layout_reproducao = QVBoxLayout(tab_reproducao)
        layout_reproducao.setSpacing(12)

        grupo_audio = QGroupBox("Áudio e Volume")
        form_audio = QFormLayout(grupo_audio)

        self.slider_volume = QSlider(Qt.Orientation.Horizontal)
        self.slider_volume.setRange(0, 100)
        self.lbl_volume_val = QLabel("80%")
        self.slider_volume.valueChanged.connect(
            lambda v: self.lbl_volume_val.setText(f"{v}%")
        )
        layout_vol = QHBoxLayout()
        layout_vol.addWidget(self.slider_volume, 1)
        layout_vol.addWidget(self.lbl_volume_val)
        form_audio.addRow("Volume padrão inicial:", layout_vol)

        self.combo_output_device = QComboBox()
        self.combo_output_device.setToolTip("Dispositivo usado para reproduzir o áudio.")
        form_audio.addRow("Dispositivo de saída:", self.combo_output_device)

        self.chk_remember_volume = QCheckBox("Lembrar o último volume ao fechar")
        form_audio.addRow("", self.chk_remember_volume)

        self.chk_repeat_default = QCheckBox("Ativar modo repetir por padrão")
        form_audio.addRow("", self.chk_repeat_default)

        self.chk_autoplay = QCheckBox("Reproduzir automaticamente ao adicionar música")
        form_audio.addRow("", self.chk_autoplay)

        grupo_formatos = QGroupBox("Formatos de Áudio Suportados")
        form_formatos = QVBoxLayout(grupo_formatos)
        self.edit_extensions = QLineEdit()
        self.edit_extensions.setPlaceholderText(".mp3, .wav, .flac, .ogg, .m4a, .aac, .opus")
        form_formatos.addWidget(QLabel("Extensões reconhecidas (separadas por vírgula):"))
        form_formatos.addWidget(self.edit_extensions)

        layout_reproducao.addWidget(grupo_audio)
        layout_reproducao.addWidget(grupo_formatos)
        layout_reproducao.addStretch()
        self.tabs.addTab(tab_reproducao, "Reprodução")

        # ----------------------------------------------------
        # ABA 3: KARAOKE & CIFRAS
        # ----------------------------------------------------
        tab_karaoke = QWidget()
        layout_karaoke = QVBoxLayout(tab_karaoke)
        layout_karaoke.setSpacing(12)

        # Repositório Central de Letras
        grupo_storage = QGroupBox("Armazenamento Único de Letras e Cifras")
        form_storage = QVBoxLayout(grupo_storage)

        form_storage.addWidget(
            QLabel("Pasta centralizada (todas as letras criadas serão salvas aqui, mantendo suas pastas de álbuns limpas):")
        )

        layout_lyrics_dir = QHBoxLayout()
        self.edit_lyrics_dir = QLineEdit()
        self.btn_browse_lyrics_dir = QPushButton("Procurar...")
        self.btn_browse_lyrics_dir.clicked.connect(self._procurar_pasta_lyrics)
        self.btn_open_lyrics_dir = QPushButton("Abrir Pasta")
        self.btn_open_lyrics_dir.clicked.connect(self._abrir_pasta_lyrics_explorer)

        layout_lyrics_dir.addWidget(self.edit_lyrics_dir, 1)
        layout_lyrics_dir.addWidget(self.btn_browse_lyrics_dir)
        layout_lyrics_dir.addWidget(self.btn_open_lyrics_dir)
        form_storage.addLayout(layout_lyrics_dir)

        self.chk_save_central = QCheckBox("Salvar novas letras automaticamente na pasta central")
        form_storage.addWidget(self.chk_save_central)
        layout_karaoke.addWidget(grupo_storage)

        # Exibição e Cifras
        grupo_karaoke = QGroupBox("Exibição de Letras e Cifras")
        form_karaoke = QFormLayout(grupo_karaoke)

        self.chk_show_chords = QCheckBox("Exibir acordes e cifras no karaoke")
        form_karaoke.addRow("", self.chk_show_chords)

        # Cor das cifras
        self.chords_color = "#f59e0b"
        self.btn_chords_color = QPushButton()
        self.btn_chords_color.setFixedHeight(28)
        self.btn_chords_color.clicked.connect(self._escolher_cor_cifras)
        form_karaoke.addRow("Cor das cifras / acordes:", self.btn_chords_color)

        self.spin_font_size = self._configurar_spinbox(QSpinBox())
        self.spin_font_size.setRange(14, 52)
        self.spin_font_size.setValue(26)
        self.spin_font_size.setSuffix(" px")
        form_karaoke.addRow("Tamanho da fonte dos versos:", self.spin_font_size)

        self.spin_context_lines = self._configurar_spinbox(QSpinBox())
        self.spin_context_lines.setRange(1, 6)
        self.spin_context_lines.setValue(2)
        self.spin_context_lines.setSuffix(" linhas")
        form_karaoke.addRow("Versos de contexto:", self.spin_context_lines)

        self.combo_editor_model = QComboBox()
        self.combo_editor_model.addItem("StageBox — cifras separadas", "stagebox")
        self.combo_editor_model.addItem("Winamp — cifras alinhadas à letra", "winamp")
        self.combo_editor_model.setToolTip(
            "Define como as cifras são posicionadas no editor e apresentadas no Karaokê."
        )
        form_karaoke.addRow("Modelo de edição de cifras:", self.combo_editor_model)

        self.chk_open_karaoke = QCheckBox("Abrir o Karaokê automaticamente ao abrir uma música")
        form_karaoke.addRow("", self.chk_open_karaoke)

        # Cor de destaque
        self.highlight_color = "#ffffff"
        self.btn_highlight_color = QPushButton()
        self.btn_highlight_color.setFixedHeight(28)
        self.btn_highlight_color.clicked.connect(self._escolher_cor_destaque)
        form_karaoke.addRow("Cor do verso ativo:", self.btn_highlight_color)

        # Cor de contexto
        self.context_color = "#8f8f8f"
        self.btn_context_color = QPushButton()
        self.btn_context_color.setFixedHeight(28)
        self.btn_context_color.clicked.connect(self._escolher_cor_contexto)
        form_karaoke.addRow("Cor dos versos de contexto:", self.btn_context_color)

        layout_karaoke.addWidget(grupo_karaoke)
        layout_karaoke.addStretch()
        self.tabs.addTab(tab_karaoke, "Karaoke & Cifras")

        # ----------------------------------------------------
        # ABA 4: APARÊNCIA
        # ----------------------------------------------------
        tab_aparencia = QWidget()
        layout_aparencia = QVBoxLayout(tab_aparencia)
        layout_aparencia.setSpacing(12)

        grupo_tema = QGroupBox("Tema da Interface")
        form_tema = QFormLayout(grupo_tema)

        self.combo_tema = QComboBox()
        self.combo_tema.addItem("Escuro Moderno (Padrão)", "dark")
        self.combo_tema.addItem("Midnight OLED (Preto Puro)", "midnight")
        self.combo_tema.addItem("Claro Suave", "light")
        form_tema.addRow("Estilo visual:", self.combo_tema)

        self.spin_interface_font_size = self._configurar_spinbox(QDoubleSpinBox())
        self.spin_interface_font_size.setRange(8.0, 16.0)
        self.spin_interface_font_size.setSingleStep(0.5)
        self.spin_interface_font_size.setDecimals(1)
        self.spin_interface_font_size.setSuffix(" pt")
        self.spin_interface_font_size.setToolTip("Ajusta o tamanho geral dos textos da interface.")
        form_tema.addRow("Tamanho do texto da interface:", self.spin_interface_font_size)

        layout_aparencia.addWidget(grupo_tema)
        layout_aparencia.addStretch()
        self.tabs.addTab(tab_aparencia, "Aparência")

        # ----------------------------------------------------
        # BOTÕES DE AÇÃO INFERIORES
        # ----------------------------------------------------
        layout_botoes = QHBoxLayout()
        self.btn_restaurar = QPushButton("Restaurar Padrões")
        self.btn_restaurar.clicked.connect(self._restaurar_padroes)
        layout_botoes.addWidget(self.btn_restaurar)

        layout_botoes.addStretch()

        self.btn_cancelar = QPushButton("Fechar")
        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_salvar = QPushButton("Salvar Configurações")
        self.btn_salvar.setDefault(True)
        self.btn_salvar.clicked.connect(self._salvar_configuracoes)

        layout_botoes.addWidget(self.btn_cancelar)
        layout_botoes.addWidget(self.btn_salvar)

        layout_principal.addLayout(layout_botoes)

    @staticmethod
    def _configurar_spinbox(spin):
        """Mantém os controles de incremento/decremento clicáveis e estáveis."""
        spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        spin.setKeyboardTracking(False)
        spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        spin.lineEdit().setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        return spin

    def _procurar_pasta_padrao(self):
        caminho = QFileDialog.getExistingDirectory(
            self,
            "Selecione o diretório padrão de músicas",
            self.edit_default_dir.text() or str(Path.home()),
        )
        if caminho:
            self.edit_default_dir.setText(caminho)

    def _procurar_pasta_lyrics(self):
        caminho = QFileDialog.getExistingDirectory(
            self,
            "Selecione a pasta central de letras e karaokês",
            self.edit_lyrics_dir.text() or str(Path.home() / "Music"),
        )
        if caminho:
            self.edit_lyrics_dir.setText(caminho)

    def _abrir_pasta_lyrics_explorer(self):
        caminho = self.edit_lyrics_dir.text().strip()
        if caminho and Path(caminho).is_dir():
            if os.name == "nt":
                os.startfile(caminho)
            else:
                subprocess.Popen(["xdg-open", caminho])

    def _atualizar_botoes_cores(self):
        self.btn_highlight_color.setStyleSheet(
            f"background-color: {self.highlight_color}; border: 1px solid #777; border-radius: 4px;"
        )
        self.btn_highlight_color.setText(self.highlight_color)

        self.btn_context_color.setStyleSheet(
            f"background-color: {self.context_color}; border: 1px solid #777; border-radius: 4px;"
        )
        self.btn_context_color.setText(self.context_color)

        self.btn_chords_color.setStyleSheet(
            f"background-color: {self.chords_color}; border: 1px solid #777; border-radius: 4px;"
        )
        self.btn_chords_color.setText(self.chords_color)

    def _escolher_cor_destaque(self):
        cor = QColorDialog.getColor(QColor(self.highlight_color), self, "Escolha a cor do verso ativo")
        if cor.isValid():
            self.highlight_color = cor.name()
            self._atualizar_botoes_cores()

    def _escolher_cor_contexto(self):
        cor = QColorDialog.getColor(QColor(self.context_color), self, "Escolha a cor do contexto")
        if cor.isValid():
            self.context_color = cor.name()
            self._atualizar_botoes_cores()

    def _escolher_cor_cifras(self):
        cor = QColorDialog.getColor(QColor(self.chords_color), self, "Escolha a cor das cifras/acordes")
        if cor.isValid():
            self.chords_color = cor.name()
            self._atualizar_botoes_cores()

    def _carregar_dispositivos_audio(self):
        self.combo_output_device.clear()
        self.combo_output_device.addItem("Automático (dispositivo padrão do Windows)", "")
        if self.audio_engine is None:
            self.combo_output_device.setEnabled(False)
            return

        configurado = self.config_manager.get("audio/output_device_id", "")
        self.audio_engine.set_configured_output_device_id(configurado)
        dispositivos = self.audio_engine.output_devices()
        selecionado = -1
        for device in dispositivos:
            device_id = bytes(device.id()).hex()
            self.combo_output_device.addItem(device.description(), device_id)
            if device_id == configurado:
                selecionado = self.combo_output_device.count() - 1

        if selecionado >= 0:
            self.combo_output_device.setCurrentIndex(selecionado)
        else:
            self.combo_output_device.setCurrentIndex(0)

    def _carregar_valores(self):
        self.edit_default_dir.setText(self.config_manager.get("general/default_music_dir", ""))
        self.chk_restore_last_folder.setChecked(self.config_manager.get("general/restore_last_folder", True))

        vol = self.config_manager.get("playback/default_volume", 80)
        self._carregar_dispositivos_audio()
        self.slider_volume.setValue(vol)
        self.lbl_volume_val.setText(f"{vol}%")

        self.chk_remember_volume.setChecked(self.config_manager.get("playback/remember_volume", True))
        self.chk_repeat_default.setChecked(self.config_manager.get("playback/repeat_enabled", False))
        self.chk_autoplay.setChecked(self.config_manager.get("playback/auto_play_on_add", False))
        self.chk_open_karaoke.setChecked(self.config_manager.get("karaoke/open_automatically_on_open", False))

        exts = self.config_manager.get("playback/audio_extensions", [".mp3", ".wav", ".flac", ".ogg", ".opus", ".m4a", ".aac"])
        self.edit_extensions.setText(", ".join(exts))

        # Karaoke e Letras
        lyrics_dir = self.config_manager.get(
            "karaoke/lyrics_directory", str(Path.home() / "Music" / "Karaoke_Lyrics")
        )
        self.edit_lyrics_dir.setText(lyrics_dir)
        self.chk_save_central.setChecked(self.config_manager.get("karaoke/save_to_central_dir", True))
        self.chk_show_chords.setChecked(self.config_manager.get("karaoke/show_chords", True))
        self.chords_color = self.config_manager.get("karaoke/chords_color", "#f59e0b")

        self.spin_font_size.setValue(self.config_manager.get("karaoke/font_size", 26))
        self.spin_context_lines.setValue(self.config_manager.get("karaoke/context_lines", 2))
        modelo = self.config_manager.get("karaoke/editor_model", "stagebox")
        idx_modelo = self.combo_editor_model.findData(modelo)
        if idx_modelo >= 0:
            self.combo_editor_model.setCurrentIndex(idx_modelo)
        self.highlight_color = self.config_manager.get("karaoke/highlight_color", "#ffffff")
        self.context_color = self.config_manager.get("karaoke/context_color", "#8f8f8f")
        self._atualizar_botoes_cores()

        self.spin_interface_font_size.setValue(
            self.config_manager.get(
                "appearance/font_size",
                self.config_manager.get("appearance/explorer_font_size", 9.0),
            )
        )

        tema = self.config_manager.get("appearance/theme", "dark")
        idx = self.combo_tema.findData(tema)
        if idx >= 0:
            self.combo_tema.setCurrentIndex(idx)

    def _previsualizar_tema(self, _index):
        """Aplica imediatamente o tema escolhido na própria janela de Preferências."""
        tema = self.combo_tema.currentData()
        if tema:
            self.setStyleSheet(ThemeManager.obter_tema_qss(tema))
            ThemeManager.aplicar_barra_titulo(self, tema)

    def _atualizar_tema_salvo(self):
        """Sincroniza o diálogo quando o tema for alterado em outra janela."""
        tema = self.config_manager.get("appearance/theme", "dark")
        self.setStyleSheet(ThemeManager.obter_tema_qss(tema))
        ThemeManager.aplicar_barra_titulo(self, tema)

    def _salvar_configuracoes(self):
        exts_raw = self.edit_extensions.text().split(",")
        exts = [
            (e.strip().lower() if e.strip().startswith(".") else f".{e.strip().lower()}")
            for e in exts_raw
            if e.strip()
        ]
        if not exts:
            exts = [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus"]

        novas_configuracoes = {
            "general/default_music_dir": self.edit_default_dir.text().strip(),
            "general/restore_last_folder": self.chk_restore_last_folder.isChecked(),
            "playback/default_volume": self.slider_volume.value(),
            "playback/remember_volume": self.chk_remember_volume.isChecked(),
            "playback/repeat_enabled": self.chk_repeat_default.isChecked(),
            "playback/auto_play_on_add": self.chk_autoplay.isChecked(),
            "karaoke/open_automatically_on_open": self.chk_open_karaoke.isChecked(),
            "playback/audio_extensions": exts,
            "audio/output_device_id": self.combo_output_device.currentData() or "",
            "karaoke/lyrics_directory": self.edit_lyrics_dir.text().strip(),
            "karaoke/save_to_central_dir": self.chk_save_central.isChecked(),
            "karaoke/show_chords": self.chk_show_chords.isChecked(),
            "karaoke/chords_color": self.chords_color,
            "karaoke/font_size": self.spin_font_size.value(),
            "karaoke/context_lines": self.spin_context_lines.value(),
            "karaoke/editor_model": self.combo_editor_model.currentData(),
            "karaoke/highlight_color": self.highlight_color,
            "karaoke/context_color": self.context_color,
            "appearance/theme": self.combo_tema.currentData(),
            "appearance/font_size": self.spin_interface_font_size.value(),
        }

        self.config_manager.update_multiple(novas_configuracoes)
        # A aplicação das configurações ocorre em um único ponto:
        # MainWindow reage ao sinal settings_changed e atualiza o áudio/UI.
        # O diálogo permanece responsável apenas por editar e persistir valores.
        # O botão Salvar aplica as alterações sem fechar esta janela.
        # O usuário pode continuar ajustando as configurações ou fechá-la
        # explicitamente pelo botão Fechar ou pelo X da janela.

    def _restaurar_padroes(self):
        self.config_manager.reset_to_defaults()
        self._carregar_valores()
