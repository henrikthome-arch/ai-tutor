"""
File-based prompt management system
Loads prompts from individual markdown files for better organization
"""

import os
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class PromptTemplate:
    """Template for AI prompts with metadata"""
    name: str
    version: str
    description: str
    use_case: str
    system_prompt: str
    user_prompt_template: str
    parameters: Dict[str, str]
    file_path: str
    created_date: datetime
    last_updated: datetime

class FileBasedPromptManager:
    """Manages prompts loaded from individual markdown files with call-type support"""
    
    def __init__(self, prompts_dir: str = None):
        if prompts_dir is None:
            # Default to prompts directory relative to this file
            current_dir = Path(__file__).parent
            self.prompts_dir = current_dir / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)
        
        self.prompts = {}
        self.call_type_prompts = {
            'introductory': ['introductory_analysis'],
            'tutoring': ['session_analysis', 'math_analysis', 'reading_analysis', 'quick_assessment', 'progress_tracking']
        }
        self._load_all_prompts()
    
    def _load_all_prompts(self):
        """Load all prompts from markdown files"""
        if not self.prompts_dir.exists():
            print(f"Warning: Prompts directory {self.prompts_dir} does not exist")
            return
        
        # Map of file names to prompt keys
        prompt_files = {
            'introductory_analysis.md': 'introductory_analysis',
            'session_analysis.md': 'session_analysis',
            'quick_assessment.md': 'quick_assessment',
            'math_analysis.md': 'math_analysis',
            'reading_analysis.md': 'reading_analysis',
            'progress_tracking.md': 'progress_tracking'
        }
        
        for filename, prompt_key in prompt_files.items():
            file_path = self.prompts_dir / filename
            if file_path.exists():
                try:
                    prompt = self._load_prompt_from_file(file_path, prompt_key)
                    if prompt:
                        self.prompts[prompt_key] = prompt
                        print(f"Loaded prompt: {prompt_key} from {filename}")
                except Exception as e:
                    print(f"Error loading prompt from {filename}: {e}")
            else:
                print(f"Prompt file not found: {filename}")
    
    def _load_prompt_from_file(self, file_path: Path, prompt_key: str) -> Optional[PromptTemplate]:
        """Load a single prompt from a markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse markdown content
            lines = content.split('\n')
            
            # Extract title (first line starting with #)
            name = "Unknown"
            for line in lines:
                if line.startswith('# '):
                    name = line[2:].strip()
                    break
            
            # Extract metadata
            version = self._extract_metadata(content, 'Version')
            description = self._extract_metadata(content, 'Description')
            use_case = self._extract_metadata(content, 'Use Case')
            
            # Extract system prompt
            system_prompt = self._extract_section(content, '## System Prompt')
            
            # Extract user prompt template
            user_prompt_template = self._extract_section(content, '## User Prompt Template')
            
            # Extract parameters
            parameters = self._extract_parameters(content)
            
            # File modification time as last updated
            stat = file_path.stat()
            last_updated = datetime.fromtimestamp(stat.st_mtime)
            created_date = datetime.fromtimestamp(stat.st_ctime)
            
            return PromptTemplate(
                name=name,
                version=version or "1.0",
                description=description or "No description",
                use_case=use_case or "General use",
                system_prompt=system_prompt or "",
                user_prompt_template=user_prompt_template or "",
                parameters=parameters,
                file_path=str(file_path),
                created_date=created_date,
                last_updated=last_updated
            )
            
        except Exception as e:
            print(f"Error parsing prompt file {file_path}: {e}")
            return None
    
    def _extract_metadata(self, content: str, field: str) -> Optional[str]:
        """Extract metadata field from markdown"""
        pattern = rf'\*\*{field}:\*\*\s*(.+?)(?:\n|$)'
        match = re.search(pattern, content)
        return match.group(1).strip() if match else None
    
    def _extract_section(self, content: str, header: str) -> str:
        """Extract content between markdown headers"""
        lines = content.split('\n')
        in_section = False
        section_lines = []
        
        for line in lines:
            if line.strip() == header:
                in_section = True
                continue
            elif in_section and line.startswith('## '):
                # Hit next section, stop
                break
            elif in_section:
                section_lines.append(line)
        
        return '\n'.join(section_lines).strip()
    
    def _extract_parameters(self, content: str) -> Dict[str, str]:
        """Extract parameters from the Required Parameters section"""
        parameters = {}
        
        # Find the Required Parameters section
        param_section = self._extract_section(content, '## Required Parameters')
        
        # Parse parameter lines (format: - `param_name`: Description)
        for line in param_section.split('\n'):
            line = line.strip()
            if line.startswith('- `') and ':' in line:
                # Extract parameter name and description
                match = re.match(r'- `([^`]+)`:\s*(.+)', line)
                if match:
                    param_name = match.group(1)
                    param_desc = match.group(2)
                    parameters[param_name] = param_desc
        
        return parameters
    
    def get_prompt(self, prompt_name: str) -> Optional[PromptTemplate]:
        """Get a specific prompt template"""
        return self.prompts.get(prompt_name)
    
    def get_available_prompts(self) -> Dict[str, str]:
        """Get list of available prompts with descriptions"""
        return {
            name: prompt.description 
            for name, prompt in self.prompts.items()
        }
    
    def format_prompt(self, prompt_name: str, **kwargs) -> Optional[Dict[str, str]]:
        """Format a prompt with provided parameters"""
        prompt = self.get_prompt(prompt_name)
        if not prompt:
            return None
        
        try:
            # Provide default values for optional parameters
            safe_kwargs = {
                'transcript': kwargs.get('transcript', ''),
                'phone_number': kwargs.get('phone_number', 'Unknown'),
                'call_duration': kwargs.get('call_duration', 'Unknown'),
                'call_datetime': kwargs.get('call_datetime', 'Unknown'),
                'student_name': kwargs.get('student_name', 'Student'),
                'student_age': kwargs.get('student_age', 'Unknown'),
                'student_grade': kwargs.get('student_grade', 'Unknown'),
                'subject_focus': kwargs.get('subject_focus', 'General'),
                'learning_style': kwargs.get('learning_style', 'Mixed'),
                'primary_interests': kwargs.get('primary_interests', 'Various'),
                'motivational_triggers': kwargs.get('motivational_triggers', 'Achievement'),
                **kwargs  # Override with any provided values
            }
            
            formatted_user_prompt = prompt.user_prompt_template.format(**safe_kwargs)
            return {
                'system_prompt': prompt.system_prompt,
                'user_prompt': formatted_user_prompt,
                'name': prompt.name,
                'version': prompt.version,
                'file_path': prompt.file_path
            }
        except KeyError as e:
            # Get the actual missing parameter name
            missing_param = str(e).strip("'\"")
            raise ValueError(f"Missing required parameter for prompt '{prompt_name}': '{missing_param}'")
        except Exception as e:
            raise ValueError(f"Error formatting prompt '{prompt_name}': {str(e)}")
    
    def reload_prompts(self):
        """Reload all prompts from files (useful for development)"""
        self.prompts.clear()
        self._load_all_prompts()
    
    def get_prompt_info(self, prompt_name: str) -> Dict[str, Any]:
        """Get detailed information about a prompt"""
        prompt = self.get_prompt(prompt_name)
        if not prompt:
            return {}
        
        return {
            'name': prompt.name,
            'version': prompt.version,
            'description': prompt.description,
            'use_case': prompt.use_case,
            'file_path': prompt.file_path,
            'parameters': prompt.parameters,
            'created_date': prompt.created_date.isoformat(),
            'last_updated': prompt.last_updated.isoformat(),
            'system_prompt_length': len(prompt.system_prompt),
            'user_prompt_length': len(prompt.user_prompt_template)
        }
    
    def list_prompt_files(self) -> Dict[str, str]:
        """List all prompt files and their status"""
        files = {}
        for prompt_name, prompt in self.prompts.items():
            files[prompt_name] = prompt.file_path
        return files
    
    def get_prompts_by_call_type(self, call_type: str) -> Dict[str, PromptTemplate]:
        """Get all prompts for a specific call type"""
        if call_type not in self.call_type_prompts:
            return {}
        
        relevant_prompts = {}
        for prompt_name in self.call_type_prompts[call_type]:
            if prompt_name in self.prompts:
                relevant_prompts[prompt_name] = self.prompts[prompt_name]
        
        return relevant_prompts
    
    def get_default_prompt_for_call_type(self, call_type: str) -> Optional[str]:
        """Get the default prompt name for a specific call type"""
        defaults = {
            'introductory': 'introductory_analysis',
            'tutoring': 'session_analysis'
        }
        return defaults.get(call_type)
    
    def format_conditional_prompt(self, call_type: str, subject: str = None, **kwargs) -> Optional[Dict[str, str]]:
        """Format a prompt based on call type and optional subject specialization"""
        # Determine the best prompt for this call type and subject
        prompt_name = self._select_best_prompt(call_type, subject)
        
        if not prompt_name:
            return None
        
        return self.format_prompt(prompt_name, **kwargs)
    
    def _select_best_prompt(self, call_type: str, subject: str = None) -> Optional[str]:
        """Select the best prompt based on call type and subject"""
        if call_type == 'introductory':
            return 'introductory_analysis'
        elif call_type == 'tutoring':
            # For tutoring sessions, consider subject specialization
            if subject and subject.lower() in ['math', 'mathematics']:
                return 'math_analysis'
            elif subject and subject.lower() in ['reading', 'literacy', 'english']:
                return 'reading_analysis'
            else:
                # Default to general session analysis
                return 'session_analysis'
        
        return None
    
    def get_call_type_info(self) -> Dict[str, Any]:
        """Get information about available call types and their prompts"""
        info = {}
        for call_type, prompt_names in self.call_type_prompts.items():
            available_prompts = [name for name in prompt_names if name in self.prompts]
            info[call_type] = {
                'available_prompts': available_prompts,
                'default_prompt': self.get_default_prompt_for_call_type(call_type),
                'count': len(available_prompts)
            }
        return info
    
    def validate_conditional_setup(self) -> Dict[str, Any]:
        """Validate that all required prompts for conditional system are available"""
        validation = {
            'valid': True,
            'missing_prompts': [],
            'available_prompts': list(self.prompts.keys()),
            'call_type_coverage': {}
        }
        
        required_prompts = ['introductory_analysis', 'session_analysis']
        
        for prompt in required_prompts:
            if prompt not in self.prompts:
                validation['missing_prompts'].append(prompt)
                validation['valid'] = False
        
        # Check coverage for each call type
        for call_type, prompt_names in self.call_type_prompts.items():
            available = [name for name in prompt_names if name in self.prompts]
            validation['call_type_coverage'][call_type] = {
                'required': prompt_names,
                'available': available,
                'coverage_percent': (len(available) / len(prompt_names)) * 100 if prompt_names else 100
            }
        
        return validation

# Global file-based prompt manager instance
file_prompt_manager = FileBasedPromptManager()