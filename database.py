import sqlite3


def initialize_database(db_name="chess_moves.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

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
            move_id INTEGER REFERENCES moves(move_id),
            tag_id INTEGER REFERENCES tags(tag_id),
            PRIMARY KEY (move_id, tag_id)            
        );
    """)

    conn.commit()
    conn.close()


def save_game(lichess_id, date, white, black, db_name="chess_moves.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

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
        SELECT move_id FROM mvoes
        WHERE lichess_id = ?
        """, (lichess_id,))
    game_id = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return game_id


def save_moves(game_id, hmove_nr, move_cost, db_name="chess_moves.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO moves
        (game_id, hmove_nr, move_cost)
        VALUES(?, ?, ?)        
        """, (
        game_id,
        hmove_nr,
        move_cost
    ))
    cursor.execute("""
        SELECT move_id FROM mvoes
        WHERE game_id = ? AND hmove_nr = ?
        """, (
        game_id,
        hmove_nr
    ))
    move_id = cursor.fetchone()[0]

    return move_id


def save_tags(tag, db_name="chess_moves.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

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


def save_moves_tags(move_id, tag_id, db_name="chess_moves.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
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

    conn.commit()
    conn.close()

    return move_tag_id
