import sqlite3
import os

# Ensure we are looking at the correct database file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'books.db')

def promote_to_head():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        print("Make sure you placed this script in the same folder as app.py")
        return

    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ask for the username
    print("--- Manual Role Assignment ---")
    username = input("Enter the username you use to log in (default: admin): ").strip()
    if not username:
        username = 'admin'

    # Check if user exists
    cursor.execute("SELECT role FROM user WHERE username = ?", (username,))
    result = cursor.fetchone()

    if result:
        current_role = result[0]
        print(f"Found user '{username}'. Current role: '{current_role}'")
        
        # Force update to 'head'
        cursor.execute("UPDATE user SET role = 'head' WHERE username = ?", (username,))
        conn.commit()
        print(f"Success! '{username}' has been promoted to 'head'.")
        print("You can now access the Backup and User Management pages.")
    else:
        print(f"Error: User '{username}' not found in the database.")

    conn.close()

if __name__ == "__main__":
    promote_to_head()