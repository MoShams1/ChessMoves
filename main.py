from train import run_train
from annotate import run_annotate
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QApplication, QLabel, QWidget, QPushButton,
                             QVBoxLayout)


class MasterWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("ChessMoves: Main")
        self.resize(500, 300)

        # --------------------------------------------------
        # attributes/variables

        self.annotate_window = None
        self.train_window = None

        # --------------------------------------------------
        # widgets

        logo_wgt = QLabel()
        logo_wgt.setPixmap(QPixmap("logo.png"))

        # --------------------------------------------------
        # layouts

        button_lay = self.create_button_lay()

        master_lay = QVBoxLayout()
        master_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        master_lay.addSpacing(20)
        master_lay.addWidget(logo_wgt)
        master_lay.addSpacing(50)
        master_lay.addLayout(button_lay)
        master_lay.setContentsMargins(50, 50, 50, 50)
        self.setLayout(master_lay)

    # --------------------------------------------------

    def create_button_lay(self):
        width = 250
        spacing = -2
        layout = QVBoxLayout()
        button_dict = {
            "Annotate":
                {"tooltip": "Annotate moves (A)",
                 "width": width,
                 "shortcut": "A",
                 "callback": self.open_annotate,
                 "level": "1"},
            "Train":
                {"tooltip": "Train annotated moves (T)",
                 "width": width,
                 "shortcut": "T",
                 "callback": self.open_train,
                 "level": "1"},
            "Quit":
                {"tooltip": "Quit (Q)",
                 "width": width,
                 "shortcut": "Q",
                 "callback": self.close,
                 "level": "3"}
        }

        for button_name, config in button_dict.items():
            button_wgt = QPushButton(button_name)

            button_wgt.setFixedWidth(int(config["width"]))
            button_wgt.setToolTip(config["tooltip"])
            button_wgt.setShortcut(config["shortcut"])
            button_wgt.clicked.connect(config["callback"])
            button_wgt.setProperty("level", config["level"])

            layout.addWidget(button_wgt)
            layout.addSpacing(spacing)

        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        return layout

    def open_annotate(self):
        self.annotate_window = run_annotate()
        self.annotate_window.show()

    def open_train(self):
        self.train_window = run_train()
        self.train_window.show()

# --------------------------------------------------

app = QApplication([])
window = MasterWindow()
with open("styles_main.qss") as f:
    window.setStyleSheet(f.read())
window.show()
app.exec()
