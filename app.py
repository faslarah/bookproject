from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory
import sqlite3
from functools import wraps


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
            email TEXT UNIQUE NOT NULL,
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
            admin_password = 'admin123'
            c.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                     ('admin', 'admin@example.com', admin_password))
        
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
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not email or not password:
            return render_template('register.html', error="Email and password are required")
        
        try:
            with get_db() as conn:
                c = conn.cursor()
                c.execute('SELECT * FROM users WHERE email = ?', (email,))
                if c.fetchone():
                    return render_template('register.html', error="Email already exists")
                
                c.execute('INSERT INTO users (email, password) VALUES (?, ?)',
                         (email, password))
                conn.commit()
                return redirect(url_for('login'))
        except sqlite3.Error as e:
            return render_template('register.html', error=f"Database error: {str(e)}")
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        with get_db() as conn:
            c = conn.cursor()
            user = c.execute('SELECT * FROM users WHERE email = ? AND password = ?', 
                           (email, password)).fetchone()
            
            if user:
                return redirect(url_for('homepage'))
            
        return render_template('login.html', error="Invalid email or password")
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
        
        # Convert rows to dictionaries
        books = []
        for row in c.fetchall():
            book = {}
            for idx, col in enumerate(c.description):
                book[col[0]] = row[idx]
            books.append(book)
        
        # Return JSON for AJAX requests
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'books': books})
        
        # Return HTML for normal requests
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

@app.route('/logout')
def logout():
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)