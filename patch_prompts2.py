import re

def main():
    with open("veritas/config/dark_patterns.py", "r") as f:
        content = f.read()

    # Change to have a proper instruction for confidence
    content = content.replace(r'\"confidence\": 0.0', r'\"confidence\": \"<0.0-1.0 estimated confidence>\"')

    with open("veritas/config/dark_patterns.py", "w") as f:
        f.write(content)

if __name__ == "__main__":
    main()