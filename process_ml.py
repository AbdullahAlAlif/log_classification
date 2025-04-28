from sentence_transformers import SentenceTransformer
from joblib import load
 # Initialize the BERT model for embeddings
model = SentenceTransformer('all-MiniLM-L6-v2') #we dont want to load the model everytime we call the function
# Load the saved classifier
classifier_path = r"models/log_classification_model_knn.joblib"  # Use raw string and forward slashes
classifier = load(classifier_path)
    
def classify_with_ml(log_msg):

    # Get embedding for the log message
    embedding = model.encode([log_msg])[0]
    
    # Getting probabilities of each class of a message
    probabilities = classifier.predict_proba([embedding])[0]
    
    if max(probabilities) < 0.5:
        prediction = "Unknown"
    else:
        # Predict using the loaded model 
        prediction = classifier.predict([embedding])[0]
        
    
    return prediction

if __name__ =="__main__":
    logs = [
        "alpha.osapi_compute.wsgi.server - 12.10.11.1 - API returned 404 not found error",
        "GET /v2/3454/servers/detail HTTP/1.1 RCODE   404 len: 1583 time: 0.1878400",
        "System crashed due to drivers errors when restarting the server",
        "Hellow World!",
        "Multiple login failures occurred on user 6454 account",
        "Server A790 was restarted unexpectedly during the process of data transfer"
    ]
    for log in logs:
        label = classify_with_ml(log)  # Fix function name
        print(log, "->", label)
