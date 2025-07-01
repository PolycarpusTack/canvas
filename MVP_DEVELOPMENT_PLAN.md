# Canvas MVP Development Plan

## 🎯 Fixed MVP Scope
Build ONLY what's shown in the mockup - a working visual editor for web projects.

## 🛠️ Technology Decision

### **Python + Flet** (Recommended)
- **Why**: Python you already know + Flutter UI = Modern, fast, lightweight
- **Size**: ~50MB vs Electron's 150MB+
- **Performance**: Native performance, smooth UI
- **Distribution**: Single executable possible

```python
# Example of how simple Flet is:
import flet as ft

def main(page: ft.Page):
    page.title = "Canvas Editor"
    page.add(ft.Text("Hello Canvas!"))

ft.app(target=main)
```

## 📋 Tiered Development Plan

### **Foundation Layer (Week 1)**

#### F1: Project Structure & Window
- [ ] Basic Flet application window
- [ ] 4-panel layout (sidebar, components, canvas, properties)
- [ ] Resizable panels
- [ ] Window state persistence (size, position)

#### F2: Project Management
- [ ] Create new project
- [ ] Import folder (HTML/CSS/JS)
- [ ] Save project state
- [ ] Load project

### **Layer 1: Core UI (Week 2)**

#### L1.1: Navigation Sidebar
- [ ] Icon buttons (Page Builder, Content, Analytics, Settings, Help)
- [ ] Active state
- [ ] Hover tooltips
- [ ] Fixed 80px width

#### L1.2: Canvas Header Bar
- [ ] Project name display
- [ ] Device switcher (Desktop/Tablet/Mobile)
- [ ] Action buttons (Grid, Undo, Redo, Preview, Save, Publish)
- [ ] Button states (hover, active, disabled)

### **Layer 2: Component System (Week 3)**

#### L2.1: Component Panel
- [ ] Search box
- [ ] Component categories (Layout, OC2 Components, Content)
- [ ] Component items with icons
- [ ] Drag initiation (visual feedback)
- [ ] Scrollable list

#### L2.2: Canvas Viewport
- [ ] HTML rendering area
- [ ] Load project HTML
- [ ] Device frame sizing (Desktop: 100%, Tablet: 768px, Mobile: 375px)
- [ ] Centered content with shadow

### **Layer 3: Selection & Editing (Week 4)**

#### L3.1: Element Selection
- [ ] Click to select element
- [ ] Selection outline (blue dashed)
- [ ] "Editing [Element]" indicator
- [ ] Clear selection on outside click

#### L3.2: Floating Toolbar
- [ ] Show on element selection
- [ ] Move Up/Down buttons
- [ ] Duplicate button
- [ ] Delete button
- [ ] Position above selected element

### **Layer 4: Properties Panel (Week 5)**

#### L4.1: Basic Properties
- [ ] Content/Style/Advanced tabs
- [ ] Text input fields
- [ ] Textarea for longer content
- [ ] Update preview on change

#### L4.2: Rich Text Editor
- [ ] Toolbar (Bold, Italic, Underline, Link, Reference)
- [ ] Editable content area
- [ ] Apply formatting to selection

#### L4.3: Color Picker
- [ ] Color preview box
- [ ] Color value input
- [ ] Basic color selection

### **Layer 5: Canvas Interactions (Week 6)**

#### L5.1: Drag & Drop
- [ ] Accept drops from component panel
- [ ] Drop zone indicators
- [ ] Insert component at drop location
- [ ] Update HTML structure

#### L5.2: Grid & Guides
- [ ] Toggle grid overlay
- [ ] 20px grid pattern
- [ ] Show/hide with button

### **Layer 6: Data Persistence (Week 7)**

#### L6.1: Save System
- [ ] Save project structure
- [ ] Save component positions
- [ ] Save property values
- [ ] Project metadata (name, last modified)

#### L6.2: Code Generation
- [ ] Export clean HTML
- [ ] Export CSS with changes
- [ ] Maintain code formatting
- [ ] Preview before export

#### L6.3: History
- [ ] Track last 10 actions
- [ ] Display in properties panel
- [ ] Timestamp each action
- [ ] Basic undo/redo implementation

### **Layer 7: MVP Polish (Week 8)**

#### L7.1: Error Handling
- [ ] Graceful import failures
- [ ] Save error recovery
- [ ] User notifications

#### L7.2: Performance
- [ ] Smooth drag animations
- [ ] Responsive property updates
- [ ] Efficient HTML rendering

#### L7.3: Final Testing
- [ ] Import OC2 project
- [ ] Make edits
- [ ] Export and verify
- [ ] Package as executable

## 📁 Project Structure

```
canvas/
├── src/
│   ├── main.py              # Application entry
│   ├── ui/
│   │   ├── sidebar.py       # Navigation sidebar
│   │   ├── components.py    # Component panel
│   │   ├── canvas.py        # Main canvas area
│   │   ├── properties.py    # Properties panel
│   │   └── toolbar.py       # Floating toolbar
│   ├── core/
│   │   ├── project.py       # Project management
│   │   ├── selection.py     # Selection system
│   │   ├── drag_drop.py     # Drag & drop logic
│   │   └── history.py       # Undo/redo system
│   ├── editors/
│   │   ├── text.py          # Text editing
│   │   ├── richtext.py      # Rich text editor
│   │   └── color.py         # Color picker
│   └── export/
│       ├── html.py          # HTML generation
│       └── css.py           # CSS generation
├── templates/               # Starter templates
│   └── blank/              # Minimal template
├── assets/                 # Icons, fonts
└── requirements.txt        # Python dependencies
```

## 🚫 NOT in MVP (See FUTURE_IDEAS.md)
- Authentication/users
- Cloud sync
- Plugin system
- Template marketplace
- API/webhooks
- Multi-language
- Collaboration features
- Advanced animations
- Database storage
- Component marketplace

## ✅ Definition of Done for MVP
1. Can import the OC2 project
2. Can select and edit text content
3. Can drag & drop new components
4. Can change basic styles (colors, fonts)
5. Can save and reload projects
6. Can export working HTML/CSS
7. Runs as local application
8. Basic undo/redo works

## 🎯 Success Criteria
- Import OC2 → Edit heading → Add component → Save → Export = Working site