from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory
import sqlite3
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your_secret_key_here'  # Add a secret key for sessions

# Database initialization
def init_db():
    with sqlite3.connect('bookshare.db') as conn:
        c = conn.cursor()
        # Create users table
        c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )''')
        
        # Create books table
        c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            genre TEXT NOT NULL,
            description TEXT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )''')

        # Add admin user if it doesn't exist
        c.execute('SELECT * FROM users WHERE username = ?', ('admin',))
        if not c.fetchone():
            admin_password = generate_password_hash('admin123')
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                     ('admin', admin_password))
        
        conn.commit()

# Database helper functions
def get_db():
    conn = sqlite3.connect('bookshare.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize the database
init_db()

# Routes
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/homepage')
def homepage():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        
        try:
            with get_db() as conn:
                c = conn.cursor()
                c.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                         (username, password))
                conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return 'Username already exists!', 400
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        with get_db() as conn:
            c = conn.cursor()
            user = c.execute('SELECT * FROM users WHERE username = ?', 
                           (username,)).fetchone()
            
            if user and check_password_hash(user['password'], password):
                return redirect(url_for('homepage'))
            
        return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

@app.route('/addbook', methods=['GET', 'POST'])
def addbook():
    if request.method == 'POST':
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO books (title, author, genre, description)
                VALUES (?, ?, ?, ?)
            ''', (
                request.form['bookTitle'],
                request.form['bookAuthor'],
                request.form['bookGenre'],
                request.form['bookDescription']
            ))
            conn.commit()
        return render_template('addbook.html', message='Book added successfully!')
    return render_template('addbook.html')

@app.route('/searchbooks')
def searchbooks():
    query = request.args.get('query', '').lower()
    with get_db() as conn:
        c = conn.cursor()
        if query:
            c.execute('''
                SELECT * FROM books 
                WHERE LOWER(title) LIKE ? OR LOWER(author) LIKE ?
            ''', (f'%{query}%', f'%{query}%'))
        else:
            c.execute('SELECT * FROM books')
        books = c.fetchall()
    return render_template('searchbooks.html', books=books)

@app.route('/yourgenre', methods=['GET', 'POST'])
def yourgenre():
    if request.method == 'POST':
        search_genre = request.form.get('genre', '').lower()
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT * FROM books 
                WHERE LOWER(genre) LIKE ?
            ''', (f'%{search_genre}%',))
            
            books = [dict(row) for row in c.fetchall()]
            
            # Handle AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'books': books})
            
            # Handle regular form submissions
            return render_template('genre.html', books=books)
            
    return render_template('genre.html', books=[])

@app.route('/myborrow')
def myborrow():
    return render_template('myborrow.html')

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/myprofile')
def myprofile():
    return render_template('myprofile.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

if __name__ == '__main__':
    app.run(debug=True)