import cairosvg
import chess.svg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QWidget


class GamePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.player_top_widget = QLabel("?")
        self.player_bottom_widget = QLabel("?")
        self.board_image_widget = QLabel()

        self.move_notation_widget = QLabel("-")
        self.move_cost_widget = QLabel("-")
        self.evaluation_widget = QLabel("-")

        player_font = QFont()
        player_font.setBold(True)
        player_font.setPointSize(14)
        self.player_top_widget.setFont(player_font)
        self.player_bottom_widget.setFont(player_font)

        board_layout = self.create_board_layout()

        eval_layout = self.create_eval_layout()

        master_layout = QVBoxLayout(self)
        master_layout.setAlignment(Qt.AlignmentFlag.AlignTop |
                                   Qt.AlignmentFlag.AlignHCenter)
        master_layout.addLayout(board_layout)
        master_layout.addLayout(eval_layout)

    def show_position(self, board, white_player, black_player, orientation,
        last_move=None, notation="-", cost="-", evaluation="-"):
        svg = chess.svg.board(
            board=board,
            orientation=orientation,
            lastmove=last_move,
            coordinates=True,
            size=480,
            colors={
                "square light": "#B0AA98",
                "square dark": "#827A68",
                "square light lastmove": "#a1ad68",
                "square dark lastmove": "#a1ad68",
            },
        )

        pixmap = QPixmap()
        pixmap.loadFromData(cairosvg.svg2png(bytestring=svg.encode()))
        self.board_image_widget.setPixmap(pixmap)

        if orientation:
            self.player_top_widget.setText(black_player)
            self.player_bottom_widget.setText(white_player)
        else:
            self.player_top_widget.setText(white_player)
            self.player_bottom_widget.setText(black_player)

        self.move_notation_widget.setText(str(notation))
        self.move_cost_widget.setText(str(cost))
        self.evaluation_widget.setText(str(evaluation))

    def create_board_layout(self):
        layout = QVBoxLayout()
        layout.addWidget(self.player_top_widget)
        layout.addWidget(self.board_image_widget)
        layout.addWidget(self.player_bottom_widget)
        return layout

    def create_eval_layout(self):
        tag_header_font = QFont()
        tag_header_font.setBold(True)
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(20, 30, 0, 15)
        layout_title = QVBoxLayout()
        layout_value = QVBoxLayout()
        move_label = QLabel("Move:")
        move_label.setFont(tag_header_font)
        cost_label = QLabel("Cost:")
        cost_label.setFont(tag_header_font)
        eval_label = QLabel("Evaluation:")
        eval_label.setFont(tag_header_font)

        layout_title.addWidget(move_label)
        layout_title.addWidget(cost_label)
        layout_title.addWidget(eval_label)

        layout_value.addWidget(self.move_notation_widget)
        layout_value.addWidget(self.move_cost_widget)
        layout_value.addWidget(self.evaluation_widget)

        layout.addLayout(layout_title)
        layout.addSpacing(10)
        layout.addLayout(layout_value)

        return layout

    def set_move_cost_color(self):
        cost = self.move_cost_widget.text()

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

        self.move_cost_widget.setStyleSheet(f"color: {color}")
        self.move_notation_widget.setStyleSheet(f"color: {color}")