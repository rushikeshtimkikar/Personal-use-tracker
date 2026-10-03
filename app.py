# app.py
import streamlit as st
import json
import re
import db

# Set Streamlit page configuration (must be the first Streamlit command)
st.set_page_config(page_title="Personal Notes", layout="wide")

# Initialize the database on startup
db.init_db()

# Initialize session state variables for navigation and interaction
if "current_note_id" not in st.session_state:
    st.session_state.current_note_id = None
if "view" not in st.session_state:
    st.session_state.view = "home"  # Views: home, add, view_note, edit_note
if "delete_confirm" not in st.session_state:
    st.session_state.delete_confirm = False

# Calculate and display a progress bar for checklists in a note
def display_progress_bar(content):
    if not content:
        return
        
    lines = content.split('\n')
    total = 0
    checked = 0
    in_code_block = False
    
    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
        if not in_code_block:
            if re.match(r'^\s*- \[( |x|X)\]', line):
                total += 1
                if re.match(r'^\s*- \[(x|X)\]', line):
                    checked += 1
                    
    if total > 0:
        st.write(f"**Progress:** {checked} of {total} done")
        st.progress(checked / total)

# Render markdown content and convert "- [ ]" and "- [x]" to interactive checkboxes
def render_markdown_with_checkboxes(note_id, content):
    if not content:
        return

    lines = content.split('\n')
    new_lines = []
    changed = False
    md_buffer = []
    in_code_block = False
    
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            
        match = re.match(r'^(\s*)- \[( |x|X)\] (.*)', line)
        if match and not in_code_block:
            # Render any buffered markdown text first
            if md_buffer:
                st.markdown('\n'.join(md_buffer))
                md_buffer = []
            
            indent, state, text = match.groups()
            is_checked = state.lower() == 'x'
            
            # Show the checkbox. Use a unique key based on note ID and line number.
            checked = st.checkbox(text, value=is_checked, key=f"cb_{note_id}_{i}")
            
            # If the user toggled the checkbox, mark as changed
            if checked != is_checked:
                changed = True
                new_state = 'x' if checked else ' '
                new_lines.append(f"{indent}- [{new_state}] {text}")
            else:
                new_lines.append(line)
        else:
            md_buffer.append(line)
            new_lines.append(line)
            
    # Render any remaining markdown text blocks
    if md_buffer:
        st.markdown('\n'.join(md_buffer))
        
    # If a checkbox was clicked, update the database and rerun to reflect changes instantly
    if changed:
        new_content = '\n'.join(new_lines)
        db.update_note_content(note_id, new_content)
        st.rerun()

# Sidebar UI for filtering, sorting, and listing notes
def sidebar_ui():
    st.sidebar.title("📚 My Notes")
    
    if st.sidebar.button("➕ New Note", use_container_width=True, type="primary"):
        st.session_state.view = "add"
        st.session_state.current_note_id = None
        
    st.sidebar.divider()
    
    # Search and Filter fields
    search_query = st.sidebar.text_input("🔍 Search")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        sort_by = st.selectbox("Sort", ["Newest", "Oldest", "Title"])
    with col2:
        cat_filter = st.selectbox("Category", ["All", "Roadmap", "Checklist", "Concept", "Code", "Prompt", "Other"])
        
    all_tags = db.get_unique_tags()
    tag_filter = st.sidebar.multiselect("Tags", all_tags)
    
    # Fetch and filter notes based on user input
    all_notes = db.get_all_notes(sort_by=sort_by)
    filtered_notes = []
    
    for note in all_notes:
        match = True
        
        # Apply category filter
        if cat_filter != "All" and note['category'] != cat_filter:
            match = False
            
        # Apply tag filter
        if tag_filter:
            note_tags = [t.strip() for t in (note['tags'] or "").split(',')] if note['tags'] else []
            if not any(t in note_tags for t in tag_filter):
                match = False
                
        # Apply search query
        if search_query:
            q = search_query.lower()
            t = (note['title'] or "").lower()
            c = (note['content'] or "").lower()
            tags_str = (note['tags'] or "").lower()
            if q not in t and q not in c and q not in tags_str:
                match = False
                
        if match:
            filtered_notes.append(note)
            
    st.sidebar.subheader("Notes List")
    if not filtered_notes:
        st.sidebar.info("No notes found.")
        
    # Display note buttons in the sidebar
    for note in filtered_notes:
        prefix = "⭐ " if note['pinned'] else ""
        if st.sidebar.button(f"{prefix}{note['title']}", key=f"nav_{note['id']}", use_container_width=True):
            st.session_state.current_note_id = note['id']
            st.session_state.view = "view_note"
            st.session_state.delete_confirm = False
            
    st.sidebar.divider()
    
    # Backup / Restore functionalities
    st.sidebar.subheader("Backup & Restore")
    
    # Export button
    all_notes_dicts = [dict(row) for row in db.get_all_notes()]
    json_data = json.dumps(all_notes_dicts, indent=4)
    st.sidebar.download_button("💾 Export All to JSON", data=json_data, file_name="notes_backup.json", mime="application/json")
    
    # Import uploader
    uploaded_file = st.sidebar.file_uploader("📂 Import JSON Backup", type=["json"])
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            if isinstance(data, list):
                added = db.import_notes(data)
                st.sidebar.success(f"Imported {added} new notes!")
            else:
                st.sidebar.error("Invalid JSON format. Expected a list of notes.")
        except Exception:
            st.sidebar.error("Error reading JSON file.")

