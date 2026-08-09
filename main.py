from PyQt6.QtCore import Qt
from annotate import run_annotate
from train import run_train
from PyQt6.QtWidgets import (QApplication,
                             QLabel,
                             QWidget,
                             QPushButton,
                             QVBoxLayout,
                             QHBoxLayout)


class MasterWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("ChessMoves")
        self.resize(300, 300)
        self.setStyleSheet("""
            QWidget {
                background: rgb(60, 60, 60);
                color: rgb(200, 200, 200);                
            }
            
            QLabel[level="1"] {
                font-family: Georgia;
                font-size: 42px;
                margin: 40px;
            }
            
            QPushButton[level="1"] {
                background-color: rgb(20, 80, 150);
                border-radius: 10px;
                font-size: 21px;                
                padding: 10px;
            }
            
            QPushButton[level="2"] {
                background-color: rgb(100, 100, 100);
                border-style: outset;
                border-width: 0px;
                border-radius: 10px;
                border-color: black;
                font-size: 21px;                
                padding: 10px;
            }
            
            QPushButton[level="3"] {
                background-color: rgb(60, 60, 60);
                border-style: outset;
                border-width: 0px;
                border-radius: 10px;
                border-color: black;
                font-size: 21px;
                text-decoration: underline;                
                padding: 10px;
            }
        """)

        self.button_widgets = {}

        self.annotate_window = None
        self.train_window = None

        self.title = QLabel("ChessMoves")
        self.title.setProperty('level', '1')

        # --------------------------------------------------------------------
        # create layouts

        button_layout = self.create_button_layout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # --------------------------------------------------------------------
        # organize layouts

        master_layout = QVBoxLayout()
        master_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        master_layout.addWidget(self.title)
        master_layout.addLayout(button_layout)
        master_layout.setContentsMargins(30, 30, 30, 30)
        self.setLayout(master_layout)

        # --------------------------------------------------------------------
        # button connections

        self.button_widgets["Annotate"].clicked.connect(self.open_annotate)
        self.button_widgets["Train"].clicked.connect(self.open_train)
        self.button_widgets["Quit"].clicked.connect(self.close)

    def create_button_layout(self):
        width = 250
        layout = QVBoxLayout()
        buttons = {
            "Annotate":
                {"tooltip": "Annotate games (A)",
                 "width": width},
            "Train":
                {"tooltip": "Train annotated moves/positions (T)",
                 "width": width},
            "Quit":
                {"tooltip": "Quit (Esc)",
                 "width": width}
        }

        for button_name, config in buttons.items():
            button_widget = QPushButton(button_name)
            button_widget.setToolTip(config["tooltip"])
            if button_name in ["Annotate"]:
                button_widget.setProperty('level', '1')
            if button_name in ["Train"]:
                button_widget.setProperty('level', '2')
            if button_name in ["Quit"]:
                button_widget.setProperty('level', '3')

            self.button_widgets[button_name] = button_widget
            self.button_widgets[button_name].setFixedWidth(
                int(config["width"]))
            layout.addWidget(button_widget)

        return layout

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_A:
            self.open_annotate()
        elif event.key() == Qt.Key.Key_T:
            self.open_train()
        elif event.key() == Qt.Key.Key_R:
            return
        elif event.key() == Qt.Key.Key_Escape:
            self.close()

    def open_annotate(self):
        self.annotate_window = run_annotate()

    def open_train(self):
        self.train_window = run_train()


app = QApplication([])
window = MasterWindow()
window.show()
app.exec()
