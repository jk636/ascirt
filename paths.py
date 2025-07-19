import os
import textwrap


def get_directory_structure(path, indent=0):
    tree_str = ""
    for item in sorted(os.listdir(path)):
        full_path = os.path.join(path, item)
        tree_str += "    " * indent + f"{item}/\n" if os.path.isdir(full_path) else "    " * indent + f"{item}\n"
        if os.path.isdir(full_path):
            tree_str += get_directory_structure(full_path, indent + 1)
    return tree_str

def directory_structure_as_string(path):
    if not os.path.isdir(path):
        raise ValueError(f"The path '{path}' is not a valid directory.")
    tree = get_directory_structure(path)
    return f'"""\n{tree}"""'


def parse_structure(structure_str, base_dir='.'):
    lines = structure_str.strip().splitlines()
    path_stack = [base_dir]
    current_indent = 0
    current_file = None
    file_content_lines = []

    def write_file(filepath, content_lines):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_lines).rstrip() + '\n')

    for line in lines:
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        # Determine level
        while indent < current_indent:
            popped = path_stack.pop()
            if current_file == popped:
                if file_content_lines:
                    write_file(os.path.join(*path_stack, current_file), file_content_lines)
                    file_content_lines = []
                current_file = None
            current_indent -= 4  # Assumes 4-space indents

        # New file or directory
        if stripped.endswith('/'):  # Directory
            path_stack.append(stripped[:-1])
            current_indent = indent + 4
        elif '.' in stripped:  # File
            if current_file and file_content_lines:
                write_file(os.path.join(*path_stack, current_file), file_content_lines)
                file_content_lines = []
            current_file = stripped
            current_indent = indent + 4
            path_stack.append(current_file)
        else:
            file_content_lines.append(stripped)

    # Handle last file
    if current_file and file_content_lines:
        write_file(os.path.join(*path_stack[:-1], current_file), file_content_lines)

import os

def combine_files(directory):
    """Reads files from a directory and combines their contents into a single string."""
    combined_string = ""
    try:
        for filename in sorted(os.listdir(directory)):  # Sort alphabetically for consistent results
            combined_string += '#############' + filename + '############\n'
            if os.path.isfile(os.path.join(directory, filename)):
                with open(os.path.join(directory, filename), 'r', encoding='utf-8') as f:  # Use utf-8 encoding to handle various characters
                    combined_string += f.read() + "\\n############end-of-ilr##########" # Add a newline between files.
                    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    return combined_string



import requests

def query_lmstudio(prompt, endpoint="http://localhost:1234/v1/chat/completions"):
    headers = {
        "Content-Type": "application/json"
    }

    # For chat models (like Mistral, LLaMA2, etc.)
    payload = {
        "model": "local-model",  # LM Studio ignores this, but it's required
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 256,
        "stream": False  # Change to True to handle streaming
    }

    try:
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        # Print the assistant's response
        print(result['choices'][0]['message']['content'])

    except requests.exceptions.RequestException as e:
        print("Error querying LM Studio:", e)
    except KeyError:
        print("Unexpected response format:", response.text)

if __name__ == "__main__":
    prompt = input("Enter your prompt: ")
    query_lmstudio(prompt)


if __name__ == "__main__":
    import sys
    dir_path = sys.argv[1] if len(sys.argv) > 1 else "."
    print(directory_structure_as_string(dir_path))
  
    structure_input = """
  project/
      main.py
          print("Hello, world!")
      utils/
          helper.py
              def greet():
                  return "Hi from helper"
      README.md
          # Project README
          This is an example project.
      """
  
      parse_structure(structure_input, base_dir='output')
      print("Directory structure created in ./output")






