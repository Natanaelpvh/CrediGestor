# ui/relogio_widget.py

from PyQt6.QtWidgets import QLCDNumber
from PyQt6.QtCore import QTime, QTimer, Qt
from . import styles
from PyQt6 import QtWidgets

class RelogioWidget(QLCDNumber):
    """
    Um widget de relógio digital que exibe a hora atual com um efeito de 'dois pontos' piscando.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setSegmentStyle(QLCDNumber.SegmentStyle.Filled)
        self.setDigitCount(8)
        self.setFixedSize(200, 60)
        self.setStyleSheet(styles.RELOGIO_STYLE)

        timer = QTimer(self)
        timer.timeout.connect(self._mostrar_hora)
        timer.start(1000)

        self._mostrar_hora()

    def _mostrar_hora(self):
        """
        Atualiza a exibição do relógio, alternando o formato da hora para
        criar o efeito de piscar dos 'dois pontos'.
        """
        time = QTime.currentTime()
        text = time.toString('hh:mm:ss' if (time.second() % 2) == 0 else 'hh mm ss')
        self.display(text)