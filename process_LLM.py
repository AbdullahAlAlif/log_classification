from dotenv import load_dotenv
from groq import Groq

load_dotenv() #loads the environemtn variables from .env file which is ouire GROQ_API_KEY for LLM model

# Debug: Check if API key is loaded
#api_key = os.getenv("GROQ_API_KEY")
#if not api_key:
#    print("Error: GROQ_API_KEY not found in environment variables")
#    exit(1)
#else:
#    print("API key found with length:", len(api_key))
#okh so deepseek-r1-distill-lamma-70b dosent exists so we will llama-3.3-70b-versatile
groq = Groq() #groq will use the variable (ALI KEY)


def classify_with_llm(log_message):
    prompt = f"""You are a log message classifier machine answers in one Word and one Word only. Your task is to analyze the following log message and classify it into one of these categories: ('Workflow Error' , 'Deprications' or "Unknown").
    The log message is: {log_message} .
    Again Respond with ONLY One Word NO preamble"""
  
    response=groq.chat.completions.create(
        model="llama-3.3-70b-versatile",  # The model to use for generating completions
        messages=[
            {
                "role": "user",  # The role of the message sender (user or assistant)
                "content": prompt  # The actual message content
            }
        ],
        temperature=0.7,  # Controls randomness: 0.0 is deterministic, higher values (up to 1.0) increase randomness
        max_tokens=4096,  # Maximum number of tokens to generate in the response
        top_p=0.4,  # Controls diversity via nucleus sampling: lower values make output more focused
        stream=False  # Whether to stream the response (True) or return it all at once (False)
    )
    return response.choices[0].message.content
# Print the response
#print("\nModel Response:")
#rint(response.choices[0].message.content)


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

