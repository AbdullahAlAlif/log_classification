from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
import os
import json
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

# Temporary storage for non-logged-in users
temporary_results = None

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
    session.pop('current_table_name', None)
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
    global temporary_results  # Ensure we use the global variable
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
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)

                # Classify the file
                try:
                    output_file = classify_csv(filepath)
                    df = pd.read_csv(output_file)

                    # If logged in, save to the database
                    if 'user' in session:
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        file_name = file.filename.rsplit('.', 1)[0]
                        upload_date = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                        table_name = generate_unique_table_name(file_name)
                        cursor.execute(f'''
                            CREATE TABLE IF NOT EXISTS {table_name} (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                source TEXT,
                                log_message TEXT,
                                target_label TEXT
                            )
                        ''')
                        df.to_sql(table_name, conn, if_exists='append', index=False)
                        cursor.execute('''
                            INSERT INTO uploads (username, file_name, upload_date, table_name)
                            VALUES (?, ?, ?, ?)
                        ''', (session['user'], file_name, upload_date, table_name))
                        conn.commit()
                        conn.close()

                        # Redirect logged-in users to /user/uploads
                        flash('File uploaded and classified successfully.')
                        return redirect(url_for('user_uploads'))

                    # For non-logged-in users, store results temporarily
                    session['results'] = df.to_json(orient='split')
                    temporary_results = df.copy()  # fallback for legacy
                    flash('File uploaded and classified successfully.')
                    return redirect(url_for('results'))
                except Exception as e:
                    flash(f"Error processing file: {str(e)}")
                    return redirect(url_for('upload_file'))
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
    
    # Clear the current_table_name when leaving the results/filter context
    session.pop('current_table_name', None)
    
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
    # Store the current table_name in session for filtering
    session['current_table_name'] = table_name
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
                           user=session.get('user'))

@app.route('/results')
def results():
    global temporary_results  # Use the global variable for temporary storage
    try:
        if 'user' in session:
            # Use the table_name from session if present
            table_name = session.get('current_table_name')
            if table_name:
                conn = sqlite3.connect(DB_PATH)
                df = pd.read_sql_query(f'SELECT * FROM {table_name}', conn)
                conn.close()
                cached_results = {
                    'label_counts': df['target_label'].value_counts().to_dict(),
                    'total_logs': len(df),
                    'unique_labels': df['target_label'].unique()
                }
            else:
                cached_results = get_classification_results()
        else:
            # Non-logged-in users: Use the session-stored results
            df = None
            if 'results' in session:
                df = pd.read_json(session['results'], orient='split')
            elif temporary_results is not None:
                df = temporary_results
            if df is None or df.empty:
                flash('No classification results found')
                return redirect(url_for('upload_file'))
            
            cached_results = {
                'label_counts': df['target_label'].value_counts().to_dict(),
                'total_logs': len(df),
                'unique_labels': df['target_label'].unique()
            }

        return render_template('results.html', 
                               label_counts=cached_results['label_counts'],
                               total_logs=cached_results['total_logs'],
                               labels=cached_results['unique_labels'],
                               user=session.get('user'))  # Pass user to the template
    except Exception as e:
        print(f"Error rendering results template: {str(e)}")
        return str(e), 500

@app.route('/filter/<label>')
def filter_logs(label):
    global temporary_results  # Use the global variable for non-logged-in users
    try:
        if 'user' in session:
            # Use the table_name from session if present
            table_name = session.get('current_table_name')
            if table_name:
                conn = sqlite3.connect(DB_PATH)
                df = pd.read_sql_query(
                    f'SELECT source, log_message FROM {table_name} WHERE target_label = ?',
                    conn, params=(label,))
                conn.close()
            else:
                # fallback to previous logic (most recent upload)
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT table_name
                    FROM uploads
                    WHERE username = ?
                    ORDER BY upload_date DESC
                    LIMIT 1
                ''', (session['user'],))
                result = cursor.fetchone()
                conn.close()
                if not result:
                    flash('No classification results found')
                    return redirect(url_for('user_uploads'))
                table_name = result[0]
                conn = sqlite3.connect(DB_PATH)
                df = pd.read_sql_query(
                    f'SELECT source, log_message FROM {table_name} WHERE target_label = ?',
                    conn, params=(label,))
                conn.close()
        else:
            # Non-logged-in users: Use the session-stored results
            df = None
            if 'results' in session:
                df = pd.read_json(session['results'], orient='split')
            elif temporary_results is not None:
                df = temporary_results
            if df is None or df.empty:
                flash('No classification results found')
                return redirect(url_for('upload_file'))
            
            # Filter the temporary results for the selected label
            df = df[df['target_label'] == label]

        # Convert the filtered DataFrame to a list of dictionaries for rendering
        filtered_logs = df.to_dict('records')

        return render_template('filtered.html', logs=filtered_logs, label=label, user=session.get('user'))
    except Exception as e:
        print(f"Error filtering logs: {str(e)}")
        return str(e), 500

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

def clear_temporary_data():
    """Clear any temporary data for non-logged-in users."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Drop all temporary tables created for non-logged-in users
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'temp_%'")
        temp_tables = cursor.fetchall()
        for table in temp_tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
        conn.commit()
    finally:
        conn.close()

# Modify the bottom of the file to properly expose the Flask app
def create_app():
    clear_temporary_data()  # Clear temporary data on server start
    return app

application = app

# Update the run configuration
if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
