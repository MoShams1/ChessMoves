# DONE the status should reset upon pushing next move
#todo: the status of tags should reappear once coming back to the same move
import io
import chess
import chess.pgn
import chess.svg
import cairosvg
from PyQt6.QtWidgets import (
    QApplication, QLabel, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QRadioButton, QCheckBox, QTabWidget, QTabBar)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
import requests
from tags import tag_dict as tags


# noinspection PyUnresolvedReferences


class Window(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("ChessMoves")
        self.setFixedSize(950, 670)
        self.setStyleSheet("""
        QWidget {
        color: #D3D3D3;
        }
        """)

        # --------------------------------------------------------------------
        # attributes

        self.game = None
        self.move_pushable = None
        self.flip_flag = True
        self.hmove_nr = 0

        self.header_font = QFont()
        self.header_font.setBold(True)

        self.tabs = QTabWidget()
        self.tabs.setTabBar(FixedWidthTabBar())
        self.tabs.tabBar().setDrawBase(False)

        tab_tag = QWidget()
        tab_report = QWidget()
        tab_train = QWidget()

        self.tag_dict = {}
        self.bt_dict = {}
        self.load_bt = QPushButton()
        self.player_top = QLabel()
        self.image_board = QLabel()
        self.pixmap = QPixmap()
        self.player_bottom = QLabel()
        self.move_notation = QLabel()
        self.move_cost = QLabel()
        self.eval = QLabel()

        # --------------------------------------------------------------------
        # create widgets and layouts

        lay_board = self.create_board()

        lay_played_move = self.create_played_move_row()

        lay_buttons = self.create_buttons(
            ["Load Game", "URL", "PGN", "FEN"])

        tag_layout_dict = {}
        for key in list(tags.keys()):
            tag_title = key.split('_')[0]
            tag_ops = tags[key]
            tag_type = key.split('_')[1]
            tag_layout_dict[tag_title] = (
                self.create_tags(tag_title, tag_ops, tag_type))

        # --------------------------------------------------------------------
        # organize layouts

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.tabs)

        board_layout = QVBoxLayout()
        board_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        board_layout.setContentsMargins(20, 10, 20, 0)
        board_layout.addLayout(lay_board)
        board_layout.addSpacing(10)
        board_layout.addLayout(lay_buttons)
        board_layout.addSpacing(10)
        board_layout.addLayout(lay_played_move)

        tag_layout = QHBoxLayout()
        tag_layout.setContentsMargins(20, 35, 20, 10)
        tag_layout_l = QVBoxLayout()
        tag_layout_l.setAlignment(Qt.AlignmentFlag.AlignTop)
        tag_layout_r = QVBoxLayout()
        tag_layout_r.setAlignment(Qt.AlignmentFlag.AlignTop)
        tag_layout_l.addLayout(tag_layout_dict["Game Phase"])
        tag_layout_l.addLayout(tag_layout_dict["Missed Response"])
        tag_layout_l.addLayout(tag_layout_dict["Diagnosis"])
        tag_layout_r.addLayout(tag_layout_dict["Tactical Theme"])
        tag_layout_r.addLayout(tag_layout_dict["Positional Disadvantage"])
        tag_layout.addLayout(tag_layout_l)
        tag_layout.addLayout(tag_layout_r)

        master_layout = QHBoxLayout()
        master_layout.addLayout(board_layout, 0)
        master_layout.addLayout(tag_layout, 1)

        tab_tag.setLayout(master_layout)

        self.tabs.addTab(tab_tag, "Tag")
        self.tabs.addTab(tab_report, "Report")
        self.tabs.addTab(tab_train, "Train")

        # --------------------------------------------------------------------

        self.initialize_board()

        # --------------------------------------------------------------------
        # button connections

        self.bt_dict["Load Game"].clicked.connect(self.load_game)

        self.bt_dict["URL"].clicked.connect(
            lambda: self.copy_text(self.game.url))
        self.bt_dict["PGN"].clicked.connect(
            lambda: self.copy_text(self.game.pgn))
        self.bt_dict["FEN"].clicked.connect(
            lambda: self.copy_text(self.game.board.fen()))

    def initialize_board(self):
        svgimage = chess.svg.board(board=chess.Board(),
                                   orientation=self.flip_flag,
                                   lastmove=self.move_pushable,
                                   colors={
                                       "square light": "#B0AA98",
                                       "square dark": "#827A68",
                                       "square light lastmove": "#a1ad68",
                                       "square dark lastmove": "#a1ad68"
                                   },
                                   coordinates=True,
                                   size=400
                                   )

        pngimage = cairosvg.svg2png(bytestring=svgimage.encode())
        self.pixmap.loadFromData(pngimage)
        self.image_board.setPixmap(self.pixmap)

        self.player_top.setText("?")
        self.player_bottom.setText("?")
        self.move_notation.setText("?")
        self.move_cost.setText("?")
        self.eval.setText("?")

    def update_board(self):
        svgimage = chess.svg.board(board=self.game.board,
                                   orientation=self.flip_flag,
                                   lastmove=self.move_pushable,
                                   colors={
                                       "square light": "#B0AA98",
                                       "square dark": "#827A68",
                                       "square light lastmove": "#a1ad68",
                                       "square dark lastmove": "#a1ad68"
                                   },
                                   coordinates=True,
                                   size=400
                                   )

        pngimage = cairosvg.svg2png(bytestring=svgimage.encode())
        self.pixmap.loadFromData(pngimage)
        self.image_board.setPixmap(self.pixmap)

        self.set_board_orientation()

        if self.hmove_nr > 0:

            if self.hmove_nr % 2 == 1:
                prefix = f"{(self.hmove_nr + 1) // 2}. "

            else:
                prefix = f"{self.hmove_nr // 2}... "

            self.move_notation.setText(f"{prefix}"
                                       f"{self.game.moves[self.hmove_nr - 1]}")
            self.move_cost.setText(f"{self.game.cost_list[self.hmove_nr - 1]}")
            current_eval = self.game.eval_list[self.hmove_nr - 1]
            if not (current_eval < 0):
                self.eval.setText(f"+{current_eval}")
            else:
                self.eval.setText(f"{current_eval}")

        else:
            self.move_notation.setText("-")
            self.move_cost.setText("-")
            self.eval.setText("-")

    def set_board_orientation(self):
        if self.flip_flag:
            self.player_top.setText(self.game.black)
            self.player_bottom.setText(self.game.white)

        if not self.flip_flag:
            self.player_top.setText(self.game.white)
            self.player_bottom.setText(self.game.black)

    def next_move(self):
        a = ["Opening", "Middlegame", "Endgame"]
        if self.game is not None and (self.hmove_nr < len(
                self.game.pushable_moves)):
            self.move_pushable = self.game.pushable_moves[self.hmove_nr]
            self.game.board.push(self.move_pushable)
            self.hmove_nr += 1
            self.update_board()
            self.read_tags()
            self.reset_tags()

    def previous_move(self):
        if self.game is not None and self.hmove_nr > 0:
            self.game.board.pop()
            self.hmove_nr -= 1
            self.update_board()

    def keyPressEvent(self, event):

        if event.key() == Qt.Key.Key_Escape:
            self.close()

        elif event.key() == Qt.Key.Key_Right:
            self.next_move()

        elif event.key() == Qt.Key.Key_Left:
            self.previous_move()

        elif event.key() == Qt.Key.Key_F:
            self.flip_flag = not self.flip_flag
            self.update_board()

        elif event.key() == Qt.Key.Key_L:
            self.load_game()

        elif event.key() == Qt.Key.Key_U:
            self.copy_text(self.game.url)

        elif event.key() == Qt.Key.Key_P:
            self.copy_text(self.game.pgn)

        elif event.key() == Qt.Key.Key_N:
            self.copy_text(self.game.board.fen())

    def create_tags(self, tag_title, tag_ops, tag_type):
        layout = QVBoxLayout()
        title = QLabel(tag_title)
        title.setFont(self.header_font)
        layout.addWidget(title)
        if tag_type == "cb":
            for op in tag_ops:
                tag = QCheckBox(op)
                self.tag_dict[op] = tag
                layout.addWidget(tag)
        elif tag_type == "rb":
            for op in tag_ops:
                tag = QRadioButton(op)
                self.tag_dict[op] = tag
                layout.addWidget(tag)
        else:
            return
        return layout

    def create_buttons(self, buttons):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for button in buttons:
            bt = QPushButton(button)
            self.bt_dict[button] = bt
            if button == "Load Game":
                bt.setFixedWidth(100)
            else:
                bt.setFixedWidth(50)
            layout.addWidget(bt)
        return layout

    def create_board(self):
        layout = QVBoxLayout()
        layout.addWidget(self.player_top)
        layout.addWidget(self.image_board)
        layout.addWidget(self.player_bottom)
        return layout

    def create_played_move_row(self):
        layout_row = QHBoxLayout()
        layout_row.addSpacing(40)
        layout_move = QHBoxLayout()
        layout_move.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout_cost = QHBoxLayout()
        layout_cost.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout_eval = QHBoxLayout()
        layout_eval.setAlignment(Qt.AlignmentFlag.AlignLeft)
        move_label = QLabel("Move:")
        move_label.setFont(self.header_font)
        cost_label = QLabel("Cost:")
        cost_label.setFont(self.header_font)
        eval_label = QLabel("Eval.:")
        eval_label.setFont(self.header_font)
        layout_move.addWidget(move_label)
        layout_move.addWidget(self.move_notation)
        layout_cost.addWidget(cost_label)
        layout_cost.addWidget(self.move_cost)
        layout_eval.addWidget(eval_label)
        layout_eval.addWidget(self.eval)
        layout_row.addLayout(layout_move)
        layout_row.addLayout(layout_cost)
        layout_row.addLayout(layout_eval)
        return layout_row

    def copy_text(self, text):
        QApplication.clipboard().setText(text)

    def load_game(self):
        game_url = QApplication.clipboard().text()
        if "study" in game_url:
            my_token = "lip_XB7WRyKqvpEnfFW9iHox"
            game_id = game_url.split("study/")[1]
            req_game = requests.get(
                f"https://lichess.org/api/study/{game_id}.pgn",
                headers={"Authorization": f"Bearer {my_token}"})
        else:
            game_id = game_url.split(".org/")[1].split("/")[0]
            req_game = requests.get(
                f"https://lichess.org/game/export/{game_id}")

        self.game = Game(req_game)

        if self.game.black in \
                ["GrayArmy", "Mohammad Shams", "Mohammad Shams-Ahmar"]:
            self.flip_flag = not self.flip_flag

        self.update_board()

    def read_tags(self):
        tags_status = {}
        for key, value in self.tag_dict.items():
            tags_status[key] = value.isChecked()

    def reset_tags(self):
        for value in self.tag_dict.values():
            value.setChecked(False)



