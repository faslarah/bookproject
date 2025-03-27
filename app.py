from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory, session
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
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )''')
        
        # Create books table with email field
        c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            genre TEXT NOT NULL,
            description TEXT,
            user_id INTEGER,
            email TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (email) REFERENCES users (email)
        )''')

        # Add admin user if it doesn't exist
        c.execute('SELECT * FROM users WHERE email = ?', ('admin@example.com',))
        if not c.fetchone():
            c.execute('INSERT INTO users (email, password) VALUES (?, ?)',
                     ('admin@example.com', 'admin123'))
        
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
                session['email'] = email  # Store email in session
                session['user_id'] = user['id']  # Store user_id in session
                return redirect(url_for('homepage'))
            
        return render_template('login.html', error="Invalid email or password")
    return render_template('login.html')

@app.route('/addbook', methods=['GET', 'POST'])
def addbook():
    if request.method == 'POST':
        email = session.get('email')
        if not email:
            return redirect(url_for('login'))
            
        try:
            with get_db() as conn:
                c = conn.cursor()
                # Get user_id for the logged-in user
                c.execute('SELECT id FROM users WHERE email = ?', (email,))
                user = c.fetchone()
                if not user:
                    return redirect(url_for('login'))
                
                # Insert book with matching field names from schema
                c.execute('''
                    INSERT INTO books (title, author, genre, description, user_id, email)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    request.form['title'],
                    request.form['author'],
                    request.form['genre'],
                    request.form['description'],
                    user[0],  # user_id
                    email    # Using session email directly
                ))
                conn.commit()
                return render_template('addbook.html', message='Book added successfully!')
        except sqlite3.Error as e:
            return render_template('addbook.html', error=f"Error adding book: {str(e)}")
            
    return render_template('addbook.html')

@app.route('/searchbooks')
def searchbooks():
    query = request.args.get('query', '').lower()
    with get_db() as conn:
        c = conn.cursor()
        if query:
            c.execute('''
                SELECT b.*, u.email as owner_email 
                FROM books b 
                LEFT JOIN users u ON b.user_id = u.id 
                WHERE LOWER(b.title) LIKE ? OR LOWER(b.author) LIKE ?
            ''', (f'%{query}%', f'%{query}%'))
        else:
            c.execute('''
                SELECT b.*, u.email as owner_email 
                FROM books b 
                LEFT JOIN users u ON b.user_id = u.id
            ''')
        
        books = [dict(row) for row in c.fetchall()]
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'books': books})
        
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
    session.clear()  # Clear all session data
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)