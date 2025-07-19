import os
import requests
import textwrap
import json
import sys
import logging
import configparser
from pathlib import Path
from typing import Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('directory_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DirectoryProcessor:
    def __init__(self, config_path: str = "config.ini"):
        self.config = self._load_config(config_path)
        self.endpoint = self.config.get('LMStudio', 'endpoint', 
            fallback="http://192.168.0.16:1234/v1/chat/completions")
        self.default_query = self.config.get('LMStudio', 'default_query',
            fallback="Optimize and refactor this code structure, maintaining functionality but improving organization and efficiency.")

    def _load_config(self, config_path: str) -> configparser.ConfigParser:
        """Load configuration from INI file."""
        config = configparser.ConfigParser()
        try:
            config.read(config_path)
            if not config.sections():
                logger.warning(f"Config file {config_path} not found or empty, using defaults")
        except Exception as e:
            logger.error(f"Error reading config file: {str(e)}")
        return config

    def get_directory_structure(self, path: Path, indent: int = 0) -> str:
        """Recursively generate directory structure string."""
        tree_str = ""
        try:
            for item in sorted(os.listdir(path)):
                full_path = path / item
                tree_str += "    " * indent + f"{item}/\n" if full_path.is_dir() else "    " * indent + f"{item}\n"
                if full_path.is_dir():
                    tree_str += self.get_directory_structure(full_path, indent + 1)
                else:
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            for line in content.splitlines():
                                tree_str += "    " * (indent + 1) + f"{line}\n"
                    except Exception as e:
                        tree_str += "    " * (indent + 1) + f"[Error reading file: {str(e)}]\n"
        except PermissionError as e:
            logger.error(f"Permission denied accessing {path}: {str(e)}")
            tree_str += "    " * indent + f"[Permission denied: {path}]\n"
        return tree_str

    def directory_structure_as_string(self, path: str) -> str:
        """Convert directory structure to formatted string."""
        path_obj = Path(path)
        if not path_obj.is_dir():
            raise ValueError(f"The path '{path}' is not a valid directory.")
        return f'"""\n{self.get_directory_structure(path_obj)}"""'

    def query_lmstudio(self, prompt: str, endpoint: Optional[str] = None) -> Optional[str]:
        """Query LM Studio with given prompt."""
        endpoint = endpoint or self.endpoint
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.config.get('LMStudio', 'model', fallback="local-model"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.getfloat('LMStudio', 'temperature', fallback=0.7),
            "max_tokens": self.config.getint('LMStudio', 'max_tokens', fallback=2048),
            "stream": False
        }
        
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying LM Studio at {endpoint}: {str(e)}")
            return None
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Unexpected response format from {endpoint}: {response.text}")
            return None

    def parse_structure(self, structure_str: str, base_dir: str = 'output') -> None:
        """Parse directory structure string and create files."""
        lines = structure_str.strip().splitlines()
        path_stack = [base_dir]
        current_indent = 0
        current_file = None
        file_content_lines: List[str] = []

        def write_file(filepath: str, content_lines: List[str]) -> None:
            try:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(content_lines).rstrip() + '\n')
                logger.info(f"Created file: {filepath}")
            except Exception as e:
                logger.error(f"Error writing file {filepath}: {str(e)}")

        for line in lines:
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip())
            stripped = line.strip()
            
            while indent < current_indent:
                popped = path_stack.pop()
                if current_file == popped:
                    if file_content_lines:
                        write_file(os.path.join(*path_stack, current_file), file_content_lines)
                        file_content_lines = []
                    current_file = None
                current_indent -= 4
            
            if stripped.endswith('/'):
                path_stack.append(stripped[:-1])
                current_indent = indent + 4
            elif '.' in stripped and not stripped.startswith('#'):
                if current_file and file_content_lines:
                    write_file(os.path.join(*path_stack, current_file), file_content_lines)
                    file_content_lines = []
                current_file = stripped
                current_indent = indent + 4
                path_stack.append(current_file)
            else:
                file_content_lines.append(stripped)

        if current_file and file_content_lines:
            write_file(os.path.join(*path_stack[:-1], current_file), file_content_lines)

def main():
    processor = DirectoryProcessor()
    
    if len(sys.argv) < 2:
        logger.error("Directory path is required")
        print("Usage: python process_directory_with_lmstudio.py <directory_path> [query] [endpoint]")
        sys.exit(1)

    dir_path = sys.argv[1]
    query = sys.argv[2] if len(sys.argv) > 2 else processor.default_query
    endpoint = sys.argv[3] if len(sys.argv) > 3 else None

    try:
        dir_content = processor.directory_structure_as_string(dir_path)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    prompt = f"""Given the following directory structure and file contents, {query}:

{dir_content}

Please return the new directory structure and file contents in the same format as provided, with files properly indented under their directories and content indented under files.
"""
    
    response = processor.query_lmstudio(prompt, endpoint)
    if not response:
        logger.error("Failed to get response from LM Studio")
        sys.exit(1)

    output_dir = os.path.join(os.path.dirname(dir_path), f'output_{os.path.basename(dir_path)}')
    processor.parse_structure(response, base_dir=output_dir)
    logger.info(f"New directory structure created in {output_dir}")

if __name__ == "__main__":
    main()
