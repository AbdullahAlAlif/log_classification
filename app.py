from flask import Flask, render_template, request, redirect, url_for, current_app
import pandas as pd
from classify import classify_csv
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get absolute paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

print(f"Base directory: {BASE_DIR}")
print(f"Template directory: {TEMPLATE_DIR}")

# Create Flask application instance
app = Flask(__name__)  # Remove template_folder parameter

# Enable debug mode and template debugging
app.config.update(
    DEBUG=True,
    TEMPLATES_AUTO_RELOAD=True,
    EXPLAIN_TEMPLATE_LOADING=True  # Add this line for template debugging
)

# Add debug logging
app.logger.setLevel('DEBUG')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# Create required directories
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists('dataset'):
    os.makedirs('dataset')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    try:
        app.logger.info('Attempting to render upload.html')
        app.logger.info(f'Template folder: {app.template_folder}')
        templates = os.listdir(app.template_folder) if os.path.exists(app.template_folder) else []
        app.logger.info(f'Available templates: {templates}')
        
        if request.method == 'POST':
            if 'file' not in request.files:
                return redirect(request.url)
            file = request.files['file']
            if file.filename == '':
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filepath = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(filepath)
                try:
                    classify_csv(filepath)
                    return redirect(url_for('results'))
                except Exception as e:
                    return f"Error processing file: {str(e)}"
        return render_template('upload.html', error=None)
    except Exception as e:
        app.logger.error(f'Error rendering template: {str(e)}')
        return f'Error rendering template: {str(e)}', 500

@app.route('/results')
def results():
    try:
        df = pd.read_csv('dataset/output.csv')
        label_counts = df['target_label'].value_counts().to_dict()
        total_logs = len(df)
        unique_labels = df['target_label'].unique()
        return render_template('results.html', 
                            label_counts=label_counts, 
                            total_logs=total_logs, 
                            labels=unique_labels)
    except Exception as e:
        return f"Error loading results: {str(e)}"

@app.route('/filter/<label>')
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
    app.logger.error(f'Server Error: {error}')
    return str(error), 500

@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f'Not Found: {error}')
    return str(error), 404

# Modify the bottom of the file to properly expose the Flask app
def create_app():
    return app

application = app

# This allows both "flask run" and "python app.py" to work
if __name__ == '__main__':
    application.run(debug=True)
