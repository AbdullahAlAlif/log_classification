from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import pandas as pd
import os
from dotenv import load_dotenv
from functools import lru_cache
from classify import classify_csv  # Add this import

# Load environment variables
load_dotenv()

# Get absolute paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# Create required directories
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists('dataset'):
    os.makedirs('dataset')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Create Flask application instance
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')  # Add secret key for flash messages

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
    return render_template('index.html')

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
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)
                try:
                    classify_csv(filepath)
                    get_classification_results.cache_clear()
                    return redirect(url_for('results'))
                except Exception as e:
                    flash(f'Error processing file: {str(e)}')
                    return redirect(url_for('upload_file'))
            else:
                flash('Invalid file type')
                return redirect(url_for('upload_file'))
        
        # Render the upload page for GET requests
        return render_template('upload.html')
    except Exception as e:
        print(f"Error rendering upload template: {str(e)}")
        return str(e), 500

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
                               labels=cached_results['unique_labels'])
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
