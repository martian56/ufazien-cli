"""
Utility functions for the Ufazien CLI.
"""

import hashlib
import json
import os
import random
import re
import string
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional


def get_input(prompt: str, default: Optional[str] = None, required: bool = True) -> Optional[str]:
    """Get user input with optional default value."""
    if default:
        prompt_text = f"{prompt} [{default}]: "
    else:
        prompt_text = f"{prompt}: "

    while True:
        value = input(prompt_text).strip()
        if value:
            return value
        elif default:
            return default
        elif not required:
            return None
        else:
            print("This field is required. Please enter a value.")


def get_yes_no(prompt: str, default: bool = False) -> bool:
    """Get yes/no input from user."""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()

    if not response:
        return default

    return response in ('y', 'yes')


def generate_random_alphabetic(length: int = 6) -> str:
    """Generate a random string of alphabetic characters."""
    return ''.join(random.choices(string.ascii_lowercase, k=length))


def find_website_config(project_dir: str) -> Optional[Dict[str, Any]]:
    """Find .ufazien.json config file in project directory."""
    config_path = Path(project_dir) / '.ufazien.json'
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None
    return None


def save_website_config(project_dir: str, config: Dict[str, Any]) -> None:
    """Save website configuration to .ufazien.json."""
    config_path = Path(project_dir) / '.ufazien.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    # Add to .gitignore if not present
    gitignore_path = Path(project_dir) / '.gitignore'
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            content = f.read()
        if '.ufazien.json' not in content:
            with open(gitignore_path, 'a') as f:
                f.write('\n.ufazien.json\n')


def should_exclude_file(file_path: Path, ufazienignore_path: Path) -> bool:
    """Check if a file should be excluded based on .ufazienignore."""
    if not ufazienignore_path.exists():
        return False

    with open(ufazienignore_path, 'r') as f:
        ignore_patterns = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

    file_str = str(file_path)
    for pattern in ignore_patterns:
        if pattern in file_str or file_str.endswith(pattern):
            return True
        if pattern.endswith('/') and file_str.startswith(pattern):
            return True

    return False


def create_zip(project_dir: str, output_path: Optional[str] = None) -> str:
    """Create a ZIP file of the project, excluding files in .ufazienignore."""
    project_path = Path(project_dir).resolve()
    ufazienignore_path = project_path / '.ufazienignore'

    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix='.zip')
        os.close(fd)

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not should_exclude_file(
                Path(root) / d, ufazienignore_path
            )]

            for file in files:
                file_path = Path(root) / file

                if should_exclude_file(file_path, ufazienignore_path):
                    continue

                if file_path.suffix == '.zip' and file_path.name == Path(output_path).name:
                    continue

                try:
                    arcname = file_path.relative_to(project_path)
                    zipf.write(file_path, arcname)
                except ValueError:
                    continue

    return output_path


def create_zip_from_folder(project_dir: str, folder_name: str, output_path: Optional[str] = None) -> str:
    """Create a ZIP file from a specific folder (e.g., dist, build)."""
    project_path = Path(project_dir).resolve()
    build_folder_path = project_path / folder_name

    if not build_folder_path.exists():
        raise Exception(f"Build folder '{folder_name}' not found. Please build your project first.")

    if not build_folder_path.is_dir():
        raise Exception(f"'{folder_name}' is not a directory.")

    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix='.zip')
        os.close(fd)

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(build_folder_path):
            for file in files:
                file_path = Path(root) / file
                try:
                    # Create relative path from build folder root
                    arcname = file_path.relative_to(build_folder_path)
                    zipf.write(file_path, arcname)
                except ValueError:
                    continue

    return output_path
    
def subdomain_sanitize(subdomain: str) -> str:
    name = subdomain.lower()

    name = re.sub(r'[^a-z0-9-]', '_', name)


    name = name.replace('-', '_')

    name = name.strip('_')

    name = re.sub(r'_+', '_', name)

    if len(name) > 63:
        hash_suffix = hashlib.sha1(name.encode()).hexdigest()[:8]
        name = name[:54] + "_" + hash_suffix

    return name
         

