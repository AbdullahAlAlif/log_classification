
import re
def classify_with_regex(log_message):
    regex_patterns = {
        r"User User\d+ logged (in|out).": "User Action",
        r"Backup (started|ended) at .*": "System Notification",
        r"Backup completed successfully.": "System Notification",
        r"System updated to version .*": "System Notification",
        r"File .* uploaded successfully by user .*": "System Notification",
        r"Disk cleanup completed successfully.": "System Notification",
        r"System reboot initiated by user .*": "System Notification",
        r"Account with ID .* created by .*": "User Action"
    }
    for pattern, label in regex_patterns.items():
        if re.search(pattern, log_message,re.IGNORECASE):
            return label
    return None

if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("User User123 logged in.", "User Action"),
        ("User User456 logged out.", "User Action"), 
        ("Backup started at 2023-10-15 14:30:00", "System Notification"),
        ("Backup ended at 2023-10-15 14:35:00", "System Notification"),
        ("Backup completed successfully.", "System Notification"),
        ("System updated to version 2.1.0", "System Notification"),
        ("File report.pdf uploaded successfully by user admin", "System Notification"),
        ("Disk cleanup completed successfully.", "System Notification"),
        ("System reboot initiated by user root", "System Notification"),
        ("Account with ID 12345 created by admin", "User Action"),
        ("Random message that shouldn't match", None)
    ]

    print("Running tests for classify_with_regex function...")
    print("-" * 50)

    all_passed = True
    for message, expected in test_cases:
        result = classify_with_regex(message)
        passed = result == expected
        all_passed &= passed
        
        print(f"Test {'PASSED' if passed else 'FAILED'}")
        print(f"Input: {message}")
        print(f"Expected: {expected}")
        print(f"Got: {result}")
        print("-" * 50)

    print(f"\nOverall test result: {'ALL PASSED' if all_passed else 'SOME TESTS FAILED'}")