from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from typing import Callable


ButtonInfo = tuple[str, Callable[[], None]]


class ButtonList(QWidget):
    def __init__(self, options: list[ButtonInfo] = [], parent=None):
        super(ButtonList, self).__init__(parent)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        for (label, action) in options:
            button = QPushButton(label)
            button.clicked.connect(action)
            layout.addWidget(button)
