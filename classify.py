from process_regex import classify_with_regex
from process_bert import classify_with_bert
from process_LLM import classify_with_llm


def classify_log(source, log_msg):
    if source == "LegacyCRM":
        label = classify_with_llm(log_msg)
    else:
        label = classify_with_regex(log_msg)
        if not label:
            label = classify_with_bert(log_msg)
    return label



def classify(logs):
    labels = []
    for source, log_msg in logs:
        label = classify_log(source, log_msg)
        labels.append(label)
    return labels


def classify_csv(input_file):
    import pandas as pd
    df = pd.read_csv(input_file)

    # Perform classification
    df["target_label"] = classify(list(zip(df["source"], df["log_message"]))) #We send a list of tupples*** 

    # Save the modified file
    output_file = "dataset/output.csv"
    df.to_csv(output_file, index=False)

    return output_file

if __name__ == '__main__':
    logs = [
        ("ModernHR", "Privilege escalation warning detected for user 6482"),
        ("LegacyCRM", "Case update for ticket ID 8247 failed as the assigned representative is no longer active."),
        ("AnalyticsEngine", "File data_4783.csv successfully uploaded by user User521."),
        ("ModernCRM", "IP 10.241.52.214 flagged due to unusual activity"),
        ("LegacyCRM", "Invoice generation halted for order ID 7632 due to errors in tax computation."),
        ("ModernHR", "GET /v3/21cdbe417ac04bdda7f9331e8d45ab1/servers/status HTTP/1.1 RCODE 200 len: 1720 time: 0.1934500"),
        ("LegacyCRM", "The 'InsightBuilder' feature is being retired in version 5.0. Transition to 'AdvancedMetricsSuite' before January 2026."),
        ("AnalyticsEngine", "Backup was completed without errors."),
        ("LegacyCRM", "The 'GroupMessageSender' functionality is deprecated. Switch to 'CampaignManagerPro' for better usability."),
        ("BillingSystem", "User 98765 accessed the platform."),
    ]

    labels = classify(logs)

    for log, label in zip(logs, labels):
        print(log[0], "->", label)
        
    output_file = classify_csv("dataset/test.csv")
    try:
        with open(output_file) as f:
            print(f"Classification results saved to: {output_file}")
    except FileNotFoundError:
        print(f"Error: {output_file} does not exist.")