class Game:

    def __init__(self, req_game):

        # ----------------------------------------------------------------
        # load pgn file

        self.parsed_game = chess.pgn.read_game(io.StringIO(req_game.text))

        # ----------------------------------------------------------------
        # extract board
        self.board = self.parsed_game.board()

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
        self.pgn = str(self.parsed_game)
        pgn_parts = self.pgn.split()
        keyword = "[%eval"
        self.eval_list = []
        for i, part in enumerate(pgn_parts):
            if part == keyword:
                try:
                    self.eval_list.append(float(pgn_parts[i + 1][:-1]))
                except ValueError:
                    self.eval_list.append(pgn_parts[i + 1][:-1])
        if len(self.eval_list) == len(self.moves) - 1:
            self.eval_list.append(self.parsed_game.headers["Result"])

        # ----------------------------------------------------------------
        # calculate move cost

        self.cost_list = []

        for ieval, evaluation in enumerate(self.eval_list):

            if ieval == 0:
                self.cost_list.append(self.eval_list[ieval])

            else:
                last_eval = self.eval_list[ieval - 1]
                curr_eval = self.eval_list[ieval]

                if isinstance(last_eval, float) and \
                        isinstance(curr_eval, str):
                    self.cost_list.append("Unavoidable Checkmate")

                if isinstance(last_eval, str) and \
                        isinstance(curr_eval, str):
                    self.cost_list.append(0)

                if isinstance(last_eval, str) and \
                        isinstance(curr_eval, float):
                    self.cost_list.append("Missed Checkmate")

                if isinstance(last_eval, float) and \
                        isinstance(curr_eval, float):
                    self.cost_list.append(round(curr_eval - last_eval, 2))

            if isinstance(self.cost_list[-1], float):

                if ieval % 2 == 0:
                    self.cost_list[-1] = -self.cost_list[-1]

                if not (self.cost_list[-1] > 0):
                    self.cost_list[-1] = 0

        # ----------------------------------------------------------------
        # extract url
        self.url = self.parsed_game.headers["Site"]


class FixedWidthTabBar(QTabBar):

    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        size.setWidth(100)
        return size


# --------------------------------------------------------------------
# run application

app = QApplication([])

window = Window()
window.show()
app.exec()
