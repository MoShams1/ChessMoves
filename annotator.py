import chess
import chess.pgn
import chess.svg
import cairosvg

from PyQt6.QtWidgets import QApplication, QLabel, QWidget, \
    QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QFrame
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlDatabase, QSqlQuery


class Window(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("ChessMoves: Annotator")
        self.setFixedSize(1000, 600)

        # --------------------------------------------------------------------
        # attributes

        self.myboard = game.pgn.board()
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

        self.alternatives_label = QLabel("Best alternative(s): ")
        self.alternatives_box = QLineEdit()
        self.alternatives_box.setPlaceholderText("e.g. Nf3 g3")

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        print(game.date)
        print(game.moves)
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # --------------------------------------------------------------------
        # layout

        master_layout = QHBoxLayout()

        left_col = QVBoxLayout()
        left_col.setAlignment(Qt.AlignmentFlag.AlignTop)
        left_col.addWidget(self.player_name_top)
        left_col.addWidget(self.image_board)
        left_col.addWidget(self.player_name_bottom)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_prev_move)
        btn_row.addWidget(self.btn_next_move)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_col.addLayout(btn_row)

        right_col = QVBoxLayout()
        right_col.setAlignment(Qt.AlignmentFlag.AlignTop)
        right_col.addSpacing(20)
        right_col.addWidget(self.move_notation)

        alternatives_row = QHBoxLayout()
        alternatives_row.addWidget(self.alternatives_label)
        alternatives_row.addWidget(self.alternatives_box)

        right_col.addLayout(alternatives_row)

        master_layout.addLayout(left_col, 0)
        master_layout.addLayout(right_col, 1)
        self.setLayout(master_layout)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()
        self.alternatives_box.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

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
            self.player_name_top.setText(game.black)
            self.player_name_bottom.setText(game.white)

        if not self.flip_flag:
            self.player_name_top.setText(game.white)
            self.player_name_bottom.setText(game.black)

        if self.current_ply > 0:
            if self.current_ply % 2 == 1:
                prefix = f"{(self.current_ply + 1) // 2}. "
            else:
                prefix = f"{self.current_ply // 2}... "
            self.move_notation.setText(
                f"Played move: {prefix}{self.san_list[self.current_ply - 1]}")
        else:
            self.move_notation.setText(
                f"Played move: ")

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # print(self.myboard.fen())
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    def next_move(self):
        if self.current_ply < len(self.ply_list):
            self.current_move = self.ply_list[self.current_ply]
            self.myboard.push(self.current_move)
            self.current_ply += 1
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

    def previous_move(self):
        if self.current_ply > 0:
            self.myboard.pop()
            self.current_ply -= 1
            self.update_board()


class Game:

    def __init__(self):

        # ----------------------------------------------------------------
        # load pgn file
        with open('game1.pgn') as f:
            self.pgn = chess.pgn.read_game(f)

        # ----------------------------------------------------------------
        # extract players' names
        self.white = self.pgn.headers["White"]
        self.black = self.pgn.headers["Black"]

        # ----------------------------------------------------------------
        # extract date
        self.date = self.pgn.headers["Date"]

        # ----------------------------------------------------------------
        # extract moves
        temp_board = self.pgn.board()

        ply_list = list(self.pgn.mainline_moves())
        self.moves = []
        for move in ply_list:
            self.moves.append(temp_board.san(move))
            temp_board.push(move)

        # ----------------------------------------------------------------
        # extract engine evaluation
        pgn_string = str(self.pgn)
        pgn_parts = pgn_string.split()
        keyword = "[%eval"
        eval_array = []
        for i, part in enumerate(pgn_parts):
            if part == keyword:
                eval_array.append(pgn_parts[i + 1][:-1])


# class Move:


# --------------------------------------------------------------------
# run application

app = QApplication([])

game = Game()
window = Window()
window.show()

app.exec()

# --------------------------------------------------------------------
# create/load database

database = QSqlDatabase.addDatabase("QSQLITE")
database.setDatabaseName("chess_moves.db")
database.open()

myquery = QSqlQuery()
myquery.exec("""
CREATE TABLE IF NOT EXISTS players(
    player_id INTEGER PRIMARY KEY,
    player_name TEXT not NULL,
    player_rating INTEGER    
)
""")

myquery = QSqlQuery()
myquery.prepare("""
INSERT INTO players (player_name, player_rating)
VALUES(?, ?)
""")
myquery.addBindValue(game.pgn.headers['Black'])
myquery.addBindValue(game.pgn.headers['BlackElo'])
myquery.exec()
