from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory

app = Flask(__name__, static_url_path='/static')

# In-memory storage for users and books
users = [
    {'username': 'admin', 'password': 'admin123'}
]
books = []

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
        password = request.form['password']
        if any(user['username'] == username for user in users):
            return 'Username already exists!', 400
        users.append({'username': username, 'password': password})
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Debug print
        print(f"Login attempt - Username: {username}")
        print(f"Current users: {users}")
        
        user = next((user for user in users if user['username'] == username and user['password'] == password), None)
        if user:
            print("Login successful")
            return redirect(url_for('homepage'))
        print("Login failed")
        return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

@app.route('/searchbooks')
def searchbooks():
    query = request.args.get('query', '').lower()
    if query:
        results = [book for book in books if 
                  query in book['title'].lower() or 
                  query in book['author'].lower()]
    else:
        results = books
    return render_template('searchbooks.html', books=results)

@app.route('/addbook', methods=['GET', 'POST'])
def addbook():
    if request.method == 'POST':
        book = {
            'title': request.form['bookTitle'],
            'author': request.form['bookAuthor'],
            'genre': request.form['bookGenre'],
            'description': request.form['bookDescription']
        }
        books.append(book)
        return render_template('addbook.html', message='Book added successfully!')
    return render_template('addbook.html')

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