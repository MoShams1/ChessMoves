import io

import chess
import chess.pgn
import chess.svg
import cairosvg

from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QGridLayout
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

class Window(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chess Moves: Annotator")

        layout = QGridLayout(self)
        self.setContentsMargins(20, 20, 20, 20)
        self.setLayout(layout)

        self.player1_name = QLabel()
        self.player2_name = QLabel()

        self.board_image = QLabel()
        self.pixmap = QPixmap()

        layout.addWidget(self.player2_name, 0, 0)
        layout.addWidget(self.board_image, 1, 0)
        layout.addWidget(self.player1_name, 2, 0)

        self.current_move = -1
        self.myboard = game.board()

        self.init_board()

        # # self.board = game.board()
        # # self.current_move = -1
        # # self.update_board()
        #
        # svg = chess.svg.board(board=self.board)
        # png = cairosvg.svg2png(
        #     bytestring=svg.encode()
        # )
        # pixmap = QPixmap()
        # pixmap.loadFromData(png)
        #
        # layout.addWidget(pixmap, 1, 0)


    def init_board(self):

        svgimage = chess.svg.board(board=self.myboard)
        pngimage = cairosvg.svg2png(bytestring=svgimage.encode())
        self.pixmap.loadFromData(pngimage)

        self.board_image.setPixmap(self.pixmap)

        self.player1_name.setText(game.headers["White"])
        self.player2_name.setText(game.headers["Black"])


    def update_board(self):
        svgimage = chess.svg.board(board=self.myboard)
        pngimage = cairosvg.svg2png(bytestring=svgimage.encode())
        self.pixmap.loadFromData(pngimage)
        self.board_image.setPixmap(self.pixmap)


    def keyPressEvent(self, event):

        if event.key() == Qt.Key.Key_Escape:
            self.close()

        elif event.key() == Qt.Key.Key_Right:

            if self.current_move < len(ply_list) - 1:
                self.current_move += 1
                self.myboard.push(ply_list[self.current_move])
                self.update_board()

        elif event.key() == Qt.Key.Key_Left:

            if self.current_move >= 0:
                self.myboard.pop()
                self.current_move -= 1
                self.update_board()


with open('game1.pgn') as f:
    game = chess.pgn.read_game(f)

ply_list = list(game.mainline_moves())

app = QApplication([])

window = Window()
window.show()

app.exec()
