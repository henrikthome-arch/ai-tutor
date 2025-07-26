"""
Simple prompt file loader for AI services
Loads prompt templates from markdown files
"""

import os
from pathlib import Path


def load_prompt_template(filename: str) -> str:
    """
    Load a prompt template from a markdown file
    
    Args:
        filename: Name of the prompt file (e.g., 'post_session_update.md')
        
    Returns:
        Content of the prompt file as a string
    """
    # Get the prompts directory relative to this file
    current_dir = Path(__file__).parent
    prompts_dir = current_dir / "prompts"
    
    # Construct full file path
    file_path = prompts_dir / filename
    
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        raise RuntimeError(f"Error reading prompt template {filename}: {str(e)}")


def get_available_prompts():
    """
    Get list of available prompt template files
    
    Returns:
        List of available prompt filenames
    """
    current_dir = Path(__file__).parent
    prompts_dir = current_dir / "prompts"
    
    if not prompts_dir.exists():
        return []
    
    prompt_files = []
    for file_path in prompts_dir.glob("*.md"):
        prompt_files.append(file_path.name)
    
    return sorted(prompt_files)