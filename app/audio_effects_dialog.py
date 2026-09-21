from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
)

from core.theme_manager import ThemeManager


class AudioEffectsDialog(QDialog):
    """Janela centralizada para ajustes e efeitos de áudio."""

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Ajustes e Efeitos de Áudio")
        self.resize(520, 620)
        self.setModal(False)

        self._criar_interface()
        self._carregar_valores()
        # Aplica o tema atual ao diálogo
        tema = self.config_manager.get("appearance/theme", "dark")
        self.setStyleSheet(ThemeManager.obter_tema_qss(tema))
        ThemeManager.aplicar_barra_titulo(self, tema)
        self.config_manager.settings_changed.connect(self._atualizar_tema)

    def _atualizar_tema(self):
        """Atualiza o tema mesmo enquanto a janela de efeitos estiver aberta."""
        tema = self.config_manager.get("appearance/theme", "dark")
        self.setStyleSheet(ThemeManager.obter_tema_qss(tema))
        ThemeManager.aplicar_barra_titulo(self, tema)

    def _criar_interface(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(12)

        grupo_ajustes = QGroupBox("Ajustes de Áudio")
        form_ajustes = QFormLayout(grupo_ajustes)

        self.chk_mono_enabled = QCheckBox("Reproduzir em mono (mesclar canais)")
        form_ajustes.addRow("", self.chk_mono_enabled)

        self.spin_gain_db = self._configurar_spinbox(QDoubleSpinBox())
        self.spin_gain_db.setRange(-60.0, 24.0)
        self.spin_gain_db.setDecimals(1)
        self.spin_gain_db.setSingleStep(0.5)
        self.spin_gain_db.setSuffix(" dB")
        form_ajustes.addRow("Ganho / Trim:", self.spin_gain_db)

        self.chk_normalize_enabled = QCheckBox("Normalizar automaticamente o nível do áudio")
        form_ajustes.addRow("", self.chk_normalize_enabled)

        layout_principal.addWidget(grupo_ajustes)

        grupo_reducao = QGroupBox("Redução de Ruído")
        form_reducao = QFormLayout(grupo_reducao)

        self.chk_noise_reduction_enabled = QCheckBox("Ativar redução de ruído")
        form_reducao.addRow("", self.chk_noise_reduction_enabled)

        self.spin_noise_threshold_db = self._configurar_spinbox(QDoubleSpinBox())
        self.spin_noise_threshold_db.setRange(-80.0, -10.0)
        self.spin_noise_threshold_db.setDecimals(1)
        self.spin_noise_threshold_db.setSingleStep(1.0)
        self.spin_noise_threshold_db.setSuffix(" dB")
        form_reducao.addRow("Limiar de ruído:", self.spin_noise_threshold_db)

        self.spin_noise_reduction_db = self._configurar_spinbox(QDoubleSpinBox())
        self.spin_noise_reduction_db.setRange(0.0, 60.0)
        self.spin_noise_reduction_db.setDecimals(1)
        self.spin_noise_reduction_db.setSingleStep(1.0)
        self.spin_noise_reduction_db.setSuffix(" dB")
        form_reducao.addRow("Redução:", self.spin_noise_reduction_db)

        layout_principal.addWidget(grupo_reducao)

        grupo_equalizador = QGroupBox("Equalizador de 3 Bandas")
        form_equalizador = QFormLayout(grupo_equalizador)

        self.chk_equalizer_enabled = QCheckBox("Ativar equalizador")
        form_equalizador.addRow("", self.chk_equalizer_enabled)

        self.spin_equalizer_bass_db = self._criar_spin_eq()
        form_equalizador.addRow("Graves (100 Hz):", self.spin_equalizer_bass_db)

        self.spin_equalizer_mid_db = self._criar_spin_eq()
        form_equalizador.addRow("Médios (1 kHz):", self.spin_equalizer_mid_db)

        self.spin_equalizer_treble_db = self._criar_spin_eq()
        form_equalizador.addRow("Agudos (10 kHz):", self.spin_equalizer_treble_db)

        layout_principal.addWidget(grupo_equalizador)

        grupo_reverb_delay = QGroupBox("Reverb / Delay")
        form_reverb_delay = QFormLayout(grupo_reverb_delay)

        self.chk_reverb_delay_enabled = QCheckBox("Ativar Reverb / Delay")
        form_reverb_delay.addRow("", self.chk_reverb_delay_enabled)

        self.spin_reverb_delay_ms = self._configurar_spinbox(QDoubleSpinBox())
        self.spin_reverb_delay_ms.setRange(10.0, 2000.0)
        self.spin_reverb_delay_ms.setDecimals(0)
        self.spin_reverb_delay_ms.setSingleStep(10.0)
        self.spin_reverb_delay_ms.setSuffix(" ms")
        form_reverb_delay.addRow("Delay:", self.spin_reverb_delay_ms)

        self.spin_reverb_feedback = self._configurar_spinbox(QDoubleSpinBox())
        self.spin_reverb_feedback.setRange(0.0, 95.0)
        self.spin_reverb_feedback.setDecimals(0)
        self.spin_reverb_feedback.setSingleStep(5.0)
        self.spin_reverb_feedback.setSuffix(" %")
        form_reverb_delay.addRow("Feedback:", self.spin_reverb_feedback)

        self.spin_reverb_mix = self._configurar_spinbox(QDoubleSpinBox())
        self.spin_reverb_mix.setRange(0.0, 100.0)
        self.spin_reverb_mix.setDecimals(0)
        self.spin_reverb_mix.setSingleStep(5.0)
        self.spin_reverb_mix.setSuffix(" %")
        form_reverb_delay.addRow("Mix:", self.spin_reverb_mix)

        layout_principal.addWidget(grupo_reverb_delay)
        layout_principal.addStretch()

        layout_botoes = QHBoxLayout()
        layout_botoes.addStretch()

        btn_fechar = QPushButton("Fechar")
        btn_fechar.clicked.connect(self.close)
        layout_botoes.addWidget(btn_fechar)

        self.btn_aplicar = QPushButton("Aplicar")
        self.btn_aplicar.setDefault(True)
        self.btn_aplicar.clicked.connect(self._aplicar_configuracoes)
        layout_botoes.addWidget(self.btn_aplicar)

        layout_principal.addLayout(layout_botoes)

    @staticmethod
    def _criar_spin_eq():
        spin = AudioEffectsDialog._configurar_spinbox(QDoubleSpinBox())
        spin.setRange(-12.0, 12.0)
        spin.setDecimals(1)
        spin.setSingleStep(0.5)
        spin.setSuffix(" dB")
        return spin

    @staticmethod\n    def _configurar_spinbox(spin):\n        """Mantém os controles de incremento/decremento clicáveis e estáveis."""\n        spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)\n        spin.setKeyboardTracking(False)\n        spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)\n        spin.lineEdit().setFocusPolicy(Qt.FocusPolicy.StrongFocus)\n        return spin\n\n    def _carregar_valores(self):
        self.chk_mono_enabled.setChecked(
            self.config_manager.get("audio/effects/mono_enabled", False)
        )
        self.spin_gain_db.setValue(
            self.config_manager.get("audio/effects/gain_db", 0.0)
        )
        self.chk_normalize_enabled.setChecked(
            self.config_manager.get("audio/effects/normalize_enabled", False)
        )
        self.chk_noise_reduction_enabled.setChecked(
            self.config_manager.get("audio/effects/noise_reduction_enabled", False)
        )
        self.spin_noise_threshold_db.setValue(
            self.config_manager.get("audio/effects/noise_threshold_db", -45.0)
        )
        self.spin_noise_reduction_db.setValue(
            self.config_manager.get("audio/effects/noise_reduction_db", 18.0)
        )
        self.chk_equalizer_enabled.setChecked(
            self.config_manager.get("audio/effects/equalizer_enabled", False)
        )
        self.spin_equalizer_bass_db.setValue(
            self.config_manager.get("audio/effects/equalizer_bass_db", 0.0)
        )
        self.spin_equalizer_mid_db.setValue(
            self.config_manager.get("audio/effects/equalizer_mid_db", 0.0)
        )
        self.spin_equalizer_treble_db.setValue(
            self.config_manager.get("audio/effects/equalizer_treble_db", 0.0)
        )
        self.chk_reverb_delay_enabled.setChecked(
            self.config_manager.get("audio/effects/reverb_delay_enabled", False)
        )
        self.spin_reverb_delay_ms.setValue(
            self.config_manager.get("audio/effects/reverb_delay_ms", 120.0)
        )
        self.spin_reverb_feedback.setValue(
            self.config_manager.get("audio/effects/reverb_feedback", 0.35) * 100.0
        )
        self.spin_reverb_mix.setValue(
            self.config_manager.get("audio/effects/reverb_mix", 0.25) * 100.0
        )

    def _aplicar_configuracoes(self):
        self.config_manager.update_multiple(
            {
                "audio/effects/mono_enabled": self.chk_mono_enabled.isChecked(),
                "audio/effects/gain_db": self.spin_gain_db.value(),
                "audio/effects/normalize_enabled": self.chk_normalize_enabled.isChecked(),
                "audio/effects/noise_reduction_enabled": self.chk_noise_reduction_enabled.isChecked(),
                "audio/effects/noise_threshold_db": self.spin_noise_threshold_db.value(),
                "audio/effects/noise_reduction_db": self.spin_noise_reduction_db.value(),
                "audio/effects/equalizer_enabled": self.chk_equalizer_enabled.isChecked(),
                "audio/effects/equalizer_bass_db": self.spin_equalizer_bass_db.value(),
                "audio/effects/equalizer_mid_db": self.spin_equalizer_mid_db.value(),
                "audio/effects/equalizer_treble_db": self.spin_equalizer_treble_db.value(),
                "audio/effects/reverb_delay_enabled": self.chk_reverb_delay_enabled.isChecked(),
                "audio/effects/reverb_delay_ms": self.spin_reverb_delay_ms.value(),
                "audio/effects/reverb_feedback": self.spin_reverb_feedback.value() / 100.0,
                "audio/effects/reverb_mix": self.spin_reverb_mix.value() / 100.0,
            }
        )
