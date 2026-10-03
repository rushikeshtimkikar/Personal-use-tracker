# Local Personal Notes App

A lightweight, completely offline personal notes app designed for storing, organizing, and interacting with AI chats and code snippets. Built with Python, Streamlit, and SQLite.

## Project Structure

- `app.py`: The main user interface and application logic written in Streamlit.
- `db.py`: Database operations for creating, reading, updating, and deleting notes using SQLite.
- `requirements.txt`: Python dependencies needed to run the app.
- `run.bat`: A quick-start Windows batch script to launch the app easily.
- `notes.db`: The local SQLite database file that is generated automatically on the first run.

## Setup Instructions (Windows)

1. **Create a Virtual Environment:**
   Open your Command Prompt or PowerShell in this folder and run:
   ```cmd
   python -m venv venv
   ```

2. **Activate the Virtual Environment:**
   ```cmd
   venv\Scripts\activate
   ```

3. **Install Requirements:**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Run the App:**
   ```cmd
   streamlit run app.py
   ```
   Or simply double-click the `run.bat` file to start it instantly!

## How the Code is Organized

- **Database (`db.py`):** Uses the built-in `sqlite3` library to communicate with the `notes.db` file. The `sqlite3.Row` factory makes it easy to access column data via keys (e.g., `row['title']`). All SQL operations use parameterized queries (`?`) to prevent SQL injection.
- **State Management (`app.py`):** Streamlit normally reruns the entire script from top to bottom every time you click a button. To remember which note you are viewing or editing, we use `st.session_state`.
- **Markdown & Checklists (`app.py`):** The function `render_markdown_with_checkboxes` reads your note line-by-line. If it detects standard Markdown code blocks, it skips them. If it finds `- [ ]` or `- [x]`, it swaps them out for interactive Streamlit `st.checkbox` widgets. Clicking one updates the database immediately.

Enjoy your offline learning companion!
