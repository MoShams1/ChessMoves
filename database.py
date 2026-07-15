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

    conn.commit()
    conn.close()