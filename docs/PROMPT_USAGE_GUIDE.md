# Canvas Editor - Prompt Usage Guide

## 🎯 How to Use the Development Prompts

This guide helps you get the most out of the Claude prompts for building Canvas Editor.

## 📋 Before You Start Each Task

### 1. Set Your Context
Always start with:
```
I'm building the Canvas Editor, currently on [WEEK X, TASK Y].
Project location: C:\Projects\canvas
Current status: [what's already done]
```

### 2. Include Relevant Files
If you've already completed previous tasks:
```
Here's my current main.py: [paste code]
Here's my project.py: [paste code]
```

### 3. Paste the Full Prompt
Copy the ENTIRE prompt from CLAUDE_PROMPTS.md for your current task.

## 🚀 Example Session

### Starting Week 1, Task F1:
```
I'm starting the Canvas Editor project, Week 1, Task F1.
Project location: C:\Projects\canvas
Current status: Fresh project with basic main.py stub

[PASTE THE ENTIRE F1 PROMPT FROM CLAUDE_PROMPTS.md]

Please implement this completely with no placeholders. Show me the working 4-panel window.
```

### Moving to Task F2:
```
I've completed F1 - the 4-panel window is working perfectly.
Here's my current code structure:
[paste main.py]
[paste any other relevant files]

Now I'm moving to Week 1, Task F2.

[PASTE THE ENTIRE F2 PROMPT FROM CLAUDE_PROMPTS.md]

The window state persistence from F1 is working, so make sure the project management integrates properly.
```

## ✅ Quality Checks

### After Each Implementation, Verify:

1. **Run the Anti-Stub Check**:
```bash
cd /mnt/c/Projects/canvas
grep -r "TODO\|FIXME\|pass\|stub\|mock" src/ | grep -v test_
# Should return NOTHING
```

2. **Test the Feature**:
```bash
python src/main.py
# Actually test what was built
# For F1: Resize panels, close and reopen
# For F2: Import a real project, save it, reload it
```

3. **Check for Completeness**:
- Every button does something real
- No "coming soon" messages
- Error handling works (try to break it!)
- The feature is actually useful

## 🚫 Red Flags to Reject

If Claude gives you code with any of these, ask for a complete rewrite:

```python
# ❌ REJECT: Stub function
def save_project(self):
    pass  # TODO: implement saving

# ❌ REJECT: Mock return
def import_folder(self, path):
    print(f"Importing {path}")
    return {"status": "success"}  # stub

# ❌ REJECT: Placeholder handler
def on_button_click(self, e):
    print("Button clicked!")  # Will implement later

# ❌ REJECT: Hardcoded test data
def get_components(self):
    return [
        {"name": "Component 1"},  # TODO: Load real components
        {"name": "Component 2"},
    ]
```

## 📈 Progressive Development

### Week 1: Foundation
Focus: Get the shell working
- Don't worry about drag & drop yet
- Just get import/save working solidly

### Week 2: Core UI  
Focus: Make it look right
- All panels should have real content
- Navigation should actually navigate

### Week 3-4: Selection
Focus: Make things clickable
- Real element selection
- Actual property editing

### Week 5-6: Interactions
Focus: Core editing features
- Real drag and drop
- Working grid system

### Week 7-8: Polish
Focus: Production ready
- Comprehensive error handling
- Professional packaging

## 💡 Pro Tips

### 1. Test With Real Data
Always test with the OC2 project:
```
Import: C:\Projects\OC2
Edit: Change the heading text
Save: As a Canvas project
Export: Verify the HTML works
```

### 2. Break Down Problems
If a task seems too big:
```
"This seems complex. Let's break F2 into steps:
1. First, show me just the Project class
2. Then implement import_folder
3. Then add save/load
4. Finally add auto-save"
```

### 3. Demand Working Demos
```
"Before we continue, show me:
1. The exact commands to run this
2. What I should see happening
3. How to verify it worked"
```

### 4. Use Incremental Validation
```
"After implementing the Project class, let's test it:
- Create a project
- Import a folder
- Print the project structure
Then we'll add save/load functionality"
```

## 🎮 Keyboard Shortcuts to Request

As you build, ask for these standard shortcuts:
- Ctrl+N: New project
- Ctrl+O: Open project  
- Ctrl+S: Save project
- Ctrl+Z/Y: Undo/Redo
- Ctrl+D: Duplicate element
- Delete: Delete element
- Ctrl+G: Toggle grid

## 📝 Documentation to Request

For each major component, ask for:
```
"Also create a docstring that explains:
1. What this component does
2. How to extend it
3. Any limitations
4. Example usage"
```

## 🐛 When Things Go Wrong

If something isn't working:
```
"The [feature] isn't working properly. Here's what happens:
1. I click [button]
2. Expected: [what should happen]
3. Actual: [what actually happens]
4. Error message: [any errors]

Please debug and fix this issue completely."
```

## 🎯 Final Checklist for Each Task

Before moving to the next task:
- [ ] Feature works as described
- [ ] No TODO/FIXME/stub in code
- [ ] Errors are handled gracefully  
- [ ] I can use it for real work
- [ ] Code is documented
- [ ] Tests pass (if applicable)

## 📚 Remember

The prompts in CLAUDE_PROMPTS.md are designed to get complete, working implementations. Don't settle for less! Each completed task should bring you closer to a professional visual editor you can actually use.

Good luck, and happy building! 🚀