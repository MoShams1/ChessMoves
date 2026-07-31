import io
import os
import chess
import sqlite3
import requests
import chess.pgn
import chess.svg
import database as db
from tags import tag_source
from game_panel import GamePanel
from personal_info import lichess_study_token, player_names
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
                             QGraphicsOpacityEffect, QPlainTextEdit)


def run_annotate():
    class AnnotateWindow(QWidget):

        def __init__(self):
            super().__init__()

            self.setWindowTitle("ChessMoves: Annotate")
            self.resize(1000, 900)
            self.setStyleSheet("""
            QWidget {
            color: #D3D3D3;
            }
            """)

            # --------------------------------------------------------------------
            #

            self.game = None
            self.existing_game_id = None
            self.lichess_id = None
            self.move_obj = None
            self.flip_flag = True
            self.current_move_num = 0
            self.game_loaded_flag = False
            self.comment_widget = QPlainTextEdit()
            self.question_widget = QPlainTextEdit()

            # --------------------------------------------------------------------
            # create widgets

            self.player_top_widget = QLabel()
            self.player_bottom_widget = QLabel()

            self.image_board_widget = QLabel()
            self.pixmap = QPixmap()

            self.move_notation_widget = QLabel()
            self.move_cost_widget = QLabel()
            self.eval_widget = QLabel()

            self.button_widgets = {}

            self.rb_group = QButtonGroup()
            self.tag_widgets = {}

            self.game_panel_widget = GamePanel(mode="annotate")

            # --------------------------------------------------------------------
            # create styles

            self.tag_header_font = QFont()
            self.tag_header_font.setBold(True)

            self.message_font = QFont()
            self.message_font.setPointSize(10)

            # --------------------------------------------------------------------
            # create layouts

            tag_layout = self.create_tag_layout()
            button_layout = self.create_button_layout()
            button_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            textbox_layout = self.create_textbox_layout()

            # --------------------------------------------------------------------
            # organize layouts

            master_layout_top = QHBoxLayout()
            master_layout_top.addWidget(self.game_panel_widget, 4)
            master_layout_top.addLayout(tag_layout, 3)

            master_layout = QVBoxLayout()
            master_layout.addLayout(master_layout_top)
            master_layout.addLayout(textbox_layout)
            master_layout.addLayout(button_layout)
            master_layout.setContentsMargins(50, 50, 50, 50)
            self.setLayout(master_layout)
            self.setFocus()

            # --------------------------------------------------------------------

            self.game_panel_widget.show_position(
                board=chess.Board(),
                white_player="?",
                black_player="?",
                orientation=self.flip_flag,
            )

            # --------------------------------------------------------------------
            # button connections

            self.button_widgets["Load"].clicked.connect(self.load_game)
            self.button_widgets["Save"].clicked.connect(
                self.save_analysis_to_db)

            self.button_widgets["URL"].clicked.connect(
                lambda: self.copy_to_clipboard(
                    self.game.url,
                    "Game URL copied to clipboard"))
            self.button_widgets["PGN"].clicked.connect(
                lambda: self.copy_to_clipboard(
                    self.game.pgn,
                    "Game PGN copied to clipboard"))
            self.button_widgets["FEN"].clicked.connect(
                lambda: self.copy_to_clipboard(
                    self.game.board.fen(),
                    "Position copied to clipboard"))

            self.button_widgets["Clear"].clicked.connect(self.clear_tags_in_ui)
            self.button_widgets["Reset"].clicked.connect(self.reset_game_tags)
            self.button_widgets["Close"].clicked.connect(self.close)

        # ///////////////////////////////////////////////////////////////////////
        # BOARD BEHAVIOR AND VISUALS

        def update_board(self):

            if self.current_move_num > 0:

                if self.current_move_num % 2 == 1:
                    prefix = f"{(self.current_move_num + 1) // 2}. "

                else:
                    prefix = f"{self.current_move_num // 2}... "

                self.move_notation_widget.setText(
                    f"{prefix}{self.game.moves[self.current_move_num - 1]}")

                self.move_cost_widget.setText(
                    f"{self.game.cost_list[self.current_move_num - 1]}")

                current_eval = self.game.eval_list[self.current_move_num - 1]

                if isinstance(current_eval, float):
                    if not (current_eval < 0):
                        self.eval_widget.setText(f"+{current_eval}")
                    else:
                        self.eval_widget.setText(f"{current_eval}")

                if isinstance(current_eval, str):
                    self.eval_widget.setText(current_eval)

            else:
                self.move_notation_widget.setText("-")
                self.move_cost_widget.setText("-")
                self.eval_widget.setText("-")

            self.game_panel_widget.show_position(
                board=self.game.board,
                white_player=self.game.white,
                black_player=self.game.black,
                orientation=self.flip_flag,
                last_move=self.move_obj,
                notation=self.move_notation_widget.text(),
                cost=self.move_cost_widget.text(),
                evaluation=self.eval_widget.text(),
            )

            if self.current_move_num > 0:
                self.game_panel_widget.set_move_cost_color()

        def next_move(self):
            if (
                    self.game is not None
                    and
                    (self.current_move_num < len(self.game.move_obj_list))
            ):
                if self.current_move_num > 0:
                    self.save_tags_to_memory(tag_list=self.read_tags_from_ui(),
                                             move_nr=self.current_move_num)
                self.game.fen_before_list[
                    self.current_move_num] = self.game.board.fen()
                self.current_move_num += 1
                self.clear_tags_in_ui()
                self.load_tags_to_ui(move_nr=self.current_move_num)

                self.move_obj = self.game.move_obj_list[
                    self.current_move_num - 1]
                self.game.board.push(self.move_obj)
                self.update_board()

        def previous_move(self):
            if (
                    self.game is not None
                    and
                    self.current_move_num > 0
            ):
                self.save_tags_to_memory(tag_list=self.read_tags_from_ui(),
                                         move_nr=self.current_move_num)
                self.current_move_num -= 1
                self.clear_tags_in_ui()
                self.load_tags_to_ui(move_nr=self.current_move_num)

                self.move_obj = self.game.move_obj_list[
                    self.current_move_num - 1]

                if self.current_move_num == 0:
                    self.move_notation_widget.setText("-")
                    self.move_cost_widget.setText("-")
                    self.eval_widget.setText("-")
                    self.move_obj = None

                self.game.board.pop()
                self.update_board()

        def create_button_layout(self):
            width_small = 50
            width_large = 70
            spacing_small = -10
            spacing_large = 15
            layout = QHBoxLayout()
            buttons = {
                "Load": {"tooltip": "Load game (L)",
                         "width": width_large,
                         "spacing": spacing_small},
                "Save": {"tooltip": "Save analysis (S)",
                         "width": width_large,
                         "spacing": spacing_large},
                "URL": {"tooltip": "Copy game URL (U)",
                        "width": width_small,
                        "spacing": spacing_small},
                "PGN": {"tooltip": "Copy game PGN (P)",
                        "width": width_small,
                        "spacing": spacing_small},
                "FEN": {"tooltip": "Copy position FEN (N)",
                        "width": width_small,
                        "spacing": spacing_large},
                "Clear": {"tooltip": "Clear move tags (C)",
                          "width": width_large,
                          "spacing": spacing_small},
                "Reset": {"tooltip": "Reset game tags (R)",
                          "width": width_large,
                          "spacing": spacing_small},
                "Close": {"tooltip": "Close window (Esc)",
                          "width": width_large,
                          "spacing": spacing_small}
            }

            for button_name, config in buttons.items():
                button_widget = QPushButton(button_name)
                button_widget.setToolTip(config["tooltip"])
                button_widget.setFixedWidth(config["width"])

                self.button_widgets[button_name] = button_widget
                layout.addWidget(button_widget)
                layout.addSpacing(int(config["spacing"]))

            return layout

        def create_tag_layout(self):

            layout = QHBoxLayout()
            layout.setAlignment(Qt.AlignmentFlag.AlignTop |
                                Qt.AlignmentFlag.AlignHCenter)
            layout.setContentsMargins(30, 15, 0, 0)

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
                        header == "GENERAL" or
                        header == "GAME PHASE" or
                        header == "DIAGNOSIS" or
                        header == "MISSED RESPONSE"):
                    layout_left.addLayout(layout_block)
                    layout_left.setAlignment(Qt.AlignmentFlag.AlignVCenter)

                if (
                        header == "TACTICAL THEME" or
                        header == "POSITIONAL THEME"):
                    layout_right.addLayout(layout_block)
                    layout_right.setAlignment(Qt.AlignmentFlag.AlignVCenter)

            layout.addLayout(layout_left)
            layout.addSpacing(20)
            layout.addLayout(layout_right)

            return layout

        def create_textbox_layout(self):
            layout = QHBoxLayout()
            layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            layout.setContentsMargins(20, 20, 20, 20)

            layout_left = QVBoxLayout()
            layout_left.addWidget(QLabel("Comments:"))
            layout_left.addWidget(self.comment_widget)
            self.comment_widget.setFixedWidth(400)

            layout_right = QVBoxLayout()
            layout_right.addWidget(QLabel("Questions:"))
            layout_right.addWidget(self.question_widget)
            self.question_widget.setFixedWidth(400)

            layout.addLayout(layout_left)
            layout.addLayout(layout_right)
            return layout

        def show_message(self, text):

            overlay = QWidget(self)
            overlay.setGeometry(self.rect())

            layout = QVBoxLayout(overlay)
            layout.setAlignment(Qt.AlignmentFlag.AlignRight |
                                Qt.AlignmentFlag.AlignBottom)

            label = QLabel(text)
            label.setFont(self.message_font)
            layout.setContentsMargins(0, 0, 10, 10)

            if "WARNING" in text:
                label.setStyleSheet("""
                    QLabel {
                        color: #E0B953;
                        background-color: rgb(40, 40, 40);
                        padding: 5px;
                        border-radius: 7px;
                    }
                """)

            elif "ERROR" in text:
                label.setStyleSheet("""
                    QLabel {
                        color: #EC7A5A;
                        background-color: rgb(40, 40, 40);
                        padding: 5px;
                        border-radius: 7px;
                    }
                """)

            else:
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
                # noinspection PyUnresolvedReferences
                animation.finished.connect(overlay.deleteLater)
                animation.start()

                overlay.animation = animation

            QTimer.singleShot(3000, fade_out)

            # ///////////////////////////////////////////////////////////////////////
            # CREATE LAYOUTS

        def read_tags_from_ui(self):
            tag_list = []
            for key, value in self.tag_widgets.items():
                if value.isChecked():
                    tag_list.append(key)
            return tag_list

        def save_tags_to_memory(self, tag_list, move_nr):
            self.game.tag_move_list[move_nr - 1] = tag_list
            self.game.comments_list[move_nr - 1] = (
                self.comment_widget.toPlainText())
            self.game.questions_list[move_nr - 1] = (
                self.question_widget.toPlainText())

        def load_tags_to_ui(self, move_nr):
            tag_list = self.game.tag_move_list[move_nr - 1]
            for tag in tag_list:
                self.tag_widgets[tag].setChecked(True)
            self.comment_widget.setPlainText(self.game.comments_list[
                                                 move_nr - 1])
            self.question_widget.setPlainText(self.game.questions_list[
                                                  move_nr - 1])

        def clear_tags_in_ui(self):
            self.rb_group.setExclusive(False)
            for value in self.tag_widgets.values():
                value.setChecked(False)
            self.rb_group.setExclusive(True)
            self.comment_widget.clear()
            self.question_widget.clear()

        def load_game(self):

            # lichess_url = QApplication.clipboard().text()
            # lichess_url = "https://lichess.org/HbXe1F1j/black"
            # lichess_url = "https://lichess.org/study/bxPkXZHd/3Wlyste3"
            lichess_url = "https://lichess.org/study/bxPkXZHd/O92Yirup"
            # lichess_url = "https://lichess.org/study/bxPkXZHd/pXoT8cCr"

            if "study" in lichess_url:
                self.lichess_id = lichess_url.split("study/")[1]
                req_game = requests.get(
                    f"https://lichess.org/api/study/{self.lichess_id}.pgn",
                    headers={"Authorization": f"Bearer {lichess_study_token}"})
            else:
                self.lichess_id = lichess_url.split(".org/")[1].split("/")[0]
                req_game = requests.get(
                    f"https://lichess.org/game/export/{self.lichess_id}")

            self.game = Game(req_game)

            if not self.game.eval_list:
                self.show_message(
                    "ERROR: Game not loaded\n"
                    "Make sure the game is already analyzed")
                return

            if self.game.black in player_names:
                self.flip_flag = not self.flip_flag

            self.update_board()

            # cursor = None
            # conn = None
            db_file_name = "chess_moves.db"
            if os.path.exists(db_file_name):
                conn = sqlite3.connect(db_file_name)
                cursor = conn.cursor()
                self.existing_game_id = db.check_if_game_exists(
                    cursor,
                    self.lichess_id)

                if self.existing_game_id:
                    self.show_message(
                        "Game loaded\n"
                        "WARNING: Game already exists in database!")
                    self.game.tag_move_list = db.read_tags_from_db(
                        cursor,
                        self.existing_game_id,
                        self.game.tag_move_list)
                else:
                    self.show_message("Game loaded")
                    print("Game Loaded!!")

                self.game_loaded_flag = True
                self.close_db_connection(conn)

        def save_analysis_to_db(self):

            tag_list = self.read_tags_from_ui()
            self.save_tags_to_memory(tag_list, self.current_move_num)

            db_file_name = "chess_moves.db"
            conn = sqlite3.connect(db_file_name)
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            db.initialize_database(cursor)

            new_game_id = db.save_game_to_db(cursor=cursor,
                                             lichess_id=self.lichess_id,
                                             date=self.game.date,
                                             white=self.game.white,
                                             black=self.game.black)

            for imove in range(self.current_move_num):
                tag_list = self.game.tag_move_list[imove]
                if tag_list:
                    move_id = db.save_moves_to_db(
                        cursor=cursor,
                        game_id=new_game_id,
                        move_num=imove + 1,
                        move_notation=self.move_notation_widget.text(),
                        move_cost=self.game.cost_list[imove],
                        fen_before=self.game.fen_before_list[imove],
                        eval_before=self.game.eval_list[imove - 1],
                        last_move_uci=self.game.move_obj_list[imove - 1].uci(),
                        comments=self.comment_widget.toPlainText(),
                        questions=self.question_widget.toPlainText(),
                    )

                    for tag in tag_list:
                        tag_id = db.save_tags_to_db(cursor=cursor,
                                                    tag=tag)
                        db.save_moves_tags_to_db(cursor=cursor,
                                                 move_id=move_id,
                                                 tag_id=tag_id)

            self.close_db_connection(conn)

            if self.existing_game_id:
                self.show_message("Analysis updated")
            else:
                self.show_message("Analysis saved")

        def reset_game_tags(self):
            self.game.tag_move_list = [[] for _ in range(len(self.game.moves))]
            self.clear_tags_in_ui()
            self.show_message("Game tags reset")

        @staticmethod
        def close_db_connection(connection):
            try:
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()

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

            elif not self.game_loaded_flag and event.key() == Qt.Key.Key_L:
                self.load_game()

            elif self.game_loaded_flag and event.key() == Qt.Key.Key_U:
                self.copy_to_clipboard(self.game.url,
                                       "Game URL copied to clipboard")

            elif self.game_loaded_flag and event.key() == Qt.Key.Key_P:
                self.copy_to_clipboard(self.game.pgn,
                                       "Game PGN copied to clipboard")

            elif self.game_loaded_flag and event.key() == Qt.Key.Key_N:
                self.copy_to_clipboard(self.game.board.fen(),
                                       "Position copied to clipboard")

            elif event.key() == Qt.Key.Key_S:
                self.save_analysis_to_db()

            elif event.key() == Qt.Key.Key_R:
                self.reset_game_tags()

            elif event.key() == Qt.Key.Key_C:
                self.clear_tags_in_ui()
                self.show_message("Move tags cleared")

        def copy_to_clipboard(self, text, message):
            QApplication.clipboard().setText(text)
            self.show_message(message)

        def mousePressEvent(self, event):
            widget = QApplication.widgetAt(event.globalPosition().toPoint())

            if not isinstance(widget, QPlainTextEdit):
                fw = QApplication.focusWidget()
                if fw:
                    fw.clearFocus()
                self.setFocus()

            super().mousePressEvent(event)

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
            for move_obj in self.move_obj_list:
                self.moves.append(board.san(move_obj))
                board.push(move_obj)

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

            # create a preallocated list to store fen for each move
            self.fen_before_list = [[] for _ in range(len(self.moves))]

            # create a preallocated list to store comments
            self.comments_list = ["" for _ in range(len(self.moves))]

            # create a preallocated list to store questions
            self.questions_list = ["" for _ in range(len(self.moves))]

    window = AnnotateWindow()
    window.show()
    return window
