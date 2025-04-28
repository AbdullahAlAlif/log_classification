import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # Loads the environment variables from .env file which includes G_API_KEY for the Gemini model

# Debug: Check if API key is loaded
#api_key = os.getenv("G_API_KEY")
#if not api_key:
#    print("Error: G_API_KEY not found in environment variables")
#    exit(1)
#else:
#    print("API key found with length:", len(api_key))

client = genai.Client(api_key=os.getenv("G_API_KEY"))  # Initialize the Gemini API client with the API key


def classify_with_llm(log_message):
    prompt = f"""You are a log message classifier machine answers in one Word and one Word only. Your task is to analyze the following log message and classify it into one of these categories: ('Workflow Error', 'Deprications',  or "Unknown").  
            The log message is: {log_message} .  
            Again Respond with ONLY One Word NO preambles or explanations."""
  
    response = client.models.generate_content(
        model="gemini-2.0-flash",  # The Gemini model to use for generating completions
        contents=prompt
    )
    return response.text.strip()  # Return the response text stripped of any extra whitespace


if __name__ == "__main__":
    test_logs = [
        "Failed to execute workflow step 3: Invalid input parameters",
        "Warning: Function xyz() will be deprecated in version 2.0",
        "Workflow execution halted due to missing dependencies",
        "This feature will be removed in the next major release",
        "Error: Workflow validation failed at node 'data_transform'",
        "Notice: Using legacy API endpoints - will be discontinued in future",
        "Critical error in workflow pipeline: Connection timeout",
        "Deprecation notice: Please use the new authentication method",
        "Hellow WOlrd!",
        "I love Burger"
    ]

    print("\nTesting log message classification:")
    print("-" * 50)
    for log in test_logs:
        result = classify_with_llm(log)
        print(f"\nLog message: {log}")
        print(f"Classification: {result}")

