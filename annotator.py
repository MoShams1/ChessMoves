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

        self.board = game.parsed_game.board()
        self.move_pushable = None
        self.move_str = None
        self.hmove_nr = 0
        self.flip_flag = True

        # --------------------------------------------------------------------
        # widgets

        self.player_name_top = QLabel()
        self.player_name_bottom = QLabel()

        self.image_board = QLabel()
        self.pixmap = QPixmap()

        self.btn_prev_move = QPushButton('< Last')
        self.btn_next_move = QPushButton('Next >')

        self.move_label = QLabel()

        self.alternatives_label = QLabel("Best alternative(s): ")
        self.alternatives_box = QLineEdit()
        self.alternatives_box.setPlaceholderText("e.g. Nf3 g3")

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
        right_col.addWidget(self.move_label)

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
        svgimage = chess.svg.board(board=self.board,
                                   orientation=self.flip_flag,
                                   lastmove=self.move_pushable)

        pngimage = cairosvg.svg2png(bytestring=svgimage.encode())
        self.pixmap.loadFromData(pngimage)
        self.image_board.setPixmap(self.pixmap)

        if self.flip_flag:
            self.player_name_top.setText(game.black)
            self.player_name_bottom.setText(game.white)

        if not self.flip_flag:
            self.player_name_top.setText(game.white)
            self.player_name_bottom.setText(game.black)

        if self.hmove_nr > 0:
            if self.hmove_nr % 2 == 1:
                prefix = f"{(self.hmove_nr + 1) // 2}. "
            else:
                prefix = f"{self.hmove_nr // 2}... "
            self.move_label.setText(
                f"Played move: {prefix}"
                f"{game.moves[self.hmove_nr - 1]}")
        else:
            self.move_label.setText(
                f"Played move: ")

    @property
    def fen(self):
        return self.board.fen()

    def next_move(self):
        if self.hmove_nr < len(game.pushable_moves):
            self.move_pushable = game.pushable_moves[self.hmove_nr]
            self.board.push(self.move_pushable)
            self.hmove_nr += 1
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
        if self.hmove_nr > 0:
            self.board.pop()
            self.hmove_nr -= 1
            self.update_board()


class Game:

    def __init__(self):

        # ----------------------------------------------------------------
        # load pgn file
        with open('game1.pgn') as f:
            self.parsed_game = chess.pgn.read_game(f)

        # ----------------------------------------------------------------
        # extract players' names
        self.white = self.parsed_game.headers["White"]
        self.black = self.parsed_game.headers["Black"]

        # ----------------------------------------------------------------
        # extract date
        self.date = self.parsed_game.headers["Date"]

        # ----------------------------------------------------------------
        # extract moves
        board = self.parsed_game.board()

        self.pushable_moves = list(self.parsed_game.mainline_moves())
        self.moves = []
        for pushable_move in self.pushable_moves:
            self.moves.append(board.san(pushable_move))
            board.push(pushable_move)

        # ----------------------------------------------------------------
        # extract engine evaluation
        pgn = str(self.parsed_game)
        pgn_parts = pgn.split()
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

# database = QSqlDatabase.addDatabase("QSQLITE")
# database.setDatabaseName("chess_moves.db")
# database.open()
#
# myquery = QSqlQuery()
# myquery.exec("""
# CREATE TABLE IF NOT EXISTS players(
#     player_id INTEGER PRIMARY KEY,
#     player_name TEXT not NULL,
#     player_rating INTEGER
# )
# """)
#
# myquery = QSqlQuery()
# myquery.prepare("""
# INSERT INTO players (player_name, player_rating)
# VALUES(?, ?)
# """)
# myquery.addBindValue(game.parsed_game.headers['Black'])
# myquery.addBindValue(game.parsed_game.headers['BlackElo'])
# myquery.exec()
