import re

def process_text():
    sentence = input("Enter a sentence: ")
    words = re.findall(r'\b\w+\b', sentence.lower())  # Extract words, remove punctuation, and lowercase them
    print("\n".join(words))  # Print each word on a new line

if __name__ == "__main__":
    process_text()
