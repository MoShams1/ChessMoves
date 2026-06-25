import io
import chess
import chess.pgn
import chess.svg
import cairosvg

from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QGridLayout, \
    QPushButton, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class Window(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("ChessMoves: Annotator")
        self.resize(1000, 500)

        # --------------------------------------------------------------------
        # attributes

        self.myboard_temp = game.board()

        self.ply_list = list(game.mainline_moves())
        self.san_list = []
        for move in self.ply_list:
            self.san_list.append(self.myboard_temp.san(move))
            self.myboard_temp.push(move)

        self.myboard = game.board()
        self.current_move = None
        self.current_ply = 0
        self.flip_flag = True

        # --------------------------------------------------------------------
        # widgets

        self.player_name_top = QLabel()
        self.player_name_bottom = QLabel()

        self.image_board = QLabel()
        self.pixmap = QPixmap()

        self.btn_prev_move = QPushButton('< Last')
        self.btn_next_move = QPushButton('Next >')

        self.move_notation = QLabel()

        # --------------------------------------------------------------------
        # layout

        master_layout = QHBoxLayout()

        left_col = QVBoxLayout()
        left_col.addWidget(self.player_name_top)
        left_col.addWidget(self.image_board)
        left_col.addWidget(self.player_name_bottom)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_prev_move)
        btn_row.addWidget(self.btn_next_move)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_col.addLayout(btn_row)

        right_col = QVBoxLayout()
        right_col.addWidget(self.move_notation)

        master_layout.addLayout(left_col, 0)
        master_layout.addLayout(right_col, 1)
        self.setLayout(master_layout)

        self.update_board()

        # --------------------------------------------------------------------
        # button connections

        self.btn_prev_move.clicked.connect(self.previous_move)
        self.btn_next_move.clicked.connect(self.next_move)

    def update_board(self):
        svgimage = chess.svg.board(board=self.myboard,
                                   orientation=self.flip_flag,
                                   lastmove=self.current_move)

        pngimage = cairosvg.svg2png(bytestring=svgimage.encode())
        self.pixmap.loadFromData(pngimage)
        self.image_board.setPixmap(self.pixmap)

        if self.flip_flag:
            self.player_name_top.setText(game.headers["Black"])
            self.player_name_bottom.setText(game.headers["White"])

        if not self.flip_flag:
            self.player_name_top.setText(game.headers["White"])
            self.player_name_bottom.setText(game.headers["Black"])

        if self.current_ply > 0:
            if self.current_ply % 2 == 1:
                prefix = f"{(self.current_ply + 1) // 2}. "
            else:
                prefix = f"{self.current_ply // 2}... "
            self.move_notation.setText(
                f"Played move: {prefix}{self.san_list[self.current_ply-1]}")
        else:
            self.move_notation.setText(
                f"Played move: ")

    def next_move(self):
        if self.current_ply < len(self.ply_list):
            self.current_move = self.ply_list[self.current_ply]
            self.myboard.push(self.current_move)
            self.current_ply += 1
            self.update_board()

    def previous_move(self):
        if self.current_ply > 0:
            self.myboard.pop()
            self.current_ply -= 1
            self.update_board()

    def keyPressEvent(self, event):

        if event.key() == Qt.Key.Key_Escape:
            self.close()

        elif event.key() == Qt.Key.Key_Right:
            self.btn_next_move.animateClick()

        elif event.key() == Qt.Key.Key_Left:
            self.btn_prev_move.animateClick()

        elif event.key() == Qt.Key.Key_F:
            self.flip_flag = not self.flip_flag
            self.update_board()


with open('game1.pgn') as f:
    game = chess.pgn.read_game(f)

app = QApplication([])

window = Window()
window.show()

app.exec()
