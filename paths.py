import os
import subprocess
import argparse

def process_directory(input_dir, mode, output_dir=None):
    """
    Process a directory structure based on the specified mode.
    
    Args:
        input_dir (str): Path to the input directory.
        mode (str): Operation mode ('recreate', 'text', or 'bash').
        output_dir (str, optional): Path to the output directory for 'recreate' mode.
    
    Returns:
        str: Formatted directory structure or bash script content.
    """
    def get_directory_structure(directory, indent=0):
        """Recursively get directory structure and file contents."""
        structure = []
        for item in sorted(os.listdir(directory)):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                structure.append("  " * indent + f"{item}/")
                structure.extend(get_directory_structure(item_path, indent + 1))
            else:
                structure.append("  " * indent + f"{item}")
                try:
                    with open(item_path, 'r', encoding='utf-8') as f:
                        content = f.read().splitlines()
                        for line in content:
                            structure.append("  " * (indent + 1) + line)
                except Exception:
                    structure.append("  " * (indent + 1) + "[Unable to read file]")
        return structure

    # Get the directory structure
    dir_content = "\n".join(get_directory_structure(input_dir))

    if mode == "recreate":
        if not output_dir:
            raise ValueError("Output directory must be specified for recreate mode")
        # Create new directory structure
        for line in dir_content.splitlines():
            indent_level = len(line) - len(line.lstrip(" "))
            item = line.lstrip(" ")
            if item.endswith("/"):
                # Create directory
                os.makedirs(os.path.join(output_dir, item[:-1]), exist_ok=True)
            elif not line.startswith("  " * (indent_level + 1)):
                # Create empty file
                open(os.path.join(output_dir, item), 'a').close()
            else:
                # Write content to file
                parent_dir = line.rsplit("/", 1)[0] if "/" in line else ""
                file_path = os.path.join(output_dir, parent_dir, item)
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(line.lstrip(" ") + "\n")
        return f"Recreated directory structure in {output_dir}\n\n{dir_content}"

    elif mode == "text":
        # Return text response with directory structure
        return f"Directory structure and contents:\n\n{dir_content}"

    elif mode == "bash":
        # Generate bash script
        bash_script = ["#!/bin/bash", ""]
        current_dir = ""
        for line in dir_content.splitlines():
            indent_level = len(line) - len(line.lstrip(" "))
            item = line.lstrip(" ")
            if item.endswith("/"):
                bash_script.append(f"mkdir -p \"{item[:-1]}\"")
                current_dir = item[:-1]
            elif not line.startswith("  " * (indent_level + 1)):
                bash_script.append(f"touch \"{os.path.join(current_dir, item)}\"")
            else:
                bash_script.append(f"echo \"{item}\" >> \"{os.path.join(current_dir, item)}\"")
        
        bash_content = "\n".join(bash_script)
        script_path = "recreate_structure.sh"
        
        # Write bash script to file
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(bash_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        # Run the bash script
        try:
            result = subprocess.run(["bash", script_path], capture_output=True, text=True, check=True)
            return f"Bash script generated and executed:\n\n{bash_content}\n\nExecution output:\n{result.stdout}"
        except subprocess.CalledProcessError as e:
            return f"Error executing bash script:\n\n{bash_content}\n\nError output:\n{e.stderr}"

def main():
    parser = argparse.ArgumentParser(description="Process directory structure with different modes.")
    parser.add_argument("input_dir", help="Input directory path")
    parser.add_argument("--mode", choices=["recreate", "text", "bash"], default="text",
                        help="Operation mode: recreate (new directory), text (print structure), bash (generate and run script)")
    parser.add_argument("--output-dir", help="Output directory for recreate mode")
    
    args = parser.parse_args()
    
    if args.mode == "recreate" and not args.output_dir:
        parser.error("--output-dir is required for recreate mode")
    
    result = process_directory(args.input_dir, args.mode, args.output_dir)
    print(result)

if __name__ == "__main__":
    main()
