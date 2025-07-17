# AI Prompt Management Guide - File-Based System

## 📍 **Where All Prompts Are Stored (Updated)**

### **New Organization: Individual Files in [`ai_poc/prompts/`](ai_poc/prompts/)**

**✅ Much Better Approach:** Each prompt is now in its own markdown file for easy maintenance and version control.

## 🗂️ **Current Prompt File Structure**

```
ai_poc/prompts/
├── README.md                    # Overview and documentation
├── session_analysis.md          # Main comprehensive analysis
├── quick_assessment.md          # Rapid session evaluation  
├── math_analysis.md             # Mathematics-specific analysis
├── reading_analysis.md          # Reading/Language arts analysis
└── progress_tracking.md         # Multi-session comparison
```

## 📝 **Available Educational Analysis Prompts**

| File | Prompt Name | Description | Use Case |
|------|-------------|-------------|----------|
| [`session_analysis.md`](ai_poc/prompts/session_analysis.md) | Educational Session Analysis | Comprehensive 4-category analysis | Most tutoring sessions |
| [`quick_assessment.md`](ai_poc/prompts/quick_assessment.md) | Quick Session Assessment | Rapid 3-point analysis | Short sessions, real-time feedback |
| [`math_analysis.md`](ai_poc/prompts/math_analysis.md) | Mathematics Session Analysis | 6-category math-focused analysis | Math tutoring sessions |
| [`reading_analysis.md`](ai_poc/prompts/reading_analysis.md) | Reading & Language Arts Analysis | 6-category literacy analysis | Reading/writing sessions |
| [`progress_tracking.md`](ai_poc/prompts/progress_tracking.md) | Progress Tracking Analysis | Multi-session comparison | Longitudinal analysis |

## ✅ **Benefits of File-Based Organization**

### **1. Easy Editing**
- **Direct editing**: Open any `.md` file in VS Code or any text editor
- **Clear structure**: Each prompt has metadata, system prompt, user template, and parameters
- **Readable format**: Markdown is human-readable and well-formatted

### **2. Version Control Friendly**
- **Individual diffs**: Changes to one prompt don't affect others
- **Clear history**: See exactly what changed in each prompt over time
- **Team collaboration**: Multiple people can edit different prompts simultaneously

### **3. Organized Documentation**
- **Self-documenting**: Each file contains its own description and use case
- **Parameter documentation**: Required parameters clearly listed
- **Examples included**: Templates show exactly how to use each prompt

## 🛠️ **How to Review and Update Prompts**

### **Method 1: Direct File Editing (Recommended)**
```bash
# Edit any prompt directly
code ai_poc/prompts/session_analysis.md

# Edit mathematics-specific prompt
code ai_poc/prompts/math_analysis.md

# View all prompts at once
code ai_poc/prompts/
```

### **Method 2: File-Based Prompt Viewer**
```bash
# Test the new file-based system
python -c "
from ai_poc.prompts_file_loader import file_prompt_manager
print('Available prompts:', file_prompt_manager.get_available_prompts())
"
```

### **Method 3: Interactive Management**
```bash
# Use the original prompt viewer (still works)
python prompt_viewer.py
```

### **Method 4: Admin Dashboard**
The prompts integrate with the admin dashboard at `http://localhost:5000/admin/ai-analysis`

## 📋 **Prompt File Format**

Each prompt file follows this standard markdown structure:

```markdown
# Prompt Name

**Version:** 1.0  
**Description:** Brief description of what this prompt does  
**Use Case:** When and why to use this prompt  

## System Prompt

Instructions for AI behavior, analysis framework, and response guidelines.

## User Prompt Template

The actual prompt template with {parameter} placeholders for dynamic content.

**STUDENT CONTEXT:**
- Name: {student_name}
- Age: {student_age}
- etc.

**SESSION TRANSCRIPT:**
{transcript}

[Analysis instructions with specific sections to complete]

## Required Parameters

- `student_name`: Student's name
- `student_age`: Student's age
- `transcript`: Session transcript content
- etc.
```

## 🔧 **Updating Existing Prompts**

### **To Update a Prompt:**

1. **Open the file**: `code ai_poc/prompts/session_analysis.md`
2. **Edit the content**:
   - **System Prompt**: Modify AI behavior instructions
   - **User Prompt Template**: Update the actual prompt text
   - **Parameters**: Add/remove required parameters
   - **Metadata**: Update version, description, use case
3. **Save the file**: Changes are automatically loaded
4. **Test changes**: Use the prompt viewer or run analysis

