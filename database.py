def initialize_database(cursor):
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS games (
            game_id INTEGER PRIMARY KEY,
            lichess_id TEXT UNIQUE,
            date TEXT,
            white TEXT,
            black TEXT
        );
        
        CREATE TABLE IF NOT EXISTS moves (
            move_id INTEGER PRIMARY KEY,
            game_id INTEGER REFERENCES games(game_id) ON DELETE CASCADE,
            move_num INTEGER,
            move_notation TEXT,
            move_cost REAL,     
            fen_before TEXT,
            times_practiced DEFAULT 0,
            learning_idx DEFAULT 0,
            UNIQUE(game_id, move_num) 
        );
        
        CREATE TABLE IF NOT EXISTS tags (
            tag_id INTEGER PRIMARY KEY,
            tag TEXT UNIQUE
        );   
        
        CREATE TABLE IF NOT EXISTS moves_tags (
            move_tag_id INTEGER PRIMARY KEY,
            move_id INTEGER REFERENCES moves(move_id) ON DELETE CASCADE,
            tag_id INTEGER REFERENCES tags(tag_id)
        );
                   
    """)


def check_if_game_exists(cursor, lichess_id):
    cursor.execute("""
        SELECT game_id
        FROM games
        WHERE lichess_id = ?
        """, (lichess_id,))

    result = cursor.fetchone()

    if result:
        return result[0]


def save_game_to_db(cursor, lichess_id, date, white, black):
    cursor.execute("""
            DELETE FROM games
            WHERE lichess_id = ?
            """, (lichess_id,))

    cursor.execute("""        
        INSERT INTO games
        (lichess_id, date, white, black)
        VALUES(?, ?, ?, ?)        
        """, (
        lichess_id,
        date,
        white,
        black
    ))

    cursor.execute("""
        SELECT game_id FROM games
        WHERE lichess_id = ?
        """, (lichess_id,))

    game_id = cursor.fetchone()[0]

    return game_id


def save_moves_to_db(cursor, game_id, move_num, move_notation, move_cost,
                     fen_before):
    cursor.execute("""
        INSERT INTO moves
        (game_id, move_num, move_notation, move_cost, fen_before)
        VALUES(?, ?, ?, ?, ?)
        """, (
        game_id,
        move_num,
        move_notation,
        move_cost,
        fen_before
    ))
    cursor.execute("""
        SELECT move_id FROM moves
        WHERE game_id = ? AND move_num = ?
        """, (
        game_id,
        move_num
    ))
    move_id = cursor.fetchone()[0]

    return move_id


def save_tags_to_db(cursor, tag):
    cursor.execute("""
        INSERT OR IGNORE INTO tags
        (tag)
        VALUES(?)        
        """, (tag,))
    cursor.execute("""
        SELECT tag_id FROM tags
        WHERE tag = ?
        """, (tag,))
    tag_id = cursor.fetchone()[0]

    return tag_id


def save_moves_tags_to_db(cursor, move_id, tag_id):
    cursor.execute("""
        INSERT INTO moves_tags
        (move_id, tag_id)
        VALUES(?, ?)        
        """, (
        move_id,
        tag_id
    ))
    cursor.execute("""
            SELECT move_tag_id FROM moves_tags
            WHERE move_id = ? AND tag_id = ?
            """, (move_id, tag_id))
    move_tag_id = cursor.fetchone()[0]

    return move_tag_id


def read_tags_from_db(cursor, game_id, tag_move_list):
    cursor.execute("""
        SELECT moves.move_num, tags.tag
        FROM moves
        JOIN moves_tags ON moves.move_id = moves_tags.move_id
        JOIN tags ON moves_tags.tag_id = tags.tag_id
        WHERE moves.game_id = ?
        ORDER BY moves.move_num
        """, (game_id,))

    for move_num, tag in cursor.fetchall():
        tag_move_list[move_num - 1].append(tag)

    return tag_move_list