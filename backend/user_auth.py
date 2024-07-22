import re
import hashlib
import sqlite3

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        reset_token TEXT
    );

    CREATE TABLE IF NOT EXISTS profiles (
        user_id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL,
        bio TEXT,
        profile_picture TEXT,
        favorite_music TEXT,
        recently_played_tracks TEXT,
        favorite_movies TEXT,
        recently_watched TEXT,
        ratings TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS friend_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_username TEXT,
        receiver_username TEXT,
        status TEXT,
        FOREIGN KEY (sender_username) REFERENCES users (username),
        FOREIGN KEY (receiver_username) REFERENCES users (username)
    );

    CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user1_username TEXT,
        user2_username TEXT,
        FOREIGN KEY (user1_username) REFERENCES users (username),
        FOREIGN KEY (user2_username) REFERENCES users (username)
    );
                         
    CREATE TABLE IF NOT EXISTS movie_ratings (
        user_id INTEGER NOT NULL,
        movie_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        PRIMARY KEY (user_id, movie_id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    ''')
    conn.commit()
    conn.close()

def alter_profiles_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(profiles)")
    columns = [column['name'] for column in cursor.fetchall()]

    if 'favorite_music' not in columns:
        cursor.execute("ALTER TABLE profiles ADD COLUMN favorite_music TEXT")
    if 'recently_played_tracks' not in columns:
        cursor.execute("ALTER TABLE profiles ADD COLUMN recently_played_tracks TEXT")
    if 'favorite_movies' not in columns:
        cursor.execute("ALTER TABLE profiles ADD COLUMN favorite_movies TEXT")
    if 'recently_watched' not in columns:
        cursor.execute("ALTER TABLE profiles ADD COLUMN recently_watched TEXT")
    if 'ratings' not in columns:
        cursor.execute("ALTER TABLE profiles ADD COLUMN ratings TEXT")
    
    conn.commit()
    conn.close()


def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

def is_valid_password(password):
    password_regex = r'^(?=.*[!@#$%^&*(),.?":{}|<>])(?=.*[a-zA-Z0-9]).{8,}$'
    return re.match(password_regex, password) is not None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(conn, username, email, password):
    cursor = conn.cursor()
    try:
        hashed_password = hash_password(password)
        cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, hashed_password))
        conn.commit()
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO profiles (user_id, username, email) VALUES (?, ?, ?)", (user_id, username, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(conn, identifier, password):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (identifier, identifier))
    user = cursor.fetchone()
    if user and user['password'] == hash_password(password):
        return user
    return None

def update_profile(conn, user_id, email, bio, profile_picture):
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE profiles
    SET email = ?, bio = ?, profile_picture = ?
    WHERE user_id = ?
    ''', (email, bio, profile_picture, user_id))
    conn.commit()

def get_profile(conn, username):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM profiles WHERE username = ?', (username,))
    row = cursor.fetchone()
    
    return dict(row) if row else None


def set_reset_token(conn, email, token):
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET reset_token = ? WHERE email = ?", (token, email))
    conn.commit()

def get_user_by_reset_token(conn, token):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE reset_token = ?", (token,))
    return cursor.fetchone()

def reset_password(conn, token, new_password):
    cursor = conn.cursor()
    hashed_password = hash_password(new_password)
    cursor.execute("UPDATE users SET password = ?, reset_token = NULL WHERE reset_token = ?", (hashed_password, token))
    conn.commit()
