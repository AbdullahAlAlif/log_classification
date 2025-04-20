# Log Classification System

A web-based tool for classifying and analyzing log files using a combination of Regular Expressions, Machine Learning (BERT) - logistic regression, and Large Language Models (LLMs). Built with Python and Flask.

## Features

- **User Authentication:** Register, log in, and manage your account.
- **Log Upload:** Upload `.csv`, `.xlsx`, or `.xls` log files for classification.
- **Classification Pipeline:**
  - Uses Regex for fast pattern-based classification.
  - Applies a BERT-based ML model for logs not matching patterns.
  - Uses an LLM (via Groq API) for complex or rare log types.


```
                    +----------------------+  
                    |  Flow Chart of the   |  
                    | Classify Process     |  
                    +----------------------+  
                            |  
                            v  
             +-------------------------------------------+  
             |  Is source equal to "LegacyCRM"?          |  
             +-------------------------------------------+  
                  |                           |  
                 Yes                          No  
                  |                           |  
                  v                           v  
       +-----------------------------+   +------------------------------+  
       | Call classify_with_llm()    |   | Call classify_with_regex()   |  
       |                             |   |                              |  
       | label = classify_with_llm() |   | label = classify_with_regex()|  
       +-----------------------------+   +------------------------------+  
                  |                                 |  
                  v                                 v  
          +------------------+        +-------------------------------+  
          |  Return label    |        |  Did regex return a label?    |  
          +------------------+        +-------------------------------+  
                                                |  
                                              /   \
                                          Yes       No  
                                          /          \  
                                         v            v  
                           +-------------------+  +------------------------------+  
                           |  Return label     |  | Call classify_with_bert()    |  
                           +-------------------+  | label = classify_with_bert() |  
                                                  +------------------------------+  
                                                                  |  
                                                                  v  
                                                         +-------------------+  
                                                         |   Return label    |  
                                                         +-------------------+  
```

- **Results Dashboard:** View classification results, filter by label, and see detailed log breakdowns.
- **User Upload History:** Registered users can view and revisit their previous uploads and results.
- **Temporary Results:** Non-logged-in users can classify logs and view results for their session.

## Log Categories

The system can classify logs into categories such as:
- Security Alert
- Error
- HTTP Status
- Workflow
- Deprecations
- Unknown (for unrecognized patterns)

## Setup Instructions

1. **Clone the Repository**
   ```
   git clone <repo-url>
   cd log classification app
   ```

2. **Install Dependencies**
   ```
   pip install -r requirements.txt
   ```

3. **Environment Variables**
   - Create a `.env` file in the root directory.
   - Add your Groq API key:
     ```
     GROQ_API_KEY=your_groq_api_key_here
     SECRET_KEY=your_flask_secret_key
     ```

4. **Run the Application**
   ```
   python log_classification/app.py
   ```
   The app will be available at `http://127.0.0.1:5000/`.

## Usage

- Register or log in to access full features.
- Upload your log file via the "Upload Logs" button.
- View classification results and filter logs by category.
- Registered users can revisit their upload history.

## Project Structure

- `log_classification/` - Main application code
  - `app.py` - Flask app and routes
  - `classify.py` - Classification logic
  - `process_regex.py`, `process_bert.py`, `process_LLM.py` - Classification engines
  - `templates/` - HTML templates
  - `uploads/` - Uploaded files
  - `dataset/` - Example/test datasets
- `requirements.txt` - Python dependencies

## Notes

- The system uses a hybrid approach for best accuracy and speed.
- The LLM model is accessed via the Groq API (see `.env` setup).
- The ML model uses sentence embeddings and logistic regression.

## License

This project is for educational and demonstration purposes.
