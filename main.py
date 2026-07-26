import annotate
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication,
                             QLabel,
                             QWidget,
                             QPushButton,
                             QVBoxLayout,
                             QHBoxLayout)

from annotate import run_annotate


class Window(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("ChessMoves")
        # self.setFixedSize(1000, 800)
        self.resize(300, 130)
        self.setStyleSheet("""
        QWidget {
        color: #D3D3D3;
        }
        """)

        main_message = QLabel("What do you want to work on?")
        self.button_widgets = {}

        self.annotate_window = None

        # --------------------------------------------------------------------
        # create layouts

        button_layout = self.create_button_layout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # --------------------------------------------------------------------
        # organize layouts

        master_layout = QVBoxLayout()
        main_message.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        master_layout.addWidget(main_message)
        master_layout.addLayout(button_layout)
        master_layout.setContentsMargins(30, 30, 30, 30)
        self.setLayout(master_layout)

        # --------------------------------------------------------------------
        # button connections

        self.button_widgets["Annotate"].clicked.connect(self.open_annotate)
        self.button_widgets["Quit"].clicked.connect(self.close)

    def create_button_layout(self):
        width_small = 50
        width_large = 70
        spacing_small = -10
        spacing_large = 15
        layout = QHBoxLayout()
        buttons = {
            "Annotate":
                {"tooltip": "Annotate games (A)",
                 "width": width_large,
                 "spacing": spacing_small},
            "Train":
                {"tooltip": "Train annotated moves/positions (T)",
                 "width": width_large,
                 "spacing": spacing_small},
            "Report":
                {"tooltip": "Create statistical reports (R)",
                 "width": width_large,
                 "spacing": spacing_large},
            "Quit":
                {"tooltip": "Quit (Esc)",
                 "width": width_small,
                 "spacing": spacing_small}
        }

        for button_name, config in buttons.items():
            button_widget = QPushButton(button_name)
            button_widget.setToolTip(config["tooltip"])
            button_widget.setFixedWidth(config["width"])

            self.button_widgets[button_name] = button_widget
            layout.addWidget(button_widget)
            layout.addSpacing(int(config["spacing"]))

        return layout

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_A:
            self.open_annotate()
        elif event.key() == Qt.Key.Key_T:
            return
        elif event.key() == Qt.Key.Key_R:
            return
        elif event.key() == Qt.Key.Key_Escape:
            self.close()

    def open_annotate(self):
        self.annotate_window = run_annotate()


app = QApplication([])
window = Window()
window.show()
app.exec()