# Show the form to add a new note
def add_note_view():
    st.header("➕ Add New Note")
    
    title = st.text_input("Title")
    category = st.selectbox("Category", ["Roadmap", "Checklist", "Concept", "Code", "Prompt", "Other"])
    tags = st.text_input("Tags (comma separated, e.g. python, sql)")
    content = st.text_area("Content (Markdown supported)", height=400)
    
    if st.button("Save Note", type="primary"):
        if not title.strip():
            st.error("Title is required to save a note!")
        else:
            note_id = db.add_note(title.strip(), content, category, tags)
            st.session_state.current_note_id = note_id
            st.session_state.view = "view_note"
            st.rerun()

# Show the form to edit an existing note
def edit_note_view():
    note = db.get_note_by_id(st.session_state.current_note_id)
    if not note:
        st.error("Note not found.")
        st.session_state.view = "home"
        st.rerun()
        return
        
    st.header("✏️ Edit Note")
    
    title = st.text_input("Title", value=note['title'])
    categories = ["Roadmap", "Checklist", "Concept", "Code", "Prompt", "Other"]
    cat_index = categories.index(note['category']) if note['category'] in categories else 0
    category = st.selectbox("Category", categories, index=cat_index)
    
    tags = st.text_input("Tags (comma separated)", value=note['tags'])
    content = st.text_area("Content (Markdown supported)", value=note['content'], height=400)
    pinned = st.checkbox("⭐ Pin Note", value=bool(note['pinned']))
    
    col1, col2 = st.columns([1, 10])
    with col1:
        if st.button("Save", type="primary"):
            if not title.strip():
                st.error("Title is required!")
            else:
                db.update_note(note['id'], title.strip(), content, category, tags, int(pinned))
                st.session_state.view = "view_note"
                st.rerun()
    with col2:
        if st.button("Cancel"):
            st.session_state.view = "view_note"
            st.rerun()

# Display a single note with view controls
def view_note_view():
    note = db.get_note_by_id(st.session_state.current_note_id)
    if not note:
        st.error("Note not found.")
        st.session_state.view = "home"
        st.rerun()
        return
        
    # Layout for title and actions
    col1, col2 = st.columns([3, 1])
    with col1:
        prefix = "⭐ " if note['pinned'] else ""
        st.header(f"{prefix}{note['title']}")
        # Ensure values don't break if None
        safe_tags = note['tags'] if note['tags'] else "None"
        safe_cat = note['category'] if note['category'] else "Uncategorized"
        created_str = note['created_at'][:10] if note['created_at'] else "Unknown"
        st.caption(f"**Category:** {safe_cat} | **Tags:** {safe_tags} | **Created:** {created_str}")
    
    with col2:
        action_col1, action_col2, action_col3 = st.columns(3)
        with action_col1:
            if st.button("✏️ Edit"):
                st.session_state.view = "edit_note"
                st.rerun()
        with action_col2:
            if st.button("📌 Pin" if not note['pinned'] else "Unpin"):
                db.update_note(note['id'], note['title'], note['content'], note['category'], note['tags'], 1 - note['pinned'])
                st.rerun()
        with action_col3:
            # Prepare and provide single note Markdown download
            safe_content = note['content'] if note['content'] else ""
            md_content = f"# {note['title']}\n\n**Category:** {safe_cat}\n**Tags:** {safe_tags}\n\n---\n\n{safe_content}"
            st.download_button("⬇️ .md", data=md_content, file_name=f"{note['title']}.md", mime="text/markdown")

    st.divider()
    
    # Progress bar and checklists logic
    if note['content']:
        display_progress_bar(note['content'])
        render_markdown_with_checkboxes(note['id'], note['content'])
    
    st.divider()
    
    # Delete note functionality with confirmation step
    if st.button("🗑️ Delete Note"):
        st.session_state.delete_confirm = True
        
    if st.session_state.get('delete_confirm', False):
        st.warning("Are you sure you want to delete this note? This action cannot be undone.")
        del_col1, del_col2 = st.columns(2)
        with del_col1:
            if st.button("Yes, Delete", type="primary"):
                db.delete_note(note['id'])
                st.session_state.delete_confirm = False
                st.session_state.view = "home"
                st.session_state.current_note_id = None
                st.rerun()
        with del_col2:
            if st.button("Cancel Delete"):
                st.session_state.delete_confirm = False
                st.rerun()

# Main Application Entry Point
def main():
    sidebar_ui()
    
    # Router logic based on current session state view
    if st.session_state.view == "home":
        st.title("👋 Welcome to Personal Notes!")
        st.write("👈 Select a note from the sidebar or click **➕ New Note** to get started.")
        st.write("You can paste Markdown content, track interactive checklists, and organize your AI chats effectively!")
    elif st.session_state.view == "add":
        add_note_view()
    elif st.session_state.view == "view_note":
        view_note_view()
    elif st.session_state.view == "edit_note":
        edit_note_view()

if __name__ == "__main__":
    main()
