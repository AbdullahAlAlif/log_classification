from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
import os
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from functools import lru_cache
from classify import classify_csv
import sqlite3

# Load environment variables
load_dotenv()

# Get absolute paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = 'uploads'
DB_PATH = os.path.join(BASE_DIR, 'users.db')
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# Create required directories
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists('dataset'):
    os.makedirs('dataset')

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Create uploads table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            file_name TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            table_name TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_table_name(base_name):
    """Generate a unique table name by appending a numeric postfix if needed."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    postfix = 0
    unique_name = base_name
    while True:
        cursor.execute('SELECT 1 FROM uploads WHERE table_name = ?', (unique_name,))
        if cursor.fetchone() is None:
            break
        postfix += 1
        unique_name = f"{base_name}_{postfix}"
    conn.close()
    return unique_name

# Create Flask application instance
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')

# Update app configuration
app.config.update(
    DEBUG=True,
    TEMPLATES_AUTO_RELOAD=True,
    SEND_FILE_MAX_AGE_DEFAULT=0,
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max file size
)

# Cache for expensive operations
@lru_cache(maxsize=32)
def get_classification_results():
    try:
        df = pd.read_csv('dataset/output.csv')
        return {
            'label_counts': df['target_label'].value_counts().to_dict(),
            'total_logs': len(df),
            'unique_labels': df['target_label'].unique().tolist()
        }
    except Exception:
        return None

@app.route('/')
def index():
    return render_template('index.html', user=session.get('user'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            conn.close()
            flash('Registration successful. Please log in.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[0], password):
            session['user'] = username
            flash('Login successful.')
            return redirect(url_for('index'))
        flash('Invalid username or password.')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/account')
def account():
    if 'user' not in session:
        flash('Please log in to access your account.')
        return redirect(url_for('login'))
    return render_template('account.html', user=session.get('user'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    try:
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file selected')
                return redirect(url_for('upload_file'))
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected')
                return redirect(url_for('upload_file'))
            
            if file and allowed_file(file.filename):
                # Save file
                file_name = file.filename.rsplit('.', 1)[0]
                upload_date = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                table_name = generate_unique_table_name(file_name)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)

                # Classify and save results in a database table
                classify_csv(filepath)
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source TEXT,
                        log_message TEXT,
                        target_label TEXT
                    )
                ''')
                df = pd.read_csv('dataset/output.csv')
                df.to_sql(table_name, conn, if_exists='append', index=False)

                # Save upload metadata if the user is logged in
                if 'user' in session:
                    cursor.execute('''
                        INSERT INTO uploads (username, file_name, upload_date, table_name)
                        VALUES (?, ?, ?, ?)
                    ''', (session['user'], file_name, upload_date, table_name))
                    conn.commit()

                conn.close()
                flash('File uploaded and classified successfully.')
                return redirect(url_for('results'))
            else:
                flash('Invalid file type')
                return redirect(url_for('upload_file'))
        
        # Render the upload page for GET requests
        return render_template('upload.html')
    except Exception as e:
        print(f"Error rendering upload template: {str(e)}")
        return str(e), 500

@app.route('/user/uploads')
def user_uploads():
    if 'user' not in session:
        flash('Please log in to view your uploads.')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT file_name, upload_date, table_name
        FROM uploads
        WHERE username = ?
        ORDER BY upload_date DESC
    ''', (session['user'],))
    uploads = cursor.fetchall()
    conn.close()
    return render_template('user_uploads.html', uploads=uploads, user=session.get('user'))

@app.route('/user/uploads/<table_name>')
def view_upload_results(table_name):
    if 'user' not in session:
        flash('Please log in to view results.')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM uploads WHERE table_name = ? AND username = ?', (table_name, session['user']))
    if cursor.fetchone() is None:
        conn.close()
        flash('You do not have access to this upload.')
        return redirect(url_for('user_uploads'))
    
    df = pd.read_sql_query(f'SELECT * FROM {table_name}', conn)
    conn.close()
    return render_template('results.html', 
                           label_counts=df['target_label'].value_counts().to_dict(),
                           total_logs=len(df),
                           labels=df['target_label'].unique(),
                           user=session.get('user'))  # Pass user to the template

@app.route('/results')
def results():
    try:
        cached_results = get_classification_results()
        if not cached_results:
            flash('No classification results found')
            return redirect(url_for('upload_file'))
        
        return render_template('results.html', 
                               label_counts=cached_results['label_counts'],
                               total_logs=cached_results['total_logs'],
                               labels=cached_results['unique_labels'],
                               user=session.get('user'))  # Pass user to the template
    except Exception as e:
        print(f"Error rendering results template: {str(e)}")
        return str(e), 500

@app.route('/filter/<label>')
@lru_cache(maxsize=32)
def filter_logs(label):
    try:
        df = pd.read_csv('dataset/output.csv')
        filtered_logs = df[df['target_label'] == label].to_dict('records')
        return render_template('filtered.html', logs=filtered_logs, label=label)
    except Exception as e:
        return f"Error filtering logs: {str(e)}"

@app.route('/about')
def about():
    return render_template('about.html', user=session.get('user'))

# Add error handlers
@app.errorhandler(500)
def internal_error(error):
    return str(error), 500

@app.errorhandler(404)
def not_found_error(error):
    return str(error), 404

# Modify the bottom of the file to properly expose the Flask app
def create_app():
    return app

application = app

# Update the run configuration
if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
