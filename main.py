# todo: [] check if game exists in database and show message
# todo: if game already exists
#   [] load tags
#   [] find game_id for later save address
# todo: [] handle connectio error: requests.exceptions.ConnectionError

import io
import os
import chess
import sqlite3
import cairosvg
import requests
import chess.pgn
import chess.svg
import database as db
from tags import tag_source
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QFont
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
                             QTabBar,
                             QGraphicsOpacityEffect,
                             QFrame)


# noinspection PyUnresolvedReferences


class Window(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("ChessMoves")
        # self.setFixedSize(1000, 800)
        self.resize(1000, 800)
        self.setStyleSheet("""
        QWidget {
        color: #D3D3D3;
        }
        """)

        # --------------------------------------------------------------------
        #

        self.game = None
        self.lichess_id = None
        self.move_obj = None
        self.flip_flag = True
        self.current_move_num = 0

        # --------------------------------------------------------------------
        # create widgets

        self.tab_widget = QTabWidget()

        self.tab_tag = QWidget()
        self.tab_report = QWidget()
        self.tab_train = QWidget()

        self.player_top_lbl = QLabel()
        self.player_bottom_lbl = QLabel()

        self.image_board_lbl = QLabel()
        self.pixmap = QPixmap()

        self.move_notation_lbl = QLabel()
        self.move_cost_lbl = QLabel()
        self.eval_lbl = QLabel()

        self.button_widgets = {}

        self.rb_group = QButtonGroup()
        self.tag_widgets = {}

        # --------------------------------------------------------------------
        # create styles

        self.tab_widget.setTabBar(FixedWidthTabBar())
        self.tab_widget.tabBar().setDrawBase(False)

        self.tag_header_font = QFont()
        self.tag_header_font.setBold(True)

        self.player_font = QFont()
        self.player_font.setBold(True)
        self.player_font.setPointSize(14)
        self.player_top_lbl.setFont(self.player_font)
        self.player_bottom_lbl.setFont(self.player_font)

        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.Shape.Box)
        self.frame.setObjectName("MyFrame")
        self.frame.setStyleSheet("#MyFrame { border: 3px solid #262626; }")

        # --------------------------------------------------------------------
        # create layouts

        board_layout = self.create_board_layout()
        button_layout = self.create_button_layout()
        eval_layout = self.create_eval_layout()
        tag_layout = self.create_tag_layout()

        # --------------------------------------------------------------------
        # organize layouts

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.layout().addWidget(self.tab_widget)

        game_layout = QVBoxLayout()
        game_layout.setAlignment(Qt.AlignmentFlag.AlignTop |
                                 Qt.AlignmentFlag.AlignHCenter)
        game_layout.addLayout(board_layout)
        game_layout.addLayout(eval_layout)
        game_layout.addLayout(button_layout)

        tag_tab_master_layout = QHBoxLayout()
        tag_tab_master_layout.addLayout(game_layout, 4)
        tag_tab_master_layout.addLayout(tag_layout, 3)
        tag_tab_master_layout.setContentsMargins(50, 30, 50, 30)

        self.tab_tag.setLayout(tag_tab_master_layout)

        self.tab_widget.addTab(self.tab_tag, "Tag")
        self.tab_widget.addTab(self.tab_report, "Report")
        self.tab_widget.addTab(self.tab_train, "Train")

        # --------------------------------------------------------------------

        self.initialize_board()

        # --------------------------------------------------------------------
        # button connections

        self.button_widgets["Load"].clicked.connect(self.load_game)

        self.button_widgets["URL"].clicked.connect(
            lambda: self.copy_text(self.game.url,
                                   "Game URL copied to clipboard"))
        self.button_widgets["PGN"].clicked.connect(
            lambda: self.copy_text(self.game.pgn,
                                   "Game PGN copied to clipboard"))
        self.button_widgets["FEN"].clicked.connect(
            lambda: self.copy_text(self.game.board.fen(),
                                   "Position copied to clipboard"))

        self.button_widgets["Save"].clicked.connect(self.save_analysis)

    # ///////////////////////////////////////////////////////////////////////
    # BOARD BEHAVIOR AND VISUALS

    def initialize_board(self):
        svgimage = chess.svg.board(board=chess.Board(),
                                   orientation=self.flip_flag,
                                   lastmove=self.move_obj,
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
        self.image_board_lbl.setPixmap(self.pixmap)

        self.player_top_lbl.setText("?")
        self.player_bottom_lbl.setText("?")
        self.move_notation_lbl.setText("?")
        self.move_cost_lbl.setText("?")
        self.eval_lbl.setText("?")

    def update_board(self):

        self.set_board_orientation()

        if self.current_move_num > 0:

            if self.current_move_num % 2 == 1:
                prefix = f"{(self.current_move_num + 1) // 2}. "

            else:
                prefix = f"{self.current_move_num // 2}... "

            self.move_notation_lbl.setText(
                f"{prefix}{self.game.moves[self.current_move_num - 1]}")

            self.move_cost_lbl.setText(
                f"{self.game.cost_list[self.current_move_num - 1]}")

            self.set_move_cost_color()

            current_eval = self.game.eval_list[self.current_move_num - 1]

            if isinstance(current_eval, float):
                if not (current_eval < 0):
                    self.eval_lbl.setText(f"+{current_eval}")
                else:
                    self.eval_lbl.setText(f"{current_eval}")

            if isinstance(current_eval, str):
                self.eval_lbl.setText(current_eval)

        else:
            self.move_notation_lbl.setText("-")
            self.move_cost_lbl.setText("-")
            self.eval_lbl.setText("-")

    def set_move_cost_color(self):
        cost = self.move_cost_lbl.text()
        if cost == "Unavoidable Checkmate" or cost == "Missed Checkmate":
            self.move_cost_lbl.setStyleSheet("color: #EC7A5A")
            self.move_notation_lbl.setStyleSheet("color: #EC7A5A")
        else:
            cost = float(cost)
            if .5 <= cost < 1:
                self.move_cost_lbl.setStyleSheet("color: #4AA8CF")
                self.move_notation_lbl.setStyleSheet("color: #4AA8CF")
            elif 1 <= cost < 3:
                self.move_cost_lbl.setStyleSheet("color: #E0B953")
                self.move_notation_lbl.setStyleSheet("color: #E0B953")
            elif cost >= 3:
                self.move_cost_lbl.setStyleSheet("color: #EC7A5A")
                self.move_notation_lbl.setStyleSheet("color: #EC7A5A")
            else:
                self.move_cost_lbl.setStyleSheet("color: #D3D3D3")
                self.move_notation_lbl.setStyleSheet("color: #D3D3D3")

    def set_board_orientation(self):
        if self.flip_flag:
            self.player_top_lbl.setText(self.game.black)
            self.player_bottom_lbl.setText(self.game.white)

        if not self.flip_flag:
            self.player_top_lbl.setText(self.game.white)
            self.player_bottom_lbl.setText(self.game.black)

    def next_move(self):
        if (
                self.game is not None
                and
                (self.current_move_num < len(self.game.move_obj_list))
        ):
            if self.current_move_num > 0:
                self.save_tags(tag_list=self.read_tags(),
                               move_nr=self.current_move_num)
            self.current_move_num += 1
            self.reset_tags()
            self.load_tags(move_nr=self.current_move_num)

            self.move_obj = self.game.move_obj_list[self.current_move_num - 1]
            self.game.board.push(self.move_obj)
            self.update_board()

    def previous_move(self):
        if (
                self.game is not None
                and
                self.current_move_num > 0
        ):
            self.save_tags(tag_list=self.read_tags(),
                           move_nr=self.current_move_num)
            self.current_move_num -= 1
            self.reset_tags()
            self.load_tags(move_nr=self.current_move_num)

            if self.current_move_num == 0:
                self.move_notation_lbl.setText("-")
                self.move_cost_lbl.setText("-")
                self.eval_lbl.setText("-")

            self.game.board.pop()
            self.update_board()

    def show_message(self, text):

        overlay = QWidget(self)
        overlay.setGeometry(self.rect())

        layout = QVBoxLayout(overlay)
        layout.setAlignment(Qt.AlignmentFlag.AlignRight |
                            Qt.AlignmentFlag.AlignBottom)
        layout.setContentsMargins(0, 0, 20, 20)

        label = QLabel(text)
        label.setStyleSheet("""
            QLabel {
                background-color: rgb(40, 40, 40);
                padding: 5px;
                border-radius: 7px;
            }
        """)

        layout.addWidget(label)
        overlay.show()

        # Add opacity effect
        effect = QGraphicsOpacityEffect(label)
        effect.setOpacity(1)
        label.setGraphicsEffect(effect)

        # Wait, then fade out
        def fade_out():
            animation = QPropertyAnimation(effect, b"opacity")
            animation.setDuration(500)  # fade duration in ms
            animation.setStartValue(effect.opacity())
            animation.setEndValue(0)
            animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
            animation.finished.connect(overlay.deleteLater)
            animation.start()

            overlay.animation = animation

        QTimer.singleShot(1500, fade_out)

        # ///////////////////////////////////////////////////////////////////////
        # CREATE LAYOUTS

    def create_board_layout(self):
        layout = QVBoxLayout()
        layout.addWidget(self.player_top_lbl)
        layout.addWidget(self.image_board_lbl)
        layout.addWidget(self.player_bottom_lbl)
        return layout

    def create_button_layout(self):
        button_names = ["Load", "URL", "PGN", "FEN", "Save"]
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(0, 15, 0, 0)
        button_tootips = {
            "Load": "Load game (L)",
            "URL": "Copy game URL (U)",
            "PGN": "Copy game PGN (P)",
            "FEN": "Copy position FEN (N)",
            "Save": "Save analysis (S)"
        }
        for button_name in button_names:
            button_widget = QPushButton(button_name)
            button_widget.setToolTip(button_tootips[button_name])
            self.button_widgets[button_name] = button_widget
            if button_name == "Load" or button_name == "Save":
                button_widget.setFixedWidth(100)
            else:
                button_widget.setFixedWidth(70)
            layout.addWidget(button_widget)
        return layout

    def create_eval_layout(self):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(20, 30, 0, 15)
        layout_title = QVBoxLayout()
        layout_value = QVBoxLayout()
        move_label = QLabel("Move:")
        move_label.setFont(self.tag_header_font)
        cost_label = QLabel("Cost:")
        cost_label.setFont(self.tag_header_font)
        eval_label = QLabel("Evaluation:")
        eval_label.setFont(self.tag_header_font)

        layout_title.addWidget(move_label)
        layout_title.addWidget(cost_label)
        layout_title.addWidget(eval_label)

        layout_value.addWidget(self.move_notation_lbl)
        layout_value.addWidget(self.move_cost_lbl)
        layout_value.addWidget(self.eval_lbl)

        layout.addLayout(layout_title)
        layout.addSpacing(10)
        layout.addLayout(layout_value)

        return layout

    def create_tag_layout(self):

        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop |
                            Qt.AlignmentFlag.AlignHCenter)
        layout.setContentsMargins(25, 15, 0, 0)

        layout_left = QVBoxLayout()
        layout_left.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_right = QVBoxLayout()
        layout_right.setAlignment(Qt.AlignmentFlag.AlignTop)

        for key in list(tag_source.keys()):

            header = key.split('_')[0]
            options = tag_source[key]
            box_type = key.split('_')[1]

            layout_block = QVBoxLayout()
            layout_block.addSpacing(20)
            header_widget = QLabel(header)
            header_widget.setFont(self.tag_header_font)
            layout_block.addWidget(header_widget)

            if box_type == "cb":
                for option in options:
                    option_widget = QCheckBox(option)
                    self.tag_widgets[option] = option_widget
                    layout_block.addWidget(option_widget)

            elif box_type == "rb":
                for option in options:
                    option_widget = QRadioButton(option)
                    self.rb_group.addButton(option_widget)
                    self.tag_widgets[option] = option_widget
                    layout_block.addWidget(option_widget)

            else:
                return

            if (
                    header == "GAME PHASE" or
                    header == "MISSED RESPONSE" or
                    header == "DIAGNOSIS"):
                layout_left.addLayout(layout_block)

            if (
                    header == "TACTICAL THEME" or
                    header == "POSITIONAL DISADVANTAGE"):
                layout_right.addLayout(layout_block)

        layout.addLayout(layout_left)
        layout.addSpacing(20)
        layout.addLayout(layout_right)

        return layout

    # ///////////////////////////////////////////////////////////////////////
    # tags operations

    def read_tags(self):
        tag_list = []
        for key, value in self.tag_widgets.items():
            if value.isChecked():
                tag_list.append(key)
        return tag_list

    def save_tags(self, tag_list, move_nr):
        self.game.tag_move_list[move_nr - 1] = tag_list

    def load_tags(self, move_nr):
        tag_list = self.game.tag_move_list[move_nr - 1]
        for tag in tag_list:
            self.tag_widgets[tag].setChecked(True)

    def reset_tags(self):
        self.rb_group.setExclusive(False)
        for value in self.tag_widgets.values():
            value.setChecked(False)
        self.rb_group.setExclusive(True)

    # ///////////////////////////////////////////////////////////////////////
    # analysis session operations

    def load_game(self):
        # lichess_url = QApplication.clipboard().text()
        # lichess_url = "https://lichess.org/study/eP6xGQfo/8kz0yG5n"
        lichess_url = "https://lichess.org/HbXe1F1j/black"
        if "study" in lichess_url:
            my_token = "lip_XB7WRyKqvpEnfFW9iHox"
            self.lichess_id = lichess_url.split("study/")[1]
            req_game = requests.get(
                f"https://lichess.org/api/study/{self.lichess_id}.pgn",
                headers={"Authorization": f"Bearer {my_token}"})
        else:
            self.lichess_id = lichess_url.split(".org/")[1].split("/")[0]
            req_game = requests.get(
                f"https://lichess.org/game/export/{self.lichess_id}")

        self.game = Game(req_game)

        if self.game.black in \
                ["GrayArmy", "Mohammad Shams", "Mohammad Shams-Ahmar"]:
            self.flip_flag = not self.flip_flag

        self.update_board()
        
        self.show_message("Game loaded")

        db_file_name = "chess_moves.db"
        if os.path.exists(db_file_name):
            conn = sqlite3.connect(db_file_name)
            cursor = conn.cursor()
            db.check_if_game_exists(cursor, self.lichess_id)

            try:
                # all database operations
                conn.commit()

            except Exception:
                conn.rollback()
                raise

            finally:
                conn.close()


    def save_analysis(self):

        tag_list = self.read_tags()
        self.save_tags(tag_list, self.current_move_num)

        db_file_name = "chess_moves.db"
        conn = sqlite3.connect(db_file_name)
        cursor = conn.cursor()

        db.initialize_database(cursor)

        game_id = db.save_game(cursor=cursor,
                               lichess_id=self.lichess_id,
                               date=self.game.date,
                               white=self.game.white,
                               black=self.game.black)

        for imove in range(self.current_move_num):
            move_id = db.save_move(cursor=cursor,
                                   game_id=game_id,
                                   move_nr=imove + 1,
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

        self.show_message("Analysis saved")

    # ///////////////////////////////////////////////////////////////////////
    # shortkeys

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
            self.copy_text(self.game.url,
                           "Game URL copied to clipboard")

        elif event.key() == Qt.Key.Key_P:
            self.copy_text(self.game.pgn,
                           "Game PGN copied to clipboard")

        elif event.key() == Qt.Key.Key_N:
            self.copy_text(self.game.board.fen(),
                           "Position copied to clipboard")


        elif event.key() == Qt.Key.Key_S:
            self.save_analysis()

    # ///////////////////////////////////////////////////////////////////////
    # other functions

    def copy_text(self, text, message):
        QApplication.clipboard().setText(text)
        self.show_message(message)


class FixedWidthTabBar(QTabBar):

    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        size.setWidth(100)
        return size


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

        self.move_obj_list = list(self.parsed_game.mainline_moves())
        self.moves = []
        for pushable_move in self.move_obj_list:
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

        for ieval, _ in enumerate(self.eval_list):

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


# --------------------------------------------------------------------
# run application

app = QApplication([])

window = Window()
window.show()
app.exec()
