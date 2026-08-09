import chess
import random
import sqlite3
import chess.pgn
import chess.svg
import database as db
from game_panel import GamePanel
from personal_info import player_names
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtWidgets import (QApplication,
                             QLabel,
                             QWidget,
                             QPushButton,
                             QVBoxLayout,
                             QHBoxLayout,
                             QGraphicsOpacityEffect)


def run_train():
    class TrainWindow(QWidget):

        def __init__(self):
            super().__init__()

            self.setWindowTitle("ChessMoves: Train")
            self.resize(1000, 800)
            self.setStyleSheet("""
            QWidget {
            color: #D3D3D3;
            }
            """)

            self.flip_flag = True
            self.global_opacity = 0

            self.learning_idx = None
            self.times_practiced = None

            self.player_top_widget = QLabel()
            self.player_bottom_widget = QLabel()

            self.image_board_widget = QLabel()
            self.pixmap = QPixmap()

            self.move_notation_widget = QLabel()
            self.effect_notation = QGraphicsOpacityEffect()
            self.move_notation_widget.setGraphicsEffect(self.effect_notation)

            self.move_cost_widget = QLabel()
            self.effect = QGraphicsOpacityEffect()
            self.move_cost_widget.setGraphicsEffect(self.effect)

            self.eval_widget = QLabel()
            self.effect = QGraphicsOpacityEffect()
            self.eval_widget.setGraphicsEffect(self.effect)

            self.button_widgets = {}

            self.game_panel_widget = GamePanel(mode="train")

            self.message_font = QFont()
            self.message_font.setPointSize(10)

            self.times_practiced_header = QLabel("Times Practiced: ")
            self.times_practiced_value = QLabel()
            self.learning_idx_header = QLabel("Learning Index:")
            self.learning_idx_value = QLabel()

            button_layout = self.create_button_layout()
            button_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            right_button_layout = self.create_learning_button_layout()

            right_layout = QVBoxLayout()
            right_layout.setAlignment(Qt.AlignmentFlag.AlignTop |
                                      Qt.AlignmentFlag.AlignCenter)
            right_layout.addWidget(QLabel("QUESTION(S):"))
            self.questions_value_widget = QLabel()
            right_layout.addWidget(self.questions_value_widget)
            right_layout.addWidget(QLabel("COMMENT(S):"))

            self.comments_value_widget = QLabel()
            self.effect = QGraphicsOpacityEffect()
            self.comments_value_widget.setGraphicsEffect(self.effect)
            right_layout.addWidget(self.comments_value_widget)

            tags = QLabel()
            tags.setGraphicsEffect(self.effect)
            right_layout.addWidget(tags)
            right_layout.addWidget(QLabel("Could you answer the question(s) "
                                          "above?"))
            right_layout.addLayout(right_button_layout)
            learning_info_layout = self.create_learning_info_layout()
            right_layout.addLayout(learning_info_layout)

            master_layout_top = QHBoxLayout()
            master_layout_top.addWidget(self.game_panel_widget, 4)
            master_layout_top.addLayout(right_layout, 3)

            master_layout = QVBoxLayout()
            master_layout.addLayout(master_layout_top)
            master_layout.addLayout(button_layout)
            master_layout.setContentsMargins(50, 50, 50, 50)
            self.setLayout(master_layout)

            self.game_panel_widget.show_position(
                board=chess.Board(),
                white_player="?",
                black_player="?",
                orientation=self.flip_flag,
            )

            self.game_row, self.move_row = self.load_position()

            self.button_widgets["Close"].clicked.connect(self.close)
            self.button_widgets["Yes"].clicked.connect(self.response_yes)
            self.button_widgets["No"].clicked.connect(self.response_no)
            self.button_widgets["Skip"].clicked.connect(self.response_skip)

            if "/" in self.game_row["lichess_id"]:
                self.game_url = ("https://lichess.org/study/" +
                                 self.game_row["lichess_id"])
            else:
                self.game_url = ("https://lichess.org/" +
                                 self.game_row["lichess_id"])
            db_file_name = "chess_moves.db"
            conn = sqlite3.connect(db_file_name)
            cursor = conn.cursor()
            self.tags = db.read_tags_from_db_train(cursor, self.game_row[
                "game_id"])
            self.close_db_connection(conn)
            self.questions_value_widget.setText(self.move_row["questions"])
            self.comments_value_widget.setText(self.move_row["comments"])
            tags.setText("\n".join(f"#{tag}" for tag in self.tags))

            self.button_widgets["URL"].clicked.connect(
                lambda: self.copy_to_clipboard(
                    self.game_url,
                    "Game URL copied to clipboard"))

            self.button_widgets["FEN"].clicked.connect(
                lambda: self.copy_to_clipboard(
                    self.move_row["fen_before"],
                    "Position copied to clipboard"))

            self.update_board()

        def update_board(self):
            self.game_panel_widget.show_position(
                board=chess.Board(self.move_row["fen_before"]),
                white_player=self.game_row["white"],
                black_player=self.game_row["black"],
                orientation=self.flip_flag,
                last_move=chess.Move.from_uci(self.move_row["last_move_uci"]),
                notation=self.move_row["move_notation"],
                cost=self.move_row["move_cost"],
                evaluation=self.move_row["eval_before"],
            )
            self.game_panel_widget.set_move_cost_color()
            self.effect.setOpacity(self.global_opacity)

            self.questions_value_widget.setText(self.move_row["questions"])
            self.comments_value_widget.setText(self.move_row["comments"])

            self.learning_idx_value.setText(
                str(self.move_row["learning_idx"]))
            self.times_practiced_value.setText(
                str(self.move_row["times_practiced"]))

        def create_button_layout(self):
            width_small = 50
            width_large = 70
            spacing_small = -10
            spacing_large = 15
            layout = QHBoxLayout()
            buttons = {
                "Reveal": {"tooltip": "Reveal position information (R)",
                            "width": width_large,
                            "spacing": spacing_large},
                "URL": {"tooltip": "Copy game URL (U)",
                        "width": width_small,
                        "spacing": spacing_small},
                "FEN": {"tooltip": "Copy position FEN (E)",
                        "width": width_small,
                        "spacing": spacing_large},
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

        def create_learning_button_layout(self):
            width_small = 50
            width_large = 70
            spacing_small = -10
            spacing_large = 15
            layout = QHBoxLayout()
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            buttons = {
                "Yes": {"tooltip": "Yes, I got this (Y)",
                        "width": width_small,
                        "spacing": spacing_small},
                "No": {"tooltip": "No, I don't get it (N)",
                       "width": width_small,
                       "spacing": spacing_small},
                "Skip": {"tooltip": "Skip it for now (K)",
                         "width": width_small,
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

        def create_learning_info_layout(self):
            layout = QVBoxLayout()

            layout1 = QHBoxLayout()
            layout1.addWidget(self.times_practiced_header)
            layout1.addWidget(self.times_practiced_value)

            layout2 = QHBoxLayout()
            layout2.addWidget(self.learning_idx_header)
            layout2.addWidget(self.learning_idx_value)

            layout.addLayout(layout1)
            layout.addLayout(layout2)

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

            QTimer.singleShot(2000, fade_out)

        def load_tags_to_ui(self, move_nr):
            tag_list = self.game.tag_move_list[move_nr - 1]
            for tag in tag_list:
                self.tag_widgets[tag].setChecked(True)

        def load_position(self):
            connection = sqlite3.connect("chess_moves.db")
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()

            idx_list = db.read_learning_idx_column(cursor)

            if min(idx_list) == max(idx_list):
                move_row = db.read_random_position_from_db(cursor)
            else:
                while True:
                    move_row = db.read_random_position_from_db(cursor)

                    p = ((move_row["learning_idx"] - min(idx_list)) / (max(
                        idx_list) - min(idx_list))) * 0.95

                    r = random.random()
                    if r >= p:
                        break
            game_row = db.read_game_from_move_id(cursor, move_row["game_id"])
            if game_row["black"] in player_names:
                self.flip_flag = False

            self.learning_idx = move_row["learning_idx"]
            self.times_practiced = move_row["times_practiced"]

            self.close_db_connection(connection)
            return game_row, move_row

        def save_train_response(self):
            conn = sqlite3.connect("chess_moves.db")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE moves
                SET learning_idx = ?, times_practiced = ?
                WHERE move_id = ?
                """, (self.learning_idx,
                      self.times_practiced,
                      self.move_row["move_id"]))
            self.close_db_connection(conn)

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

            elif event.key() == Qt.Key.Key_F:
                self.flip_flag = not self.flip_flag
                self.update_board()

            elif event.key() == Qt.Key.Key_R:
                if self.global_opacity == 0:
                    self.global_opacity = 1
                elif self.global_opacity == 1:
                    self.global_opacity = 0
                self.update_board()

            elif event.key() == Qt.Key.Key_Y:
                self.response_yes()

            elif event.key() == Qt.Key.Key_N:
                self.response_no()

            elif event.key() == Qt.Key.Key_K:
                self.response_skip()

            elif event.key() == Qt.Key.Key_U:
                self.copy_to_clipboard(self.game_url,
                                       "Game URL copied to clipboard")

            elif event.key() == Qt.Key.Key_E:
                self.copy_to_clipboard(self.move_row["fen_before"],
                                       "Position copied to clipboard")

        def response_yes(self):
            self.learning_idx += 1
            self.times_practiced += 1
            self.save_train_response()
            self.game_row, self.move_row = self.load_position()
            self.update_board()

        def response_no(self):
            if self.learning_idx > 0:
                self.learning_idx -= 1
            self.times_practiced += 1
            self.save_train_response()
            self.game_row, self.move_row = self.load_position()
            self.update_board()

        def response_skip(self):
            self.game_row, self.move_row = self.load_position()
            self.update_board()

        def copy_to_clipboard(self, text, message):
            QApplication.clipboard().setText(text)
            self.show_message(message)

    window = TrainWindow()
    window.show()
    return window