### **Example Update:**
```markdown
# Educational Session Analysis Prompt

**Version:** 1.1  ← Updated version
**Description:** Enhanced analysis with emotional intelligence focus  ← Updated description

## System Prompt

You are an expert educational analyst with expertise in both learning assessment and emotional intelligence...  ← Enhanced instructions

## User Prompt Template

Please analyze this tutoring session with focus on both cognitive and emotional development...  ← Updated prompt

## Required Parameters

- `student_name`: Student's name
- `emotional_state`: Student's emotional context  ← New parameter
```

## ➕ **Adding New Prompts**

### **Create a New Prompt File:**

1. **Create file**: `ai_poc/prompts/science_analysis.md`
2. **Follow format**:
```markdown
# Science Session Analysis Prompt

**Version:** 1.0
**Description:** Specialized analysis for science tutoring sessions
**Use Case:** STEM education and scientific thinking assessment

## System Prompt

You are a science education specialist...

## User Prompt Template

Analyze this science tutoring session...

## Required Parameters

- `student_name`: Student's name
- `science_topic`: Specific science subject
- `transcript`: Session transcript
```

3. **Update loader**: Add to `ai_poc/prompts_file_loader.py`
4. **Update documentation**: Add to the table above

## 🧪 **Testing Prompts**

### **Quick Test:**
```bash
python -c "
from ai_poc.prompts_file_loader import file_prompt_manager

# Test loading
prompts = file_prompt_manager.get_available_prompts()
print(f'Loaded {len(prompts)} prompts')

# Test formatting
formatted = file_prompt_manager.format_prompt('session_analysis', 
    student_name='Test Student',
    student_age='10',
    student_grade='5',
    subject_focus='Math',
    learning_style='Visual',
    primary_interests='Science',
    motivational_triggers='Games',
    transcript='Sample transcript...'
)
print('✅ Prompt formatting works')
"
```

### **Full System Test:**
```bash
# Test with the AI analysis system
python -c "
from ai_poc.session_processor import session_processor
# System will automatically use the file-based prompts
"
```

## 🔄 **Integration with AI System**

### **Current Integration:**
- **File Loader**: [`ai_poc/prompts_file_loader.py`](ai_poc/prompts_file_loader.py)
- **AI Providers**: [`ai_poc/providers.py`](ai_poc/providers.py) (uses prompts for real API calls)
- **Session Processor**: [`ai_poc/session_processor.py`](ai_poc/session_processor.py)
- **Admin Dashboard**: `http://localhost:5000/admin/ai-analysis`

### **Switching to File-Based Prompts:**
The system can use either the old hardcoded prompts or the new file-based ones. To switch:

```python
# In ai_poc/providers.py - replace hardcoded with file-based
from .prompts_file_loader import file_prompt_manager

# Format prompt from file
formatted_prompt = file_prompt_manager.format_prompt('session_analysis', **context)
system_prompt = formatted_prompt['system_prompt']
user_prompt = formatted_prompt['user_prompt']
```

## 📊 **File Management**

### **Current Status:**
- ✅ **5 prompt files** created with comprehensive analysis types
- ✅ **File-based loader** implemented and tested
- ✅ **Documentation** complete with usage examples
- ✅ **Version control ready** with individual file tracking

### **Backup and Sync:**
- Each prompt file is individually version controlled
- Easy to backup, sync, and collaborate on
- No conflicts when multiple people edit different prompts
- Clear history of what changed in each prompt

## 🎯 **Quick Access Commands**

```bash
# View all prompt files
ls ai_poc/prompts/

# Edit main analysis prompt
code ai_poc/prompts/session_analysis.md

# Edit math-specific prompt  
code ai_poc/prompts/math_analysis.md

# Test file-based prompt system
python -c "from ai_poc.prompts_file_loader import file_prompt_manager; print(file_prompt_manager.get_available_prompts())"

# Open prompts directory
code ai_poc/prompts/

# View prompt documentation
code ai_poc/prompts/README.md
```

## 📁 **Final File Organization**

```
ai_poc/
├── prompts/                     # ← ALL PROMPTS HERE (NEW)
│   ├── README.md               # Overview and documentation
│   ├── session_analysis.md     # Main comprehensive analysis
│   ├── quick_assessment.md     # Rapid evaluation
│   ├── math_analysis.md        # Mathematics-specific
│   ├── reading_analysis.md     # Reading/Language arts
│   └── progress_tracking.md    # Multi-session comparison
├── prompts_file_loader.py      # ← FILE-BASED LOADER (NEW)
├── prompts.py                  # Old centralized system (backup)
├── providers.py               # AI provider implementations  
├── config.py                  # Configuration management
├── validator.py               # Quality validation
└── session_processor.py       # Main orchestration

prompt_viewer.py               # ← PROMPT REVIEW TOOL
```

---

**🎯 Summary: All AI analysis prompts are now organized as individual markdown files in [`ai_poc/prompts/`](ai_poc/prompts/) for easy editing, version control, and maintenance.**

**✅ This is much better than having everything in one file!**