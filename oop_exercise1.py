class ChessMoveClass:

    def __init__(self, move_number, move_notation):
        self.move_number_att = move_number
        self.move_notation_att = move_notation
        self.move_tag_att = None

    def add_tag_method(self, tag):
        self.move_tag_att = tag

move1 = ChessMoveClass(1, 'c4')
print(move1.__dict__)
move1.move_tag_att = 'nice move!'
