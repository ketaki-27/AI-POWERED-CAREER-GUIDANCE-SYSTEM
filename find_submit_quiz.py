import os

search_term = "submit_quiz"
root_dir = '.'  # current directory

matches = []

for subdir, _, files in os.walk(root_dir):
    for file in files:
        if file.endswith(('.py', '.html', '.jinja2', '.txt')):  # check relevant file types
            filepath = os.path.join(subdir, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, start=1):
                        if search_term in line:
                            matches.append((filepath, i, line.strip()))
            except Exception as e:
                print(f"Could not read {filepath}: {e}")

if matches:
    print(f"Found '{search_term}' in these locations:")
    for filepath, lineno, line in matches:
        print(f"{filepath} (line {lineno}): {line}")
else:
    print(f"No occurrences of '{search_term}' found.")
