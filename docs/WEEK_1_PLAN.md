# Week 1: Foundation Layer

## 🎯 Goal
Get the basic application structure working with project import/export.

## 📋 Day-by-Day Plan

### **Day 1: Basic Window**
- [ ] Get Flet running
- [ ] Create 4-panel layout
- [ ] Make panels resizable
- [ ] Add basic styling

### **Day 2: Project Structure**
- [ ] Define project format (JSON metadata)
- [ ] Create project class
- [ ] File system utilities
- [ ] Error handling

### **Day 3: Import System**
- [ ] Folder picker dialog
- [ ] HTML file detection
- [ ] CSS file detection
- [ ] Parse and store structure

### **Day 4: Display HTML**
- [ ] WebView or HTML renderer research
- [ ] Display imported HTML in canvas
- [ ] Handle CSS loading
- [ ] Basic error handling

### **Day 5: Save/Load**
- [ ] Save project state
- [ ] Load saved projects
- [ ] Recent projects list
- [ ] Auto-save timer

### **Day 6: Window Polish**
- [ ] Remember window size/position
- [ ] Keyboard shortcuts (Ctrl+O, Ctrl+S)
- [ ] Menu bar
- [ ] About dialog

### **Day 7: Testing**
- [ ] Import OC2 project
- [ ] Verify display
- [ ] Save and reload
- [ ] Fix any bugs

## 🛠️ Code to Write

### `src/core/project.py`
```python
class Project:
    def __init__(self, path=None):
        self.path = path
        self.name = ""
        self.files = {}
        self.metadata = {}
    
    def import_folder(self, folder_path):
        """Import HTML/CSS/JS from folder"""
        pass
    
    def save(self, path=None):
        """Save project state"""
        pass
    
    def load(self, path):
        """Load saved project"""
        pass
```

### `src/ui/layout.py`
```python
def create_resizable_panels(page):
    """Create the 4-panel layout with dividers"""
    pass
```

## ✅ Success Criteria
By end of Week 1:
1. Application launches with 4-panel layout
2. Can import a folder (like OC2)
3. Displays HTML in canvas area
4. Can save and reload the project
5. Window state persists between sessions

## 🚫 NOT This Week
- Editing functionality
- Drag and drop
- Component library
- Any complex features

Just get the foundation solid!