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
                # Usa a área útil entre as extremidades do controle. Forçar
                # explicitamente os extremos garante que o primeiro clique
                # realmente produza exatamente 0 ms.
                largura = self.width()
                if largura > 0:
                    pos_x = max(0, min(event.pos().x(), largura - 1))
                    if pos_x <= 2:
                        valor = self.minimum()
                    elif pos_x >= largura - 3:
                        valor = self.maximum()
                    else:
                        valor = QStyle.sliderValueFromPosition(
                            self.minimum(), self.maximum(), pos_x, largura - 1
                        )
                    self.setValue(valor)
                    self.sliderMoved.emit(valor)
                    self.clicked_position.emit(valor)
            else:
                altura = self.height()
                if altura > 0:
                    pos_y = max(0, min(event.pos().y(), altura - 1))
                    if pos_y <= 2:
                        valor = self.maximum()
                    elif pos_y >= altura - 3:
                        valor = self.minimum()
                    else:
                        valor = QStyle.sliderValueFromPosition(
                            self.minimum(), self.maximum(), altura - 1 - pos_y, altura - 1
                        )
                    self.setValue(valor)
                    self.sliderMoved.emit(valor)
                    self.clicked_position.emit(valor)

            # Não delega o clique ao QSlider: o evento padrão poderia recalcular
            # a posição usando a geometria do handle e desfazer o valor extremo.
            return

        super().mousePressEvent(event)
