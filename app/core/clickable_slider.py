from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QSlider, QStyle, QStyleOptionSlider


class ClickableSlider(QSlider):
    """QSlider aprimorado que pula instantaneamente para a posição exata clicada com o mouse."""

    clicked_position = Signal(int)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)

            if self.orientation() == Qt.Orientation.Horizontal:
                # Calcula a nova posição proporcional ao clique
                largura = self.width()
                if largura > 0:
                    pos_x = max(0, min(event.pos().x(), largura))
                    valor = QStyle.sliderValueFromPosition(
                        self.minimum(), self.maximum(), pos_x, largura
                    )
                    self.setValue(valor)
                    self.sliderMoved.emit(valor)
                    self.clicked_position.emit(valor)
            else:
                altura = self.height()
                if altura > 0:
                    pos_y = max(0, min(event.pos().y(), altura))
                    valor = QStyle.sliderValueFromPosition(
                        self.minimum(), self.maximum(), altura - pos_y, altura
                    )
                    self.setValue(valor)
                    self.sliderMoved.emit(valor)
                    self.clicked_position.emit(valor)

        super().mousePressEvent(event)
