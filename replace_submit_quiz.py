import os

def replace_in_files(directory, old_text, new_text, file_extension='.html'):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith(file_extension):
                filepath = os.path.join(root, filename)
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                if old_text in content:
                    new_content = content.replace(old_text, new_text)
                    with open(filepath, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    print(f"Replaced in: {filepath}")

# Usage example: run this in your project root
replace_in_files('.', 'submit_quiz', 'quiz')
