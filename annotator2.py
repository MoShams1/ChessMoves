import chess
import chess.pgn
import chess.svg
import cairosvg

from PyQt6.QtWidgets import (
    QApplication, QLabel, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QRadioButton, QButtonGroup, QCheckBox, QGroupBox)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlDatabase, QSqlQuery


class Window(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("ChessMoves: Annotator")
        self.setFixedSize(700, 700)

        # --------------------------------------------------------------------
        # attributes

        self.board = game.parsed_game.board()
        self.move_pushable = None
        self.move_str = None
        self.hmove_nr = 0
        self.flip_flag = True
        self.pixmap = QPixmap()
        self.player_top = QLabel()
        self.player_bottom = QLabel()
        self.image_board = QLabel()

        # --------------------------------------------------------------------
        # widgets

        self.header_font = QFont()
        self.header_font.setBold(True)

        self.move_label = QLabel()
        self.move_label.setFont(self.header_font)

        lay_board = self.create_board()

        lay_navi_buttons, self.bt_dict = self.create_navi_buttons(
            ["< Last", "Next >"])

        lay_game_phase = self.create_radiobutton_list(
            "Game Phase",
            [
                "Opening",
                "Middlegame",
                "Endgame"])

        lay_tactics = self.create_checkbox_list(
            "Tactical Theme",
            [
                "Pin",
                "Fork",
                "Skewer",
                "Double Attack",
                "Trapped Piece",
                "Hanging Material",
                "Forced Checkmate",
                "Discovered Attack",
                "Removal of Defender"]
        )

        lay_positional = self.create_checkbox_list(
            "Positional Disadvantage",
            [
                "Spatial Control Loss",
                "Tempo/Initiative Loss",
                "Allowed Passed Pawn",
                "Unfavorable Exchange",
                "Compromised King Safety",
                "Pawn Structure Weakness"]
        )

        lay_diagnosis = self.create_checkbox_list(
            "Diagnosis",
            [
                "Fatigue",
                "Oversight",
                "Time Trouble",
                "Mis-Evaluation",
                "Mis-Calculation",
                "Missed Intention"]
        )

        # --------------------------------------------------------------------

        board_layout = QVBoxLayout()
        board_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        board_layout.addLayout(lay_board)
        board_layout.addLayout(lay_navi_buttons)

        tags_layout = QVBoxLayout()
        tags_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        tags_layout.addLayout(lay_game_phase)
        tags_layout.addLayout(lay_tactics)
        tags_layout.addLayout(lay_positional)
        tags_layout.addLayout(lay_diagnosis)

        master_layout = QHBoxLayout()
        master_layout.addLayout(board_layout, 0)
        master_layout.addSpacing(20)
        master_layout.addLayout(tags_layout, 1)
        self.setLayout(master_layout)

        # --------------------------------------------------------------------

        self.update_board()

        # --------------------------------------------------------------------
        # button connections

        self.bt_dict["< Last"].clicked.connect(self.previous_move)
        self.bt_dict["Next >"].clicked.connect(self.next_move)

    def update_board(self):
        svgimage = chess.svg.board(board=self.board,
                                   orientation=self.flip_flag,
                                   lastmove=self.move_pushable)

        pngimage = cairosvg.svg2png(bytestring=svgimage.encode())
        self.pixmap.loadFromData(pngimage)
        self.image_board.setPixmap(self.pixmap)

        if self.flip_flag:
            self.player_top.setText(game.black)
            self.player_bottom.setText(game.white)

        if not self.flip_flag:
            self.player_top.setText(game.white)
            self.player_bottom.setText(game.black)

        if self.hmove_nr > 0:
            if self.hmove_nr % 2 == 1:
                prefix = f"{(self.hmove_nr + 1) // 2}. "
            else:
                prefix = f"{self.hmove_nr // 2}... "
            self.move_label.setText(
                f"Played Move: {prefix}"
                f"{game.moves[self.hmove_nr - 1]}")
        else:
            self.move_label.setText(
                f"Played Move: ")

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
            self.bt_dict["Next >"].animateClick()

        elif event.key() == Qt.Key.Key_Left:
            self.bt_dict["< Last"].animateClick()

        elif event.key() == Qt.Key.Key_F:
            self.flip_flag = not self.flip_flag
            self.update_board()

    def previous_move(self):
        if self.hmove_nr > 0:
            self.board.pop()
            self.hmove_nr -= 1
            self.update_board()

    def create_radiobutton_list(self, title, options):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        title = QLabel(title)
        title.setFont(self.header_font)
        layout.addWidget(title)
        rb_dict = {}
        for option in options:
            rb = QRadioButton(option)
            rb_dict[rb] = rb
            layout.addWidget(rb)
        layout.addSpacing(10)
        return layout

    def create_checkbox_list(self, title, options):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        title = QLabel(title)
        title.setFont(self.header_font)
        layout.addWidget(title)
        cb_dict = {}
        for option in options:
            cb = QCheckBox(option)
            cb_dict[cb] = cb
            layout.addWidget(cb)
        layout.addSpacing(10)
        return layout

    def create_navi_buttons(self, buttons):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bt_dict = {}
        for button in buttons:
            bt = QPushButton(button)
            bt_dict[button] = bt
            layout.addWidget(bt)
        layout.addSpacing(10)
        return layout, bt_dict

    def create_board(self):
        layout = QVBoxLayout()
        layout.addWidget(self.player_top)
        layout.addWidget(self.image_board)
        layout.addWidget(self.player_bottom)
        layout.addSpacing(10)
        return layout


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
        self.eval_array = []
        for i, part in enumerate(pgn_parts):
            if part == keyword:
                self.eval_array.append(pgn_parts[i + 1][:-1])


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
