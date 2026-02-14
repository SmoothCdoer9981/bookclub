from app import app, db
from models import User

def reset_admin_user():
    """
    Deletes all users and creates a default admin user.
    This script should be run from your terminal.
    """
    with app.app_context():
        # Delete all existing users from the database
        try:
            num_deleted = db.session.query(User).delete()
            db.session.commit()
            if num_deleted > 0:
                print(f"Successfully deleted {num_deleted} user(s).")
            else:
                print("No existing users to delete.")
        except Exception as e:
            db.session.rollback()
            print(f"An error occurred while deleting users: {e}")
            return

        # Create the default admin user
        try:
            print("Creating default admin user...")
            admin_user = User(username='Admin', role='head')
            admin_user.set_password('admin')
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user 'Admin' has been successfully created. Default Password is 'admin'")
        except Exception as e:
            db.session.rollback()
            print(f"An error occurred while creating the new admin user: {e}")

if __name__ == '__main__':
    reset_admin_user()