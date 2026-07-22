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
            game_id INTEGER REFERENCES gameS(game_id),
            hmove_nr INTEGER,
            move_cost REAL,     
            UNIQUE(game_id, hmove_nr) 
        );
        
        CREATE TABLE IF NOT EXISTS tags (
            tag_id INTEGER PRIMARY KEY,
            tag TEXT UNIQUE
        );   
        
        CREATE TABLE IF NOT EXISTS moves_tags (
            move_tag_id INTEGER PRIMARY KEY,
            move_id INTEGER REFERENCES moves(move_id),
            tag_id INTEGER REFERENCES tags(tag_id)
        );
    """)


def check_if_game_exists(cursor, lichess_id):
    cursor.execute("""
        SELECT EXISTS (SELECT 1 FROM games WHERE lichess_id = ?)
        """, (lichess_id,))
    flag = bool(cursor.fetchone()[0])
    return flag


def save_game(cursor, lichess_id, date, white, black):
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


def save_move(cursor, game_id, move_nr, move_cost):
    cursor.execute("""
        INSERT INTO moves
        (game_id, hmove_nr, move_cost)
        VALUES(?, ?, ?)        
        """, (
        game_id,
        move_nr,
        move_cost
    ))
    cursor.execute("""
        SELECT move_id FROM moves
        WHERE game_id = ? AND hmove_nr = ?
        """, (
        game_id,
        move_nr
    ))
    move_id = cursor.fetchone()[0]

    return move_id


def save_tag(cursor, tag):
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


def save_move_tag(cursor, move_id, tag_id):
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
