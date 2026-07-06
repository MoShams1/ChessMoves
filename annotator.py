import chess
import chess.pgn
import chess.svg
import cairosvg

from PyQt6.QtWidgets import (
    QApplication, QLabel, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QRadioButton, QButtonGroup, QCheckBox)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlDatabase, QSqlQuery


class Window(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("ChessMoves: Annotator")
        self.setFixedSize(1000, 700)

        # --------------------------------------------------------------------
        # attributes

        self.board = game.parsed_game.board()
        self.move_pushable = None
        self.move_str = None
        self.hmove_nr = 0
        self.flip_flag = True

        # --------------------------------------------------------------------
        # widgets

        header_font = QFont()
        header_font.setBold(True)

        # widgets [left panel]

        self.player_name_top = QLabel()
        self.player_name_bottom = QLabel()

        self.image_board = QLabel()
        self.pixmap = QPixmap()

        self.btn_prev_move = QPushButton('< Last')
        self.btn_next_move = QPushButton('Next >')

        # widgets [right panel, top row]
        # todo: remove best move; add points lost (cost); forced mate in #N
        self.move_label = QLabel()
        self.move_label.setFont(header_font)

        self.moves_label = QLabel("Best Move(s): ")
        self.moves_label.setFont(header_font)
        self.moves_box = QLineEdit()
        self.moves_box.setPlaceholderText("")

        # widgets [right panel, left tag column]

        self.game_phase_label = QLabel("Game Phase")
        self.game_phase_label.setFont(header_font)

        self.game_phase_group = QButtonGroup(self)

        self.opening = QRadioButton("Opening")
        self.middlegame = QRadioButton("Middlegame")
        self.endgame = QRadioButton("Endgame")

        self.game_phase_group.addButton(self.opening)
        self.game_phase_group.addButton(self.middlegame)
        self.game_phase_group.addButton(self.endgame)

        self.missed_action_label = QLabel("Missed Action")
        self.missed_action_label.setFont(header_font)
        self.missed_action_cbx1 = QCheckBox("Missed Own Opportunity")
        self.missed_action_cbx2 = QCheckBox("Missed Own Defensive Resource")
        self.missed_action_cbx3 = QCheckBox("Missed Opponent's Threat")
        self.missed_action_cbx4 = QCheckBox("Missed Opponent's Defensive "
                                            "Resource")

        self.missed_outcome_label = QLabel("Missed Outcome")
        self.missed_outcome_label.setFont(header_font)
        self.missed_outcome_cbx1 = QCheckBox("Passed Pawn")
        self.missed_outcome_cbx2 = QCheckBox("Material Gain")
        self.missed_outcome_cbx3 = QCheckBox("Positional Gain")
        self.missed_outcome_cbx4 = QCheckBox("Initiative/Tempo")
        self.missed_outcome_cbx5 = QCheckBox("Forced Checkmate")

        self.diagnosis_label = QLabel("Diagnosis")
        self.diagnosis_label.setFont(header_font)
        self.diagnosis_cbx1 = QCheckBox("Fatigue")
        self.diagnosis_cbx2 = QCheckBox("Oversight")
        self.diagnosis_cbx3 = QCheckBox("Time Pressure")
        self.diagnosis_cbx4 = QCheckBox("Mis-Evaluation")
        self.diagnosis_cbx5 = QCheckBox("Mis-Calculation")

        # widgets [right panel, right tag column]

        self.motif_label = QLabel("Motifs")
        self.motif_label.setFont(header_font)

        self.motif_cbx1 = QCheckBox("Pin")
        self.motif_cbx2 = QCheckBox("Fork")
        self.motif_cbx3 = QCheckBox("Skewer")
        self.motif_cbx14 = QCheckBox("Discovered Attack")
        self.motif_cbx8 = QCheckBox("Zwischenzug")
        self.motif_cbx9 = QCheckBox("Overloading")

        self.motif_cbx10 = QCheckBox("Trapped Piece")
        self.motif_cbx12 = QCheckBox("Hanging Material")

        self.motif_cbx4 = QCheckBox("Zugzwang")
        self.motif_cbx5 = QCheckBox("Pawn Break")
        self.motif_cbx6 = QCheckBox("Deflection")
        self.motif_cbx6 = QCheckBox("Attraction/Decoy")
        self.motif_cbx7 = QCheckBox("Prophylaxis")

        self.motif_cbx13 = QCheckBox("Undefended Square")
        self.motif_cbx11 = QCheckBox("Poor Exchange")
        self.motif_cbx15 = QCheckBox("Sacrifice")


        # --------------------------------------------------------------------
        # layout [left panel]

        master_layout = QHBoxLayout()

        left_panel = QVBoxLayout()
        left_panel.setAlignment(Qt.AlignmentFlag.AlignTop)
        left_panel.addWidget(self.player_name_top)
        left_panel.addWidget(self.image_board)
        left_panel.addWidget(self.player_name_bottom)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_prev_move)
        btn_row.addWidget(self.btn_next_move)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_panel.addLayout(btn_row)

        # layout [right panel]

        right_panel = QVBoxLayout()
        right_panel.setAlignment(Qt.AlignmentFlag.AlignTop)
        right_panel.addSpacing(20)

        # layout [right panel, moves row]

        moves_row = QHBoxLayout()
        moves_row.addWidget(self.move_label,2)
        moves_row.addWidget(self.moves_label,1)
        moves_row.addWidget(self.moves_box,3)

        right_panel.addLayout(moves_row)
        right_panel.addSpacing(20)

        # layout [right panel, tag column]

        right_panel_tags = QHBoxLayout()

        # layout [right panel, tag column left]

        right_panel_tags_left = QVBoxLayout()
        right_panel_tags_left.setAlignment(Qt.AlignmentFlag.AlignTop)

        right_panel_tags_left.addWidget(self.game_phase_label)
        right_panel_tags_left.addWidget(self.opening)
        right_panel_tags_left.addWidget(self.middlegame)
        right_panel_tags_left.addWidget(self.endgame)

        right_panel_tags_left.addSpacing(20)

        right_panel_tags_left.addWidget(self.missed_action_label)
        right_panel_tags_left.addWidget(self.missed_action_cbx1)
        right_panel_tags_left.addWidget(self.missed_action_cbx2)
        right_panel_tags_left.addWidget(self.missed_action_cbx3)
        right_panel_tags_left.addWidget(self.missed_action_cbx4)

        right_panel_tags_left.addSpacing(20)

        right_panel_tags_left.addWidget(self.missed_outcome_label)
        right_panel_tags_left.addWidget(self.missed_outcome_cbx1)
        right_panel_tags_left.addWidget(self.missed_outcome_cbx2)
        right_panel_tags_left.addWidget(self.missed_outcome_cbx3)
        right_panel_tags_left.addWidget(self.missed_outcome_cbx4)
        right_panel_tags_left.addWidget(self.missed_outcome_cbx5)

        right_panel_tags_left.addSpacing(20)

        right_panel_tags_left.addWidget(self.diagnosis_label)
        right_panel_tags_left.addWidget(self.diagnosis_cbx1)
        right_panel_tags_left.addWidget(self.diagnosis_cbx2)
        right_panel_tags_left.addWidget(self.diagnosis_cbx3)
        right_panel_tags_left.addWidget(self.diagnosis_cbx4)
        right_panel_tags_left.addWidget(self.diagnosis_cbx5)

        # layout [right panel, tag column right]

        right_panel_tags_right = QVBoxLayout()
        right_panel_tags_right.setAlignment(Qt.AlignmentFlag.AlignTop)
        right_panel_tags_right.addWidget(self.motif_label)
        right_panel_tags_right.addWidget(self.motif_cbx1)
        right_panel_tags_right.addWidget(self.motif_cbx2)
        right_panel_tags_right.addWidget(self.motif_cbx3)
        right_panel_tags_right.addWidget(self.motif_cbx4)
        right_panel_tags_right.addWidget(self.motif_cbx5)
        right_panel_tags_right.addWidget(self.motif_cbx6)
        right_panel_tags_right.addWidget(self.motif_cbx7)
        right_panel_tags_right.addWidget(self.motif_cbx8)
        right_panel_tags_right.addWidget(self.motif_cbx9)
        right_panel_tags_right.addWidget(self.motif_cbx10)
        right_panel_tags_right.addWidget(self.motif_cbx11)
        right_panel_tags_right.addWidget(self.motif_cbx12)
        right_panel_tags_right.addWidget(self.motif_cbx13)
        right_panel_tags_right.addWidget(self.motif_cbx14)
        right_panel_tags_right.addWidget(self.motif_cbx15)
        right_panel_tags_right.addWidget(self.motif_cbx16)

        right_panel_tags.addLayout(right_panel_tags_left)
        right_panel_tags.addSpacing(20)
        right_panel_tags.addLayout(right_panel_tags_right)

        right_panel.addLayout(right_panel_tags)

        # layout [master]

        master_layout.addLayout(left_panel, 0)
        master_layout.addSpacing(20)
        master_layout.addLayout(right_panel, 1)
        self.setLayout(master_layout)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()
        self.moves_box.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        # --------------------------------------------------------------------

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
