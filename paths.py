import os

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


import os
import textwrap

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






