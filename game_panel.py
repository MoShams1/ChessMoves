import cairosvg
import chess.svg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (QLabel, QHBoxLayout, QVBoxLayout, QWidget,
                             QPushButton)


class GamePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # --------------------------------------------------
        # attributes/variables

        # --------------------------------------------------
        # widgets

        self.player_top_wgt = QLabel()
        self.player_top_wgt.setProperty('type', 'player')
        self.player_top_wgt.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.player_bottom_wgt = QLabel()
        self.player_bottom_wgt.setProperty('type', 'player')
        self.player_bottom_wgt.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.board_image_wgt = QLabel()

        self.notation_val_wgt = QLabel()
        self.cost_val_wgt = QLabel()
        self.eval_val_wgt = QLabel()

        # --------------------------------------------------
        # layouts

        board_layout = self.create_board_layout()

        eval_layout = self.create_eval_layout()
        copy_lay = self.create_copy_layout()

        master_layout = QVBoxLayout(self)
        master_layout.setAlignment(Qt.AlignmentFlag.AlignTop |
                                   Qt.AlignmentFlag.AlignHCenter)
        master_layout.addLayout(board_layout)
        master_layout.addLayout(eval_layout)
        master_layout.addLayout(copy_lay)

    # --------------------------------------------------

    def show_position(self, board, orientation,
                      white_player="---", black_player="---", last_move=None,
                      notation_val="---", cost_val="---", eval_val="---"):
        svg = chess.svg.board(
            board=board,
            orientation=orientation,
            lastmove=last_move,
            coordinates=True,
            size=450,
            colors={
                "square light": "#B0AA98",
                "square dark": "#827A68",
                "square light lastmove": "#a1ad68",
                "square dark lastmove": "#a1ad68",
            },
        )

        pixmap = QPixmap()
        pixmap.loadFromData(cairosvg.svg2png(bytestring=svg.encode()))
        self.board_image_wgt.setPixmap(pixmap)

        if orientation:
            self.player_top_wgt.setText(black_player)
            self.player_bottom_wgt.setText(white_player)
        else:
            self.player_top_wgt.setText(white_player)
            self.player_bottom_wgt.setText(black_player)

        self.notation_val_wgt.setText(str(notation_val))
        self.cost_val_wgt.setText(str(cost_val))
        self.eval_val_wgt.setText(str(eval_val))

    def create_board_layout(self):
        layout = QVBoxLayout()
        layout.addWidget(self.player_top_wgt)
        layout.addWidget(self.board_image_wgt)
        layout.addWidget(self.player_bottom_wgt)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return layout

    def create_eval_layout(self):
        layout = QHBoxLayout()

        layout_hdr = QVBoxLayout()
        layout_val = QVBoxLayout()

        info_dict = {
            "Move:": {"type": "eval-header",
                      "val": self.notation_val_wgt},
            "Cost:": {"type": "eval-header",
                      "val": self.cost_val_wgt},
            "Evaluation:": {"type": "eval-header",
                            "val": self.eval_val_wgt},
        }
        for label, config in info_dict.items():
            hdr_wgt = QLabel(label)
            hdr_wgt.setProperty("type", config["type"])
            layout_hdr.addWidget(hdr_wgt)
            layout_val.addWidget(config["val"])

        layout.addLayout(layout_hdr)
        layout.addSpacing(10)
        layout.addLayout(layout_val)

        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(20, 30, 0, 0)

        return layout

    def create_copy_layout(self):
        layout = QHBoxLayout()

        width = 80
        spacing = -2

        button_dict = {
            "URL":
                {"tooltip": "Copy game URL (U)",
                 "width": width,
                 "shortcut": "U",
                 "callback": self.close,
                 "level": "2"},
            "PGN":
                {"tooltip": "Copy game PGN (P)",
                 "width": width,
                 "shortcut": "P",
                 "callback": self.close,
                 "level": "2"},
            "FEN":
                {"tooltip": "Copy position FEN (E)",
                 "width": width,
                 "shortcut": "E",
                 "callback": self.close,
                 "level": "2"}
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

    def set_cost_color(self):
        cost = self.cost_val_wgt.text()

        if cost in ("Unavoidable Checkmate", "Missed Checkmate"):
            color = "#EC7A5A"
        else:
            cost = float(cost)
            if .5 <= cost < 1:
                color = "#4AA8CF"
            elif 1 <= cost < 3:
                color = "#E0B953"
            elif cost >= 3:
                color = "#EC7A5A"
            else:
                color = "#D3D3D3"

        self.cost_val_wgt.setStyleSheet(f"color: {color}")
        self.notation_val_wgt.setStyleSheet(f"color: {color}")

    def copy_to_clipboard(self, text, message):
        QApplication.clipboard().setText(text)
        # self.show_message(message)
