import io
import chess
import sqlite3
import cairosvg
import requests
import chess.pgn
import chess.svg
import database as db
from PyQt6.QtCore import Qt
from PyQt6.QtGui import (QPixmap,
                         QFont)
from tags import tag_dict as tags
from PyQt6.QtWidgets import (QApplication,
                             QLabel,
                             QWidget,
                             QPushButton,
                             QVBoxLayout,
                             QHBoxLayout,
                             QButtonGroup,
                             QRadioButton,
                             QCheckBox,
                             QTabWidget,
                             QTabBar, QFrame)


# noinspection PyUnresolvedReferences


class Window(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("ChessMoves")
        self.setFixedSize(1000, 800)
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
        self.player_font = QFont()
        self.player_font.setBold(True)
        self.player_font.setPointSize(14)

        self.tabs = QTabWidget()
        self.tabs.setTabBar(FixedWidthTabBar())
        self.tabs.tabBar().setDrawBase(False)

        tab_tag = QWidget()
        tab_report = QWidget()
        tab_train = QWidget()

        self.tag_dict = {}
        self.bt_dict = {}
        self.player_top = QLabel()
        self.player_top.setFont(self.player_font)
        self.player_bottom = QLabel()
        self.player_bottom.setFont(self.player_font)
        self.image_board = QLabel()
        self.pixmap = QPixmap()
        self.move_notation = QLabel()
        self.move_cost = QLabel()
        self.eval = QLabel()

        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.Shape.Box)
        self.frame.setObjectName("MyFrame")
        self.frame.setStyleSheet("#MyFrame { border: 3px solid #262626; }")

        # --------------------------------------------------------------------
        # create widgets and layouts

        lay_board = self.create_board()

        lay_played_move = self.create_played_move_info()

        lay_buttons = self.create_buttons(["Load",
                                           "URL",
                                           "PGN",
                                           "FEN",
                                           "Save"])

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
        board_layout.setAlignment(Qt.AlignmentFlag.AlignTop |
                                  Qt.AlignmentFlag.AlignHCenter)
        board_layout.addLayout(lay_board)
        board_layout.addLayout(lay_played_move)
        board_layout.addLayout(lay_buttons)

        tag_layout = QHBoxLayout()
        tag_layout.setAlignment(Qt.AlignmentFlag.AlignTop |
                                Qt.AlignmentFlag.AlignHCenter)
        tag_layout.setContentsMargins(25, 15, 0, 0)
        tag_layout_l = QVBoxLayout()
        tag_layout_l.setAlignment(Qt.AlignmentFlag.AlignTop)
        tag_layout_r = QVBoxLayout()
        tag_layout_r.setAlignment(Qt.AlignmentFlag.AlignTop)
        tag_layout_l.addLayout(tag_layout_dict["GAME PHASE"])
        tag_layout_l.addLayout(tag_layout_dict["MISSED RESPONSE"])
        tag_layout_l.addLayout(tag_layout_dict["DIAGNOSIS"])
        tag_layout_r.addLayout(tag_layout_dict["TACTICAL THEME"])
        tag_layout_r.addLayout(tag_layout_dict["POSITIONAL DISADVANTAGE"])
        tag_layout.addLayout(tag_layout_l)
        tag_layout.addSpacing(20)
        tag_layout.addLayout(tag_layout_r)

        master_layout = QHBoxLayout()
        master_layout.addLayout(board_layout, 4)
        master_layout.addLayout(tag_layout, 3)
        master_layout.setContentsMargins(50, 30, 50, 30)

        tab_tag.setLayout(master_layout)

        self.tabs.addTab(tab_tag, "Tag")
        self.tabs.addTab(tab_report, "Report")
        self.tabs.addTab(tab_train, "Train")

        # --------------------------------------------------------------------

        self.initialize_board()

        # --------------------------------------------------------------------
        # button connections

        self.bt_dict["Load"].clicked.connect(self.load_game)

        self.bt_dict["URL"].clicked.connect(
            lambda: self.copy_text(self.game.url))
        self.bt_dict["PGN"].clicked.connect(
            lambda: self.copy_text(self.game.pgn))
        self.bt_dict["FEN"].clicked.connect(
            lambda: self.copy_text(self.game.board.fen()))

        self.bt_dict["Save"].clicked.connect(self.save_analysis)

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
                                   size=480
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
                                   size=480
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

            self.move_notation.setText(
                f"{prefix}{self.game.moves[self.hmove_nr - 1]}")

            self.move_cost.setText(
                f"{self.game.cost_list[self.hmove_nr - 1]}")

            self.set_move_color()

            current_eval = self.game.eval_list[self.hmove_nr - 1]

            if isinstance(current_eval, float):
                if not (current_eval < 0):
                    self.eval.setText(f"+{current_eval}")
                else:
                    self.eval.setText(f"{current_eval}")

            if isinstance(current_eval, str):
                self.eval.setText(current_eval)

        else:
            self.move_notation.setText("-")
            self.move_cost.setText("-")
            self.eval.setText("-")

    def set_move_color(self):
        cost = self.move_cost.text()
        if cost == "Unavoidable Checkmate" or cost == "Missed Checkmate":
            self.move_cost.setStyleSheet("color: #EC7A5A")
            self.move_notation.setStyleSheet("color: #EC7A5A")
        else:
            cost = float(cost)
            if .5 <= cost < 1:
                self.move_cost.setStyleSheet("color: #4AA8CF")
                self.move_notation.setStyleSheet("color: #4AA8CF")
            elif 1 <= cost < 3:
                self.move_cost.setStyleSheet("color: #E0B953")
                self.move_notation.setStyleSheet("color: #E0B953")
            elif cost >= 3:
                self.move_cost.setStyleSheet("color: #EC7A5A")
                self.move_notation.setStyleSheet("color: #EC7A5A")
            else:
                self.move_cost.setStyleSheet("color: #D3D3D3")
                self.move_notation.setStyleSheet("color: #D3D3D3")

    def set_board_orientation(self):
        if self.flip_flag:
            self.player_top.setText(self.game.black)
            self.player_bottom.setText(self.game.white)

        if not self.flip_flag:
            self.player_top.setText(self.game.white)
            self.player_bottom.setText(self.game.black)

    def next_move(self):
        if (
                self.game is not None
                and
                (self.hmove_nr < len(self.game.pushable_moves))
        ):
            if self.hmove_nr > 0:
                self.save_tags(tag_list=self.read_tags(),
                               hmove_nr=self.hmove_nr)
            self.hmove_nr += 1
            self.reset_tags()
            self.load_tags(hmove_nr=self.hmove_nr)

            self.move_pushable = self.game.pushable_moves[self.hmove_nr - 1]
            self.game.board.push(self.move_pushable)
            self.update_board()

    def previous_move(self):
        if (
                self.game is not None
                and
                self.hmove_nr > 0
        ):
            self.save_tags(tag_list=self.read_tags(),
                           hmove_nr=self.hmove_nr)
            self.hmove_nr -= 1
            self.reset_tags()
            self.load_tags(hmove_nr=self.hmove_nr)

            if self.hmove_nr == 0:
                self.move_notation.setText("-")
                self.move_cost.setText("-")
                self.eval.setText("-")

            self.game.board.pop()
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

        elif event.key() == Qt.Key.Key_S:
            self.save_analysis()

    def create_tags(self, tag_title, tag_ops, tag_type):
        layout = QVBoxLayout()
        layout.addSpacing(20)
        title = QLabel(tag_title)
        title.setFont(self.header_font)
        layout.addWidget(title)
        if tag_type == "cb":
            for op in tag_ops:
                tag = QCheckBox(op)
                self.tag_dict[op] = tag
                layout.addWidget(tag)
        elif tag_type == "rb":
            self.rb_group = QButtonGroup()
            for op in tag_ops:
                tag = QRadioButton(op)
                self.rb_group.addButton(tag)
                self.tag_dict[op] = tag
                layout.addWidget(tag)
        else:
            return
        return layout

    def create_buttons(self, buttons):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(0, 15, 0, 0)
        tooltip_dict = {
            "Load": "Load game from Lichess (L)",
            "URL": "Copy Lichess URL (U)",
            "PGN": "Copy PGN of current game (P)",
            "FEN": "Copy FEN of current position (N)",
            "Save": "Save tags into database (S)"
        }
        for button in buttons:
            bt = QPushButton(button)
            bt.setToolTip(tooltip_dict[button])
            self.bt_dict[button] = bt
            if button == "Load" or button == "Save":
                bt.setFixedWidth(100)
            else:
                bt.setFixedWidth(70)
            layout.addWidget(bt)
        return layout

    def create_board(self):
        layout = QVBoxLayout()
        layout.addWidget(self.player_top)
        layout.addWidget(self.image_board)
        layout.addWidget(self.player_bottom)
        return layout

    def create_played_move_info(self):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(20, 30, 0, 15)
        layout_title = QVBoxLayout()
        layout_value = QVBoxLayout()
        move_label = QLabel("Move:")
        move_label.setFont(self.header_font)
        cost_label = QLabel("Cost:")
        cost_label.setFont(self.header_font)
        eval_label = QLabel("Evaluation:")
        eval_label.setFont(self.header_font)

        layout_title.addWidget(move_label)
        layout_title.addWidget(cost_label)
        layout_title.addWidget(eval_label)

        layout_value.addWidget(self.move_notation)
        layout_value.addWidget(self.move_cost)
        layout_value.addWidget(self.eval)

        layout.addLayout(layout_title)
        layout.addSpacing(10)
        layout.addLayout(layout_value)

        return layout

    def copy_text(self, text):
        QApplication.clipboard().setText(text)

    def load_game(self):
        # game_url = QApplication.clipboard().text()
        # game_url = "https://lichess.org/study/eP6xGQfo/8kz0yG5n"
        game_url = "https://lichess.org/HbXe1F1j/black"
        if "study" in game_url:
            my_token = "lip_XB7WRyKqvpEnfFW9iHox"
            self.game_id = game_url.split("study/")[1]
            req_game = requests.get(
                f"https://lichess.org/api/study/{self.game_id}.pgn",
                headers={"Authorization": f"Bearer {my_token}"})
        else:
            self.game_id = game_url.split(".org/")[1].split("/")[0]
            req_game = requests.get(
                f"https://lichess.org/game/export/{self.game_id}")

        self.game = Game(req_game)

        if self.game.black in \
                ["GrayArmy", "Mohammad Shams", "Mohammad Shams-Ahmar"]:
            self.flip_flag = not self.flip_flag

        self.update_board()

    def read_tags(self):
        tag_list = []
        for key, value in self.tag_dict.items():
            if value.isChecked():
                tag_list.append(key)
        return tag_list

    def save_tags(self, tag_list, hmove_nr):
        self.game.tag_move_list[hmove_nr - 1] = tag_list

    def load_tags(self, hmove_nr):
        tag_list = self.game.tag_move_list[hmove_nr - 1]
        for tag in tag_list:
            self.tag_dict[tag].setChecked(True)

    def reset_tags(self):
        self.rb_group.setExclusive(False)
        for value in self.tag_dict.values():
            value.setChecked(False)
        self.rb_group.setExclusive(True)

    def save_analysis(self):

        tag_list = self.read_tags()
        self.save_tags(tag_list, self.hmove_nr)

        db_file_name = "chess_moves.db"
        conn = sqlite3.connect(db_file_name)
        cursor = conn.cursor()

        db.initialize_database(cursor)

        game_id = db.save_game(cursor=cursor,
                               lichess_id=self.game_id,
                               date=self.game.date,
                               white=self.game.white,
                               black=self.game.black)

        for imove in range(self.hmove_nr):
            move_id = db.save_move(cursor=cursor,
                                   game_id=game_id,
                                   hmove_nr=imove + 1,
                                   move_cost=self.game.cost_list[imove])

            tag_list = self.game.tag_move_list[imove]
            for tag in tag_list:
                tag_id = db.save_tag(cursor=cursor,
                                     tag=tag)

                db.save_move_tag(cursor=cursor,
                                 move_id=move_id,
                                 tag_id=tag_id)

        try:
            # all database operations
            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()


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
                # self.eval_list.append(pgn_parts[i + 1][:-1])
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

        # create a preallocated list to store tags for each move
        self.tag_move_list = [[] for _ in range(len(self.moves))]


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
