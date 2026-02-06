import sqlite3
import datetime
from livekit.agents import function_tool

# Initialize SQLite DB (creates mini_crm.db if not exists)
conn = sqlite3.connect('mini_crm.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT, 
    email TEXT               
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts(id)
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER,
    task TEXT,
    due_date DATE,
    FOREIGN KEY (contact_id) REFERENCES contacts(id)
)
''')
conn.commit()

@ function_tool()
async def search_contact(name: str) -> str:
    """Search for a contact by name and return details including notes and tasks."""
    cursor.execute("SELECT id, name, phone, email FROM contacts WHERE name LIKE ?", (f"%{name}%",))
    contacts = cursor.fetchall()
    if not contacts:
        return f"No contact found for '{name}'."
    
    result = ""
    for contact in contacts:
        contact_id, c_name, phone, email = contact
        result += f"Contact: {c_name} (ID: {contact_id}), Phone: {phone}, Email: {email}\n"

        # Get notes
        cursor.execute("SELECT note, created_at FROM notes WHERE contact_id = ?", (contact_id,))
        notes = cursor.fetchall()
        if notes:
            result += "Notes:\n" + "\n".join(f"- {note} ({created_at})" for note, created_at in notes) + "\n"
        
        # Get tasks
        cursor.execute("SELECT task, due_date FROM tasks WHERE contact_id = ?", (contact_id,))
        tasks = cursor.fetchall()
        if tasks:
            result += "Tasks:\n" + "\n".join(f"- {task} (due: {due_date})" for task, due_date in tasks)
    
    return result


@function_tool()
async def add_or_update_contact(name: str, phone: str = None, email: str = None) -> str:
    """Add a new contact or update an existing one by name."""
    cursor.execute("SELECT id FROM contacts WHERE name = ?", (name,))
    existing = cursor.fetchone()

    if existing:
        contact_id = existing[0]
        if phone:
            cursor.execute("UPDATE contacts SET phone = ? WHERE id = ?", (phone, contact_id))
        if email:    
            cursor.execute("UPDATE contacts SET email = ? WHERE id = ?", (email, contact_id))
        conn.commit()
        return f"Updated contact '{name}'."
    else:
        cursor.execute("INSERT INTO contacts (name, phone, email) VALUES (?, ?, ?)", (name, phone, email))
        conn.commit()
        return f"Added new contact '{name}'."
    
@function_tool()
async def add_note_to_contact(contact_name: str, note: str) -> str:
    """Add a note to a contact by name."""
    cursor.execute("SELECT id FROM contacts WHERE name = ?", (contact_name,))
    contact = cursor.fetchone()
    if not contact:
        return f"No contact found for '{contact_name}'."
    
    contact_id = contact[0]
    cursor.execute("INSERT INTO notes (contact_id, note) VALUES (?, ?)", (contact_id, note))
    conn.commit()
    return f"Added note to '{contact_name}': {note}"

@function_tool()
async def create_or_list_tasks(contact_name: str = None, task: str = None, due_date: str = None):
    """Create a new task for a contact (provide task and due_date) or list tasks for a contact (provide only contact_name). Due date format: YYYY-MM-DD."""
    if contact_name is None:
        return "Contact name required."
    
    cursor.execute("SELECT id FROM contacts WHERE name = ?", (contact_name,))
    contact = cursor.fetchone()
    if not contact:
        return f"No contact found for '{contact_name}'."
    
    contact_id  = contact[0]

    if task and due_date:
        cursor.execute("INSERT INTO tasks (contact_id, task, due_date) VALUES (?, ?, ?)",(contact_id, task, due_date))
        conn.commit()
        return f"Created task for '{contact_name}: {task} (due: {due_date})'"
    elif task or due_date:
        return "Must provide both task and due_date to create."
    else:
        # List tasks
        cursor.execute("SELECT task, due_date FROM tasks WHERE contact_id = ?", (contact_id,))
        tasks = cursor.fetchall()
        if not tasks:
            return f"No tasks for '{contact_name}'."
        return "Tasks for '{contact_name}':\n" + "\n".join(f"- {t} (due: {d})" for t, d in tasks)