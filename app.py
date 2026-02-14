from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename
import os
import shutil
from datetime import datetime, timedelta
from extensions import db
from models import Book, Chapter, Review, User, ReadingProgress
from itsdangerous import URLSafeTimedSerializer
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from flask_mail import Mail, Message



app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Or your SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'email@example.com'  # REPLACE THIS
app.config['MAIL_PASSWORD'] = 'xxxx xxxx xxxx xxxx'     # REPLACE THIS
app.config['MAIL_DEFAULT_SENDER'] = ('Book Club', 'email@example.com')# REPLACE THIS

mail = Mail(app)

app.secret_key = os.urandom(24)
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
os.makedirs(instance_path, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'books.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'images', 'covers')
app.config['BACKUP_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024



db.init_app(app)
mail = Mail(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['BACKUP_FOLDER'], exist_ok=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Archive Admin privileges required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def head_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_head:
            flash('Access denied. Head privileges required.', 'danger')
            return redirect(url_for('admin_panel'))
        return f(*args, **kwargs)
    return decorated_function

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        unique_filename = timestamp + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        return url_for('static', filename=f'images/covers/{unique_filename}')
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        login_input = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter((User.username == login_input) | (User.email == login_input)).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            if user.is_admin:
                return redirect(url_for('admin_panel'))
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or Email already exists.', 'danger')
            return redirect(url_for('register'))
            
        new_user = User(username=username, email=email, role='user')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('login.html', register_mode=True) 

@app.route('/')
def home():
    books = Book.query.order_by(Book.created_at.desc()).all()
    return render_template('home.html', books=books)

@app.route('/books/<int:book_id>')
def book_page(book_id):
    book = Book.query.get_or_404(book_id)
    user_progress = None
    if current_user.is_authenticated:
        user_progress = ReadingProgress.query.filter_by(user_id=current_user.id, book_id=book.id).first()
        
    return render_template('book_page.html', book=book, Review=Review, progress=user_progress)
@app.route('/shutdown')
def shutdown():
    archive_path = os.path.join('static', 'images', 'dev_archive')
    
    if os.path.exists(archive_path):
        files = [f for f in os.listdir(archive_path) 
                 if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.webm'))]
    else:
        files = []

    return render_template('shutdown.html', media_files=files)
@app.route('/test-email')
def test_email():
    try:
        msg = Message("Test Email", recipients=["YOUR_REAL_EMAIL@gmail.com"])
        msg.body = "If you are reading this, Flask-Mail is working!"
        mail.send(msg)
        return "Email sent successfully! Check your inbox."
    except Exception as e:
        return f"Error sending email: {str(e)}"

@app.route('/books/<int:book_id>/chapters/<int:chapter_id>')
def read_chapter(book_id, chapter_id):
    book = Book.query.get_or_404(book_id)
    chapter = Chapter.query.get_or_404(chapter_id)
    
    if current_user.is_authenticated:
        progress = ReadingProgress.query.filter_by(user_id=current_user.id, book_id=book_id).first()
        if not progress:
            progress = ReadingProgress(user_id=current_user.id, book_id=book_id, chapter_id=chapter_id)
            db.session.add(progress)
        else:
            progress.chapter_id = chapter_id
            progress.last_read_at = datetime.utcnow()
        db.session.commit()

    prev_chapter = Chapter.query.filter(Chapter.book_id == book_id, Chapter.chapter_number < chapter.chapter_number).order_by(Chapter.chapter_number.desc()).first()
    next_chapter = Chapter.query.filter(Chapter.book_id == book_id, Chapter.chapter_number > chapter.chapter_number).order_by(Chapter.chapter_number.asc()).first()
    return render_template('read_chapter.html', book=book, chapter=chapter, prev_chapter=prev_chapter, next_chapter=next_chapter)

@app.route('/books/<int:book_id>/review', methods=['GET', 'POST'])
@login_required
def submit_review(book_id):
    book = Book.query.get_or_404(book_id)
    if request.method == 'POST':
        content = request.form.get('content')
        if not content:
            flash('Review content is required.', 'danger')
            return redirect(url_for('submit_review', book_id=book_id))
            
        review = Review(
            book_id=book_id,
            user_id=current_user.id,
            reviewer_name=current_user.username,
            content=content
        )
        db.session.add(review)
        db.session.commit()
        flash('Review submitted for approval.', 'success')
        return redirect(url_for('book_page', book_id=book_id))
    return render_template('submit_review.html', book=book)

@app.route('/admin')
@admin_required
def admin_panel():
    books = Book.query.order_by(Book.created_at.desc()).all()
    return render_template('admin_panel.html', books=books)

@app.route('/admin/books/add', methods=['GET', 'POST'])
@admin_required
def add_book():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        image_file = request.files.get('cover_image')

        if not title or not description:
            flash('Title and description are required.', 'danger')
            return render_template('book_form.html', title=title, description=description)

        image_url = 'https://placehold.co/400x600/1F2937/9CA3AF?text=Cover' 
        if image_file and image_file.filename != '':
            if allowed_file(image_file.filename):
                image_url = save_image(image_file)
        
        new_book = Book(title=title, description=description, image_url=image_url)
        db.session.add(new_book)
        db.session.commit()

        try:
            users = User.query.filter(User.email != None).all()
            with mail.connect() as conn:
                for user in users:
                    msg = Message(f"New Book: {new_book.title}", recipients=[user.email])
                    msg.body = f"Hi {user.username}, check out {new_book.title} on Book Club!"
                    conn.send(msg)
        except Exception as e:
            print(f"Email error: {e}")

        flash('Book added successfully!', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('book_form.html')

@app.route('/admin/books/<int:book_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.description = request.form.get('description')
        image = request.files.get('cover_image')
        if image and allowed_file(image.filename):
            url = save_image(image)
            if url: book.image_url = url
        db.session.commit()
        flash('Book updated.', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('book_form.html', book=book)

@app.route('/admin/books/<int:book_id>/delete', methods=['POST'])
@admin_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/books/<int:book_id>/chapters')
@admin_required
def manage_chapters(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('manage_chapters.html', book=book)

@app.route('/admin/books/<int:book_id>/chapters/add', methods=['POST'])
@admin_required
def add_chapter(book_id):
    chapter_number = request.form.get('chapter_number')
    title = request.form.get('title')
    content = request.form.get('content')
    new_chapter = Chapter(book_id=book_id, chapter_number=chapter_number, title=title, content=content)
    db.session.add(new_chapter)
    db.session.commit()
    flash('Chapter added.', 'success')
    return redirect(url_for('manage_chapters', book_id=book_id))

@app.route('/admin/reviews')
@admin_required
def admin_reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('admin_reviews.html', reviews=reviews)

@app.route('/admin/reviews/<int:review_id>/approve', methods=['POST'])
@admin_required
def approve_review(review_id):
    review = Review.query.get_or_404(review_id)
    review.approved = True
    db.session.commit()
    return redirect(url_for('admin_reviews'))

@app.route('/admin/reviews/<int:review_id>/reject', methods=['POST'])
@admin_required
def reject_review(review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    return redirect(url_for('admin_reviews'))

@app.route('/admin/users')
@head_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/add', methods=['GET', 'POST'])
@head_required
def add_user():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        surname = request.form.get('surname')
        username_manual = request.form.get('username')
        password_manual = request.form.get('password')
        role = request.form.get('role', 'user')
        username = f"{first_name} {surname}" if (first_name and surname) else username_manual
        
        if User.query.filter_by(username=username).first():
            flash('User exists.', 'danger')
            return redirect(url_for('add_user'))

        new_user = User(username=username, role=role)
        
        if first_name and surname:
            new_user.set_password(os.urandom(16).hex())
            db.session.add(new_user)
            db.session.commit()
            s = URLSafeTimedSerializer(app.secret_key)
            token = s.dumps(username, salt='invite-user')
            link = url_for('accept_invite', token=token, _external=True)
            flash(f'User created. Invite link: {link}', 'success')
            return redirect(url_for('admin_users'))
        else:
            new_user.set_password(password_manual)
            db.session.add(new_user)
            db.session.commit()
            flash('User added.', 'success')
            return redirect(url_for('admin_users'))

    return render_template('user_form.html')

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@head_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.role = request.form.get('role')
        password = request.form.get('password')
        if password:
            user.set_password(password)
        db.session.commit()
        flash('User updated.', 'success')
        return redirect(url_for('admin_users'))
    return render_template('user_form.html', user=user)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@head_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_head and User.query.filter_by(role='head').count() == 1:
        flash('Cannot delete last Head user.', 'danger')
        return redirect(url_for('admin_users'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/backup', methods=['GET', 'POST'])
@head_required
def backup_database():
    if request.method == 'POST':
        db_path = os.path.join(instance_path, 'books.db')
        backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = os.path.join(app.config['BACKUP_FOLDER'], backup_filename)
        try:
            shutil.copy2(db_path, backup_path)
            flash(f'Backup created: {backup_filename}', 'success')
        except Exception as e:
            flash(f'Error: {e}', 'danger')
        return redirect(url_for('backup_database'))
    backups = sorted(os.listdir(app.config['BACKUP_FOLDER']), reverse=True)
    return render_template('admin_backup.html', backups=backups)

@app.route('/download/database')
@head_required
def download_database():
    return send_from_directory(directory=instance_path, path='books.db', as_attachment=True)

from models import ReadingProgress, Review


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_email = request.form.get('email')

        if new_username != current_user.username:
            if User.query.filter_by(username=new_username).first():
                flash('That username is already taken.', 'danger')
                return redirect(url_for('profile'))
            current_user.username = new_username

        if new_email != current_user.email:
            if User.query.filter_by(email=new_email).first():
                flash('That email is already being used.', 'danger')
                return redirect(url_for('profile'))
            current_user.email = new_email

        db.session.commit()
        flash('Profile details updated successfully.', 'success')
        return redirect(url_for('profile'))

    my_books = ReadingProgress.query.filter_by(user_id=current_user.id)\
        .order_by(ReadingProgress.last_read_at.desc()).all()
    
    my_reviews = Review.query.filter_by(user_id=current_user.id)\
        .order_by(Review.created_at.desc()).all()

    return render_template('profile.html', my_books=my_books, my_reviews=my_reviews)

@app.route('/admin/restore_from_list/<string:filename>', methods=['POST'])
@head_required
def restore_from_list(filename):
    backup_path = os.path.join(app.config['BACKUP_FOLDER'], filename)
    db_path = os.path.join(instance_path, 'books.db')

    if not os.path.exists(backup_path):
        flash('Backup file not found.', 'danger')
        return redirect(url_for('backup_database'))

    try:
        db.session.remove()
        
        shutil.copy2(backup_path, db_path)
        flash(f'Successfully restored database from {filename}.', 'success')
    except Exception as e:
        flash(f'Error restoring database: {e}', 'danger')
    
    return redirect(url_for('backup_database'))

@app.route('/admin/restore', methods=['POST'])
@head_required
def restore_database():
    if request.method == 'POST':
        backup_file = request.files.get('backup_file')
        
        if backup_file and backup_file.filename.endswith('.db'):
            db_path = os.path.join(instance_path, 'books.db')
            
            try:
                db.session.remove()
                backup_file.save(db_path)
                flash('Successfully restored database from backup.', 'success')
            except Exception as e:
                flash(f'Error restoring database: {e}', 'danger')
                
            return redirect(url_for('backup_database'))
        else:
            flash('Invalid file. Please upload a .db backup file.', 'danger')
            
    return redirect(url_for('backup_database'))

@app.route('/admin/books/<int:book_id>/chapters/<int:chapter_id>', methods=['GET'])
@admin_required
def get_chapter(book_id, chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    if chapter.book_id != book_id:
        return jsonify({'error': 'Chapter not found for this book'}), 404
        
    return jsonify({
        'id': chapter.id,
        'chapter_number': chapter.chapter_number,
        'title': chapter.title,
        'content': chapter.content
    })

@app.route('/admin/books/<int:book_id>/chapters/<int:chapter_id>/edit', methods=['POST'])
@admin_required
def edit_chapter(book_id, chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    if chapter.book_id != book_id:
        flash('Invalid chapter.', 'danger')
        return redirect(url_for('manage_chapters', book_id=book_id))

    chapter.chapter_number = request.form.get('chapter_number')
    chapter.title = request.form.get('title')
    chapter.content = request.form.get('content')
    
    db.session.commit()
    flash('Chapter updated successfully!', 'success')
    return redirect(url_for('manage_chapters', book_id=book_id))

@app.route('/admin/books/<int:book_id>/chapters/<int:chapter_id>/delete', methods=['POST'])
@admin_required
def delete_chapter(book_id, chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    if chapter.book_id != book_id:
        flash('Invalid chapter.', 'danger')
        return redirect(url_for('manage_chapters', book_id=book_id))
        
    db.session.delete(chapter)
    db.session.commit()
    flash('Chapter deleted successfully!', 'success')
    return redirect(url_for('manage_chapters', book_id=book_id))

@app.route('/admin/invite/<token>')
def accept_invite(token):
    s = URLSafeTimedSerializer(app.secret_key)
    try:
        username = s.loads(token, salt='invite-user', max_age=86400)
    except:
        flash('Invalid/Expired link.', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=username).first()
    if not user: return redirect(url_for('login'))
    
    login_user(user)
    flash('Welcome! Please set your password.', 'success')
    return redirect(url_for('change_password'))

@app.route('/admin/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password updated.', 'success')
        return redirect(url_for('home'))
    return render_template('change_password.html')


@app.route('/sitemap.xml')
def sitemap():
    return send_file('sitemap.xml', mimetype='application/xml')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=2500)# Change port if needed