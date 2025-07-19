# AI Educational Analysis Prompts

This directory contains all AI prompts for educational session analysis, organized as separate files for easy maintenance and version control.

## Available Prompts

| File | Prompt Type | Description | Use Case |
|------|-------------|-------------|----------|
| [`session_analysis.md`](session_analysis.md) | Main Analysis | Comprehensive 4-category analysis | Most tutoring sessions |
| [`quick_assessment.md`](quick_assessment.md) | Quick Assessment | Rapid 3-point analysis | Short sessions, real-time feedback |
| [`math_analysis.md`](math_analysis.md) | Mathematics | 6-category math-focused analysis | Math tutoring sessions |
| [`reading_analysis.md`](reading_analysis.md) | Reading/Language Arts | 6-category literacy analysis | Reading/writing sessions |
| [`progress_tracking.md`](progress_tracking.md) | Progress Tracking | Multi-session comparison | Longitudinal analysis |

## Prompt File Format

Each prompt file follows this markdown structure:

```markdown
# Prompt Name

**Version:** 1.0  
**Description:** Brief description  
**Use Case:** When to use this prompt  

## System Prompt

Instructions for AI behavior and analysis framework.

## User Prompt Template

The actual prompt template with {parameter} placeholders.

## Required Parameters

- `parameter_name`: Description of what this parameter contains
```

## How to Edit Prompts

1. **Edit directly**: Open any `.md` file and modify the System Prompt or User Prompt Template
2. **Version control**: Each prompt has a version number for tracking changes
3. **Test changes**: Use the prompt viewer to test updated prompts
4. **Documentation**: Update descriptions and use cases as needed

## Adding New Prompts

1. Create a new `.md` file following the format above
2. Add it to the table in this README
3. Update the prompt loader to include the new prompt
4. Test with the prompt management tools

## Integration

These prompts are loaded by [`ai/prompts.py`](../prompts.py) and used throughout the AI analysis system.