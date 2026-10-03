# db.py
import sqlite3
import datetime

DB_FILE = 'notes.db'

def get_db():
    # check_same_thread=False allows Streamlit to use the connection across threads securely
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def init_db():
    # Creates the notes table if it does not exist.
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            category TEXT,
            tags TEXT,
            pinned INTEGER DEFAULT 0,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_all_notes(sort_by="Newest"):
    # Retrieves all notes, sorting based on user preference and pinned status.
    conn = get_db()
    try:
        order_clause = "ORDER BY pinned DESC, created_at DESC"
        if sort_by == "Oldest":
            order_clause = "ORDER BY pinned DESC, created_at ASC"
        elif sort_by == "Title":
            order_clause = "ORDER BY pinned DESC, title COLLATE NOCASE ASC"
            
        query = f"SELECT * FROM notes {order_clause}"
        cursor = conn.execute(query)
        notes = cursor.fetchall()
        return notes
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

def get_note_by_id(note_id):
    # Retrieves a single note by its ID.
    conn = get_db()
    try:
        cursor = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
        return cursor.fetchone()
    finally:
        conn.close()

def add_note(title, content, category, tags, pinned=0):
    # Inserts a new note securely using parameterized queries.
    conn = get_db()
    try:
        now = datetime.datetime.now().isoformat()
        cursor = conn.execute('''
            INSERT INTO notes (title, content, category, tags, pinned, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, content, category, tags, pinned, now, now))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def update_note(note_id, title, content, category, tags, pinned):
    # Updates a note's full details (used from the edit screen).
    conn = get_db()
    try:
        now = datetime.datetime.now().isoformat()
        conn.execute('''
            UPDATE notes 
            SET title = ?, content = ?, category = ?, tags = ?, pinned = ?, updated_at = ?
            WHERE id = ?
        ''', (title, content, category, tags, pinned, now, note_id))
        conn.commit()
    finally:
        conn.close()

def update_note_content(note_id, content):
    # Updates only the content (useful for toggling checkboxes instantly).
    conn = get_db()
    try:
        now = datetime.datetime.now().isoformat()
        conn.execute('''
            UPDATE notes 
            SET content = ?, updated_at = ?
            WHERE id = ?
        ''', (content, now, note_id))
        conn.commit()
    finally:
        conn.close()

def delete_note(note_id):
    # Deletes a note permanently.
    conn = get_db()
    try:
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()
    finally:
        conn.close()

def get_unique_tags():
    # Extracts all unique tags from the database for the sidebar filter.
    conn = get_db()
    try:
        cursor = conn.execute("SELECT tags FROM notes")
        all_tags = set()
        for row in cursor.fetchall():
            if row['tags']:
                tags = [t.strip() for t in row['tags'].split(',') if t.strip()]
                all_tags.update(tags)
        return sorted(list(all_tags))
    finally:
        conn.close()

def import_notes(notes_list):
    # Inserts notes from a backup list, skipping duplicates based on title and content.
    conn = get_db()
    try:
        cursor = conn.execute("SELECT title, content FROM notes")
        existing = set((row['title'], row['content']) for row in cursor.fetchall())
        
        added = 0
        now = datetime.datetime.now().isoformat()
        for note in notes_list:
            if (note['title'], note['content']) not in existing:
                conn.execute('''
                    INSERT INTO notes (title, content, category, tags, pinned, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (note['title'], note['content'], note['category'], note['tags'], note.get('pinned', 0), note.get('created_at', now), note.get('updated_at', now)))
                added += 1
                existing.add((note['title'], note['content']))
        
        conn.commit()
        return added
    finally:
        conn.close()
