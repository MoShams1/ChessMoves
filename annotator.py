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

        # --------------------------------------------------------------------
        # attributes

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

        left_col.addLayout(btn_row)

        right_col = QVBoxLayout()

        master_layout.addLayout(left_col)
        master_layout.addLayout(right_col)

        # --------------------------------------------------------------------
        # ???

        self.btn_prev_move.clicked.connect(self.previous_move)
        self.btn_next_move.clicked.connect(self.next_move)

        self.setLayout(master_layout)

        self.update_board()

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

    def next_move(self):
        if self.current_ply < len(ply_list):
            self.current_move = ply_list[self.current_ply]
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
            # self.next_move()

        elif event.key() == Qt.Key.Key_Left:
            self.btn_prev_move.animateClick()
            # self.previous_move()

        elif event.key() == Qt.Key.Key_F:
            self.flip_flag = not self.flip_flag
            self.update_board()


with open('game1.pgn') as f:
    game = chess.pgn.read_game(f)

ply_list = list(game.mainline_moves())

app = QApplication([])

window = Window()
window.show()

app.exec()
