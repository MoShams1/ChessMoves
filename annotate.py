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
            self.resize(1000, 1000)

            # --------------------------------------------------
            # attributes/variables/lists/dictionaries

            self.game = None
            self.existing_game_id = None
            self.lichess_id = None
            self.move_obj = None
            self.flip_flag = True
            self.current_move_num = 0
            self.game_loaded_flag = False

            self.comment_wgt = QPlainTextEdit()
            self.question_wgt = QPlainTextEdit()

            self.btn_wgt_dict = {}
            self.tag_wgt_dict = {}

            # --------------------------------------------------
            # widgets

            self.player_top_wgt = QLabel()
            self.player_bottom_wgt = QLabel()

            self.board_wgt = QLabel()
            self.pixmap = QPixmap()

            self.notation_val_wgt = QLabel()
            self.cost_val_wgt = QLabel()
            self.eval_val_wgt = QLabel()

            self.rb_group = QButtonGroup()

            # --------------------------------------------------
            # layouts

            board_lay = self.create_board_layout()
            info_lay = self.create_info_layout()
            copy_btn_lay = self.create_copy_btn_layout()
            game_btn_lay = self.create_game_btn_layout()
            tag_lay = self.create_tag_lay()
            textbox_lay = self.create_textbox_layout()
            clear_btn_wgt = self.create_clear_btn_widget()

            left_lay = QVBoxLayout()
            left_lay.addLayout(board_lay)
            left_lay.addSpacing(40)
            left_lay.addLayout(info_lay)
            left_lay.addSpacing(40)
            left_lay.addLayout(copy_btn_lay)
            left_lay.addSpacing(20)
            left_lay.addLayout(game_btn_lay)

            right_lay = QVBoxLayout()
            right_lay.addLayout(tag_lay)
            right_lay.addLayout(textbox_lay)
            right_lay.addLayout(clear_btn_wgt)

            master_lay = QHBoxLayout()
            master_lay.addLayout(left_lay)
            master_lay.addLayout(right_lay)

            master_lay.setContentsMargins(90, 90, 90, 90)

            self.setLayout(master_lay)
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.setFocus()

            self.setTabOrder(self, self.question_wgt)
            self.setTabOrder(self.question_wgt, self.comment_wgt)

            # --------------------------------------------------------------------

            self.show_position(
                board=chess.Board(),
                orientation=self.flip_flag,
            )

        # ///////////////////////////////////////////////////////////////////////
        # BOARD BEHAVIOR AND VISUALS

        def update_board(self):

            if self.current_move_num > 0:

                if self.current_move_num % 2 == 1:
                    prefix = f"{(self.current_move_num + 1) // 2}. "

                else:
                    prefix = f"{self.current_move_num // 2}... "

                self.notation_val_wgt.setText(
                    f"{prefix}{self.game.moves[self.current_move_num - 1]}")

                self.cost_val_wgt.setText(
                    f"{self.game.cost_list[self.current_move_num - 1]}")

                current_eval = self.game.eval_list[self.current_move_num - 1]

                if isinstance(current_eval, float):
                    if not (current_eval < 0):
                        self.eval_val_wgt.setText(f"+{current_eval}")
                    else:
                        self.eval_val_wgt.setText(f"{current_eval}")

                if isinstance(current_eval, str):
                    self.eval_val_wgt.setText(current_eval)

            self.show_position(
                board=self.game.board,
                white_player=self.game.white,
                black_player=self.game.black,
                orientation=self.flip_flag,
                last_move=self.move_obj,
                notation_val=self.notation_val_wgt.text(),
                cost_val=self.cost_val_wgt.text(),
                eval_val=self.eval_val_wgt.text(),
            )

            if self.current_move_num > 0:
                self.set_cost_color()

        def show_position(self, board, orientation,
                          white_player="---", black_player="---",
                          last_move=None,
                          notation_val="---", cost_val="---", eval_val="---"):
            svg = chess.svg.board(
                board=board,
                orientation=orientation,
                lastmove=last_move,
                coordinates=True,
                size=450,
                colors={
                    "square light": "#B0AA98",
                    "square dark": "#827A68",
                    "square light lastmove": "#a1ad68",
                    "square dark lastmove": "#a1ad68",
                },
            )

            pixmap = QPixmap()
            pixmap.loadFromData(cairosvg.svg2png(bytestring=svg.encode()))
            self.board_wgt.setPixmap(pixmap)

            self.player_top_wgt.setProperty('type', 'player')
            self.player_top_wgt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.player_bottom_wgt.setProperty('type', 'player')
            self.player_bottom_wgt.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if orientation:
                self.player_top_wgt.setText(black_player)
                self.player_bottom_wgt.setText(white_player)
            else:
                self.player_top_wgt.setText(white_player)
                self.player_bottom_wgt.setText(black_player)

            self.notation_val_wgt.setText(str(notation_val))
            self.cost_val_wgt.setText(str(cost_val))
            self.eval_val_wgt.setText(str(eval_val))

        def create_board_layout(self):
            layout = QVBoxLayout()
            layout.addWidget(self.player_top_wgt)
            layout.addWidget(self.board_wgt)
            layout.addWidget(self.player_bottom_wgt)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return layout

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

                self.game.board.pop()
                self.update_board()

        def create_info_layout(self):

            spacing_v = 2
            spacing_h = 10

            self.notation_val_wgt.setProperty('type', 'eval-normal')
            self.cost_val_wgt.setProperty('type', 'eval-normal')
            self.eval_val_wgt.setProperty('type', 'eval-normal')

            layout = QHBoxLayout()

            layout_hdr = QVBoxLayout()
            layout_val = QVBoxLayout()

            info_dict = {
                "Move:": {"type": "eval-header",
                          "val": self.notation_val_wgt},
                "Cost:": {"type": "eval-header",
                          "val": self.cost_val_wgt},
                "Evaluation:": {"type": "eval-header",
                                "val": self.eval_val_wgt},
            }
            for label, config in info_dict.items():
                hdr_wgt = QLabel(label)
                hdr_wgt.setProperty("type", config["type"])
                layout_hdr.addWidget(hdr_wgt)
                layout_hdr.addSpacing(spacing_v)
                layout_val.addWidget(config["val"])
                layout_val.addSpacing(spacing_v)

            layout.addWidget(self.create_navi_button()[0],
                             Qt.AlignmentFlag.AlignLeft)
            layout.addSpacing(spacing_h)
            layout.addLayout(layout_hdr, 2)
            layout.addLayout(layout_val, 5)
            layout.addSpacing(spacing_h)
            layout.addWidget(self.create_navi_button()[1],
                             Qt.AlignmentFlag.AlignRight)

            layout.setContentsMargins(25, 0, 25, 0)

            return layout

        def create_navi_button(self):
            width = 35
            height = 50
            btn_wgt_list = []
            btn_dict = {
                "<":
                    {"tooltip": "Previous move (<)",
                     "shortcut": "Left",
                     "callback": self.previous_move,
                     "level": "2"},
                ">":
                    {"tooltip": "Next move (>)",
                     "shortcut": "Right",
                     "callback": self.next_move,
                     "level": "2"}
            }
            for button_name, config in btn_dict.items():
                btn_wgt = QPushButton(button_name)

                btn_wgt.setFixedSize(width, height)
                btn_wgt.setToolTip(config["tooltip"])
                btn_wgt.setShortcut(config["shortcut"])
                btn_wgt.clicked.connect(config["callback"])
                btn_wgt.setProperty("level", config["level"])

                btn_wgt_list.append(btn_wgt)

            return btn_wgt_list

        def create_copy_btn_layout(self):
            layout = QHBoxLayout()

            width = 80
            spacing = -10

            btn_dict = {
                "URL":
                    {"tooltip": "Copy game URL (U)",
                     "width": width,
                     "shortcut": "U",
                     "callback": self.copy_url,
                     "level": "2"},
                "PGN":
                    {"tooltip": "Copy game PGN (P)",
                     "width": width,
                     "shortcut": "P",
                     "callback": self.copy_pgn,
                     "level": "2"},
                "FEN":
                    {"tooltip": "Copy position FEN (E)",
                     "width": width,
                     "shortcut": "E",
                     "callback": self.copy_fen,
                     "level": "2"}
            }

            for button_name, config in btn_dict.items():
                btn_wgt = QPushButton(button_name)

                btn_wgt.setFixedWidth(int(config["width"]))
                btn_wgt.setToolTip(config["tooltip"])
                btn_wgt.setShortcut(config["shortcut"])
                btn_wgt.clicked.connect(config["callback"])
                btn_wgt.setProperty("level", config["level"])

                layout.addWidget(btn_wgt)
                if not button_name == "FEN":
                    layout.addSpacing(spacing)

            layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            return layout

        def create_game_btn_layout(self):
            width = 250
            spacing = -5
            layout = QVBoxLayout()
            buttons = {
                "Load": {"tooltip": "Load game (L)",
                         "width": width,
                         "shortcut": "L",
                         "callback": self.load_game,
                         "level": "1"},
                "Reset": {"tooltip": "Reset game tags (R)",
                          "width": width,
                          "shortcut": "R",
                          "callback": self.reset_game_tags,
                          "level": "3"},
                "Close": {"tooltip": "Close window (Esc)",
                          "width": width,
                          "shortcut": "Esc",
                          "callback": self.close,
                          "level": "3"}
            }
            for button_name, config in buttons.items():
                btn_wgt = QPushButton(button_name)
                btn_wgt.setToolTip(config["tooltip"])
                btn_wgt.setFixedWidth(config["width"])
                btn_wgt.setShortcut(config["shortcut"])
                btn_wgt.clicked.connect(config["callback"])
                btn_wgt.setProperty("level", config["level"])

                layout.addWidget(btn_wgt)
                if not button_name == "Close":
                    layout.addSpacing(spacing)

            layout.setAlignment(Qt.AlignmentFlag.AlignHCenter |
                                Qt.AlignmentFlag.AlignTop)
            return layout

        def create_tag_lay(self):

            spacing_block_v_before = 20
            spacing_block_v_after = 5
            spacing_column_h = 20
            spacing_tag_v = 3

            layout = QHBoxLayout()
            layout.setAlignment(Qt.AlignmentFlag.AlignTop |
                                Qt.AlignmentFlag.AlignLeft)
            layout.setContentsMargins(60, 15, 0, 0)

            layout_left = QVBoxLayout()
            layout_left.setAlignment(Qt.AlignmentFlag.AlignTop)
            layout_right = QVBoxLayout()
            layout_right.setAlignment(Qt.AlignmentFlag.AlignTop)

            for key in list(tag_source.keys()):

                header = key.split('_')[0]
                tags = tag_source[key]
                box_type = key.split('_')[1]

                tag_hdr_wgt = QLabel(header)
                tag_hdr_wgt.setProperty("type", "tag-header")

                layout_block = QVBoxLayout()
                layout_block.addSpacing(spacing_block_v_before)
                layout_block.addWidget(tag_hdr_wgt)
                layout_block.addSpacing(spacing_block_v_after)

                tag_wgt = None
                for tag in tags:
                    if box_type == "cb":
                        tag_wgt = QCheckBox(tag)
                    if box_type == "rb":
                        tag_wgt = QRadioButton(tag)
                        self.rb_group.addButton(tag_wgt)
                    tag_wgt.setProperty("type", "tag")
                    self.tag_wgt_dict[tag] = tag_wgt
                    layout_block.addWidget(tag_wgt)
                    layout_block.addSpacing(spacing_tag_v)

                if header in ["GENERAL", "GAME PHASE", "GIAGNOSIS",
                              "MISSED RESPONSE"]:
                    layout_left.addLayout(layout_block)

                if header in ["TACTICAL THEME", "POSITIONAL THEME"]:
                    layout_right.addLayout(layout_block)

            layout.addLayout(layout_left)
            layout.addSpacing(spacing_column_h)
            layout.addLayout(layout_right)

            return layout

        def create_textbox_layout(self):
            height_hdr = 15
            height_box = 100
            spacing_box_v = 5

            self.comment_wgt.setFixedHeight(height_box)
            self.comment_wgt.setTabChangesFocus(True)
            self.question_wgt.setFixedHeight(height_box)
            self.question_wgt.setTabChangesFocus(True)

            question_hdr_wgt = QLabel("QUESTIONS:")
            question_hdr_wgt.setFixedHeight(height_hdr)
            question_hdr_wgt.setProperty("type", "textbox-header")

            comment_hdr_wgt = QLabel("COMMENTS:")
            comment_hdr_wgt.setFixedHeight(height_hdr)
            comment_hdr_wgt.setProperty("type", "textbox-header")

            self.question_wgt.setProperty('type', 'textbox')
            self.comment_wgt.setProperty('type', 'textbox')

            layout = QVBoxLayout()

            layout.addWidget(question_hdr_wgt)
            layout.addWidget(self.question_wgt)
            layout.addSpacing(spacing_box_v)
            layout.addWidget(comment_hdr_wgt)
            layout.addWidget(self.comment_wgt)

            layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            layout.setContentsMargins(60, 20, 00, 0)

            return layout

        def create_clear_btn_widget(self):

            width_btn = 80
            btn_wgt = QPushButton("Clear")

            btn_wgt.setToolTip("Clear move annotations (C)")
            btn_wgt.setFixedWidth(width_btn)
            btn_wgt.setShortcut("C")
            btn_wgt.clicked.connect(self.clear_tags_in_ui)
            btn_wgt.setProperty("level", "2")

            layout = QVBoxLayout()
            layout.addWidget(btn_wgt)
            layout.setAlignment(Qt.AlignmentFlag.AlignRight |
                                Qt.AlignmentFlag.AlignBottom)
            return layout

        def show_message(self, text, message_type):
            overlay = QWidget(self)
            overlay.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            overlay.setGeometry(self.rect())

            # Ensure mouse clicks pass through the overlay to underlying
            # controls
            overlay.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents)

            layout = QVBoxLayout(overlay)
            layout.setAlignment(
                Qt.AlignmentFlag.AlignRight |
                Qt.AlignmentFlag.AlignBottom
            )
            layout.setContentsMargins(0, 0, 10, 10)

            label = QLabel(text)
            label.setProperty('type', message_type)

            layout.addWidget(label)

            effect = QGraphicsOpacityEffect(label)
            effect.setOpacity(1.0)
            label.setGraphicsEffect(effect)

            overlay.show()

            def fade_out():
                animation = QPropertyAnimation(effect, b"opacity")
                animation.setDuration(500)
                animation.setStartValue(1.0)
                animation.setEndValue(0.0)
                animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
                animation.finished.connect(overlay.deleteLater)
                overlay.animation = animation
                animation.start()

            QTimer.singleShot(3000, fade_out)


            # # ///////////////////////////////////////////////////////////////////////
            # # CREATE LAYOUTS

        def read_tags_from_ui(self):
            tag_list = []
            for key, value in self.tag_wgt_dict.items():
                if value.isChecked():
                    tag_list.append(key)
            return tag_list

        def save_tags_to_memory(self, tag_list, move_nr):
            self.game.tag_move_list[move_nr - 1] = tag_list
            self.game.comments_list[move_nr - 1] = (
                self.comment_wgt.toPlainText())
            self.game.questions_list[move_nr - 1] = (
                self.question_wgt.toPlainText())
            self.game.notation_list[
                move_nr - 1] = self.notation_val_wgt.text()

        def load_tags_to_ui(self, move_nr):
            tag_list = self.game.tag_move_list[move_nr - 1]
            for tag in tag_list:
                self.tag_wgt_dict[tag].setChecked(True)
            self.comment_wgt.setPlainText(self.game.comments_list[
                                              move_nr - 1])
            self.question_wgt.setPlainText(self.game.questions_list[
                                               move_nr - 1])

        def clear_tags_in_ui(self):
            self.rb_group.setExclusive(False)
            for value in self.tag_wgt_dict.values():
                value.setChecked(False)
            self.rb_group.setExclusive(True)
            self.comment_wgt.clear()
            self.question_wgt.clear()

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
                    "Make sure the game is already analyzed",
                    'message-error')
                return

            if self.game.black in player_names:
                self.flip_flag = False

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
                        "WARNING: Game already exists in database!",
                        'message-warning')
                    (self.game.tag_move_list,
                     self.game.comments_list,
                     self.game.questions_list,
                     ) = (db.read_tags_from_db(
                        cursor,
                        self.existing_game_id,
                        self.game.tag_move_list,
                        self.game.comments_list,
                        self.game.questions_list)
                    )
                else:
                    self.show_message("Game loaded", 'message-normal')
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
                        move_notation=self.game.notation_list[imove],
                        move_cost=self.game.cost_list[imove],
                        fen_before=self.game.fen_before_list[imove],
                        eval_before=self.game.eval_list[imove - 1],
                        last_move_uci=self.game.move_obj_list[imove - 1].uci(),
                        comments=self.game.comments_list[imove],
                        questions=self.game.questions_list[imove],
                    )

                    for tag in tag_list:
                        tag_id = db.save_tags_to_db(cursor=cursor,
                                                    tag=tag)
                        db.save_moves_tags_to_db(cursor=cursor,
                                                 move_id=move_id,
                                                 tag_id=tag_id)

            self.close_db_connection(conn)

            if self.existing_game_id:
                self.show_message("Analysis updated", 'message-normal')
            else:
                self.show_message("Analysis saved", 'message-normal')

        def reset_game_tags(self):
            self.game.tag_move_list = [[] for _ in range(len(self.game.moves))]
            self.clear_tags_in_ui()
            self.show_message("Game tags reset", 'message-normal')

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

            # if event.key() == Qt.Key.Key_Escape:
            #     self.close()


            if event.key() == Qt.Key.Key_Right:
                self.next_move()

            elif event.key() == Qt.Key.Key_Left:
                self.previous_move()


            elif event.key() == Qt.Key.Key_F:
                self.flip_flag = not self.flip_flag
                self.update_board()

            # elif event.key() == Qt.Key.Key_S:
            #     self.save_analysis_to_db()

            # elif event.key() == Qt.Key.Key_R:
            #     self.reset_game_tags()

            # elif event.key() == Qt.Key.Key_C:
            #     self.clear_tags_in_ui()
            #     self.show_message("Move tags cleared", 'message-normal')

        def mousePressEvent(self, event):
            widget = QApplication.widgetAt(event.globalPosition().toPoint())

            if not isinstance(widget, QPlainTextEdit):
                fw = QApplication.focusWidget()
                if fw:
                    fw.clearFocus()
                self.setFocus()

            super().mousePressEvent(event)

        def set_cost_color(self):
            cost = self.cost_val_wgt.text()

            if cost in ("Unavoidable Checkmate", "Missed Checkmate"):
                style_type = "eval-blunder"
            else:
                cost = float(cost)

                if .5 <= cost < 1:
                    style_type = "eval-inaccuracy"
                elif 1 <= cost < 3:
                    style_type = "eval-mistake"
                elif cost >= 3:
                    style_type = "eval-blunder"
                else:
                    style_type = "eval-normal"

            for widget in (self.notation_val_wgt, self.cost_val_wgt):
                widget.setProperty("type", style_type)
                widget.style().unpolish(widget)
                widget.style().polish(widget)

        def copy_url(self):
            QApplication.clipboard().setText(self.game.url)
            self.show_message("Game URL copied to clipboard",
                              'message-normal')

        def copy_pgn(self):
            QApplication.clipboard().setText(self.game.pgn)
            self.show_message("Game PGN copied to clipboard",
                              'message-normal')

        def copy_fen(self):
            QApplication.clipboard().setText(self.game.board.fen())
            self.show_message("Position FEN copied to clipboard",
                              'message-normal')

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

            # create a preallocated list to store move notations
            self.notation_list = ["" for _ in range(len(self.moves))]

    window = AnnotateWindow()
    with open("styles.qss") as f:
        window.setStyleSheet(f.read())
    return window
