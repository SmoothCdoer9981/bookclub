from datetime import datetime
import pytz
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# Define your desired timezone
TIMEZONE = pytz.timezone('Europe/London')

def current_time():
    """Get the current time in the specified timezone."""
    return datetime.now(TIMEZONE)

class Book(db.Model):
    __tablename__ = 'book'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(200))
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, nullable=False, default=current_time)
    updated_at = db.Column(db.DateTime, nullable=False, default=current_time, onupdate=current_time)
    chapters = db.relationship('Chapter', backref='book', lazy=True, cascade='all, delete-orphan', order_by='Chapter.chapter_number')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'subtitle': self.subtitle,
            'description': self.description,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'chapters': [chap.to_dict_simple() for chap in self.chapters]
        }

    def __repr__(self):
        return f'<Book {self.title}>'

class Chapter(db.Model):
    __tablename__ = 'chapter'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    chapter_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=current_time)
    updated_at = db.Column(db.DateTime, nullable=False, default=current_time, onupdate=current_time)

    __table_args__ = (
        db.UniqueConstraint('book_id', 'chapter_number', name='unique_chapter_number'),
    )

    def to_dict_simple(self):
        return {
            'id': self.id,
            'book_id': self.book_id,
            'chapter_number': self.chapter_number,
            'title': self.title,
            'created_at': self.created_at.isoformat(),
        }

    def to_dict_full(self):
        return {
            'id': self.id,
            'book_id': self.book_id,
            'chapter_number': self.chapter_number,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<Chapter {self.chapter_number}: {self.title}>'

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    reviewer_name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved = db.Column(db.Boolean, default=False)

    book = db.relationship('Book', backref=db.backref('reviews', lazy='dynamic'))
    user = db.relationship('User', backref='reviews')

    def to_dict(self):
        return {
            'id': self.id,
            'book_id': self.book_id,
            'user_id': self.user_id,
            'reviewer_name': self.reviewer_name,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'approved': self.approved
        }

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128))
    
    # Roles: 'user', 'admin', 'head'
    role = db.Column(db.String(20), nullable=False, default='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_head(self):
        return self.role == 'head'

    @property
    def is_admin(self):
        # Both Head and Admin can access the Archive
        return self.role in ['admin', 'head']

class ReadingProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    last_read_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    book = db.relationship('Book')
    chapter = db.relationship('Chapter')