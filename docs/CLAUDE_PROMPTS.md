# Canvas Editor - Claude Development Prompts

## How to Use These Prompts

Each prompt below corresponds to a task in the MVP_DEVELOPMENT_PLAN.md. Copy the entire prompt for your current task and paste it into Claude. These prompts are designed to get COMPLETE, WORKING implementations with zero stubs or placeholders.

---

# WEEK 1: FOUNDATION LAYER

## F1: Project Structure & Window

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Implement the Canvas Editor basic Flet application window with complete, production-ready 4-panel layout (sidebar 80px, components 280px, canvas flexible, properties 320px) that maintains state between sessions. Every panel must be fully functional with proper resize handling and no placeholder content.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- Study Flet's layout system and ResponsiveRow capabilities
- Understand Flet's state persistence mechanisms
- Research panel resize handling in Flet applications
- Map out event flow for panel interactions

**B. RESEARCH ROOT CAUSES:**
- Common issues with Flet layout persistence
- Panel resize performance considerations
- Cross-platform window state handling

**C. DEPTH CHECK - For EACH component explain:**
- Exact Flet container hierarchy for 4-panel layout
- State persistence using Flet's client storage
- Resize handle implementation approach
- Panel minimum/maximum size constraints
- Event handling for resize operations

**D. ENVIRONMENT CONTEXT:**
- Python 3.8+ with Flet 0.25.0+
- Target platforms: Windows, macOS, Linux
- Canvas project structure at C:\Projects\canvas
- Must integrate with existing main.py structure

**E. DELIVERABLE REQUIREMENTS:**
Complete implementation that:
1. Creates 4-panel layout matching mockup exactly
2. Saves window size/position on close
3. Restores window state on launch
4. Handles panel resizing smoothly
5. Shows real content in each panel (no placeholders)
6. Includes proper error handling for state corruption

**VERIFICATION COMMANDS:**
```bash
cd /mnt/c/Projects/canvas
python src/main.py
# Window should appear with 4 panels
# Resize window and panels
# Close and reopen - state should persist
grep -r "TODO\|FIXME\|pass\|stub" src/ | grep -v test_
```

**SUCCESS METRIC:**
- Application launches with exact layout from mockup
- Panel sizes persist between sessions
- Smooth resize operations at 60fps
- Zero placeholder content or stub functions

---

## F2: Project Management

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Implement complete project management system for Canvas Editor that handles create new project, import folder (HTML/CSS/JS), save project state, and load project with full error handling and no mock implementations.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- File system operations in Python for cross-platform compatibility
- Project metadata structure requirements
- HTML/CSS/JS file detection patterns
- State serialization best practices

**B. RESEARCH ROOT CAUSES:**
- Common project corruption scenarios
- File permission issues across platforms
- Large project performance considerations

**C. DEPTH CHECK - For EACH component explain:**
- Project class structure with all properties
- Import algorithm for detecting web files
- JSON schema for project metadata
- File watching strategy for external changes
- Error recovery for corrupted projects

**D. ENVIRONMENT CONTEXT:**
- Must handle projects up to 1000 files
- Support nested folder structures
- Preserve file encoding (UTF-8, etc.)
- Work with symlinks and junctions

**E. DELIVERABLE REQUIREMENTS:**
Complete implementation with:
1. Project class with full CRUD operations
2. Folder import with progress indication
3. Robust save/load with corruption detection
4. Recent projects list (last 10)
5. Auto-save every 5 minutes
6. Project validation on load

**VERIFICATION COMMANDS:**
```bash
# Test with OC2 project
python src/main.py
# Import /mnt/c/Projects/OC2
# Verify all files detected
# Save project
# Corrupt save file slightly
# Attempt reload - should handle gracefully
```

**SUCCESS METRIC:**
- Import OC2 project completely
- Save creates valid project file
- Load recovers from minor corruption
- Auto-save works without blocking UI
- Recent projects menu functional

---

# WEEK 2: CORE UI

## L1.1: Navigation Sidebar

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Implement the complete navigation sidebar (80px wide) with icon buttons for Page Builder, Content, Analytics, Settings, Help with active states, hover tooltips, proper styling, and navigation functionality - no placeholder handlers.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- Flet Icon button best practices
- Tooltip implementation in Flet
- Navigation state management patterns
- Icon loading and rendering optimization

**B. RESEARCH ROOT CAUSES:**
- Common navigation state sync issues
- Tooltip positioning edge cases
- Icon rendering performance impacts

**C. DEPTH CHECK - For EACH component explain:**
- Navigation state management approach
- Active state visual feedback implementation
- Tooltip show/hide timing logic
- Icon lazy loading strategy
- Keyboard navigation support

**D. ENVIRONMENT CONTEXT:**
- Must support keyboard navigation (Tab, Enter)
- Tooltips must not overflow window
- Icons from Material Design set
- State persists across app restarts

**E. DELIVERABLE REQUIREMENTS:**
Complete sidebar with:
1. All 5 navigation buttons functional
2. Active state with visual feedback
3. Hover states with 200ms delay
4. Tooltips positioned correctly
5. Keyboard accessible
6. Navigation actually changes main content

**SUCCESS METRIC:**
- Each button navigates to different view
- Active state clearly visible
- Tooltips appear/disappear smoothly
- Keyboard navigation works
- No console errors on rapid clicking

---

## L1.2: Canvas Header Bar

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Implement the complete canvas header bar with project name display, device switcher (Desktop/Tablet/Mobile), and all action buttons (Grid, Undo, Redo, Preview, Save, Publish) with real functionality, not stub handlers.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- Device preview size calculations
- Undo/Redo stack implementation patterns
- Grid overlay rendering approaches
- Save operation progress indication

**B. RESEARCH ROOT CAUSES:**
- Device switching performance issues
- Undo/redo memory management
- Grid rendering impact on canvas

**C. DEPTH CHECK - For EACH component explain:**
- Device frame size calculations (Desktop: 100%, Tablet: 768px, Mobile: 375px)
- Undo/redo stack data structure
- Grid overlay SVG generation
- Save operation queue management
- Preview window implementation

**D. DELIVERABLE REQUIREMENTS:**
Complete header with:
1. Editable project name that saves
2. Device switcher changes canvas size
3. Grid toggle shows/hides overlay
4. Undo/redo with 50 action history
5. Save with progress indication
6. Preview opens new window

**SUCCESS METRIC:**
- All buttons have real functionality
- Device switching animates smoothly
- Grid overlay aligns properly
- Undo/redo works for all operations
- Save completes with confirmation

---

# WEEK 3: COMPONENT SYSTEM

## L2.1: Component Panel

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Implement the complete component panel (280px) with search box, categorized components (Layout, OC2 Components, Content), drag initiation with visual feedback, and scrollable list - all components must be real and draggable.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- Drag and drop initiation in Flet
- Component metadata structure
- Search algorithm requirements
- Scroll performance with many components

**B. RESEARCH ROOT CAUSES:**
- Drag preview rendering challenges
- Search performance with large lists
- Category organization patterns

**C. DEPTH CHECK - For EACH component explain:**
- Component registry data structure
- Drag data transfer format
- Search indexing approach
- Virtual scrolling implementation
- Component preview generation

**D. DELIVERABLE REQUIREMENTS:**
Complete panel with:
1. Real components (not placeholders)
2. Instant search filtering
3. Drag preview follows cursor
4. Category expand/collapse
5. Component descriptions
6. Smooth scrolling

**SUCCESS METRIC:**
- Search filters in <50ms
- Drag preview appears instantly
- All components have real templates
- Categories remember state
- No lag with 50+ components

---

## L2.2: Canvas Viewport

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Implement the canvas viewport with HTML rendering area, project file loading, device frame sizing (Desktop/Tablet/Mobile), centered content with shadow, and real HTML/CSS rendering - not a placeholder.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- HTML rendering options in Flet (WebView vs custom)
- CSS injection techniques
- Device frame rendering approaches
- Shadow and styling methods

**B. RESEARCH ROOT CAUSES:**
- Cross-platform HTML rendering differences
- CSS isolation challenges
- Performance with complex HTML

**C. DEPTH CHECK - For EACH component explain:**
- HTML rendering engine choice
- CSS sandboxing approach
- Device frame implementation
- Content scaling algorithm
- Shadow rendering technique

**D. DELIVERABLE REQUIREMENTS:**
Complete viewport with:
1. Renders actual HTML/CSS
2. Device frames visually accurate
3. Content scales properly
4. Shadows match mockup
5. Handles malformed HTML
6. Updates in real-time

**SUCCESS METRIC:**
- OC2 project renders correctly
- Device switching maintains aspect ratio
- No CSS leakage to main app
- 60fps during interactions
- Handles 100KB+ HTML files

---

# WEEK 4: SELECTION & EDITING

## L3.1: Element Selection

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Implement complete element selection system with click to select, selection outline (blue dashed), "Editing [Element]" indicator, and clear selection - must work with real HTML elements in canvas.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- HTML element detection in rendered view
- Selection overlay positioning
- Element boundary calculation
- Click event propagation

**B. RESEARCH ROOT CAUSES:**
- Iframe/WebView click detection issues
- Overlay positioning with scrolling
- Selection persistence challenges

**C. DEPTH CHECK - For EACH component explain:**
- Element detection algorithm
- Overlay rendering approach
- Selection state management
- Coordinate transformation logic
- Multi-select considerations

**D. DELIVERABLE REQUIREMENTS:**
Complete selection with:
1. Click any element to select
2. Blue dashed outline appears
3. Shows element type indicator
4. Handles nested elements
5. Clear selection on outside click
6. Selection survives canvas updates

**SUCCESS METRIC:**
- Can select any element in OC2
- Outline positions perfectly
- No selection lag
- Works with transformed elements
- Indicator updates correctly

---

## L3.2: Floating Toolbar

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Implement the floating toolbar that appears above selected elements with Move Up/Down, Duplicate, Delete buttons - all with real functionality that modifies the actual HTML structure.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- DOM manipulation strategies
- Toolbar positioning algorithms
- HTML structure preservation
- Operation history tracking

**B. RESEARCH ROOT CAUSES:**
- Toolbar overlap issues
- DOM mutation performance
- Structure corruption risks

**C. DEPTH CHECK - For EACH component explain:**
- Move up/down sibling detection
- Duplicate with unique IDs
- Delete with child handling
- Position calculation with scroll
- Animation approach

**D. DELIVERABLE REQUIREMENTS:**
Complete toolbar with:
1. Appears above selection
2. Move operations work correctly
3. Duplicate creates unique copy
4. Delete removes from DOM
5. All operations undoable
6. Smooth position updates

**SUCCESS METRIC:**
- All buttons modify real HTML
- No visual glitches
- Operations maintain valid HTML
- Toolbar never off-screen
- Animations at 60fps

---

# WEEK 5: PROPERTIES PANEL

## L4.1: Basic Properties

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Implement basic properties panel with Content/Style/Advanced tabs, text inputs, textarea fields that actually update the selected element's properties in real-time with proper two-way binding.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- Property extraction from HTML elements
- Two-way data binding patterns
- Real-time update strategies
- Property validation rules

**B. RESEARCH ROOT CAUSES:**
- Binding performance issues
- Property sync challenges
- Validation complexity

**C. DEPTH CHECK - For EACH component explain:**
- Property detection algorithm
- Update debouncing approach
- Validation implementation
- Error state handling
- Undo integration

**D. DELIVERABLE REQUIREMENTS:**
Complete properties with:
1. Auto-detects element properties
2. Updates preview instantly
3. Validates input values
4. Shows error states
5. Supports undo/redo
6. Handles special characters

**SUCCESS METRIC:**
- Changes appear immediately
- No input lag
- Validation prevents bad data
- All standard properties supported
- Graceful error handling

---

## L4.2: Rich Text Editor

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Implement complete rich text editor with toolbar (Bold, Italic, Underline, Link, Reference), editable content area, and format application - must actually modify HTML with proper selection handling.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- Rich text editing in Python/Flet
- Selection range handling
- HTML generation from formatting
- Link dialog implementation

**B. RESEARCH ROOT CAUSES:**
- Selection loss on button click
- Format nesting issues
- Browser compatibility

**C. DEPTH CHECK - For EACH component explain:**
- Text selection preservation
- Format command execution
- HTML sanitization approach
- Reference superscript implementation
- Toolbar state updates

**D. DELIVERABLE REQUIREMENTS:**
Complete editor with:
1. All formatting works
2. Selection maintained
3. Link dialog functional
4. Reference numbering automatic
5. Handles paste from Word
6. Outputs clean HTML

**SUCCESS METRIC:**
- Formatting applies correctly
- No selection issues
- Links are clickable
- References auto-number
- Clean HTML output

---

## L4.3: Color Picker

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Implement a complete color picker with preview box, hex input, and color selection UI that updates element styles in real-time - not a mock color picker.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- Color picker UI patterns
- Color format conversions
- Real-time preview updates
- Accessibility considerations

**B. RESEARCH ROOT CAUSES:**
- Color space accuracy
- Performance with frequent updates
- Cross-platform color display

**C. DEPTH CHECK - For EACH component explain:**
- Color picker UI implementation
- HSL/RGB/Hex conversions
- Preview rendering approach
- Eyedropper tool feasibility
- Recent colors storage

**D. DELIVERABLE REQUIREMENTS:**
Complete picker with:
1. Visual color selection
2. Hex/RGB input support
3. Real-time preview
4. Recent colors (last 10)
5. Applies to selection
6. Supports transparency

**SUCCESS METRIC:**
- Smooth color selection
- Accurate color display
- No update lag
- Remembers recent colors
- Works with CSS variables

---

# WEEK 6: CANVAS INTERACTIONS

## L5.1: Drag & Drop

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Implement complete drag and drop system that accepts components from panel, shows drop zone indicators, inserts at correct position, and updates HTML structure - with smooth animations and no glitches.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- Drag and drop in Flet applications
- Drop zone detection algorithms
- HTML insertion strategies
- Animation performance

**B. RESEARCH ROOT CAUSES:**
- Drop position calculation issues
- HTML structure corruption
- Animation frame drops

**C. DEPTH CHECK - For EACH component explain:**
- Drag data transfer format
- Drop zone calculation logic
- Insertion point detection
- HTML generation approach
- Animation sequencing

**D. DELIVERABLE REQUIREMENTS:**
Complete drag & drop with:
1. Smooth drag preview
2. Drop zones highlight
3. Accurate insertion
4. Structure preservation
5. Undo support
6. Multi-element support

**SUCCESS METRIC:**
- No visual glitches
- Drop zones appear instantly
- Insertion never corrupts HTML
- 60fps throughout drag
- Works with nested containers

---

## L5.2: Grid & Guides

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Implement grid overlay system with 20px grid pattern, toggle button functionality, and proper alignment guides that actually help with element positioning - not just visual decoration.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- SVG grid rendering optimization
- Snap-to-grid algorithms
- Guide generation logic
- Performance with many elements

**B. RESEARCH ROOT CAUSES:**
- Grid rendering performance
- Snap calculation accuracy
- Guide overlap issues

**C. DEPTH CHECK - For EACH component explain:**
- Grid SVG generation
- Snap detection approach
- Smart guide algorithm
- Rendering optimization
- Toggle state persistence

**D. DELIVERABLE REQUIREMENTS:**
Complete grid system with:
1. 20px grid renders clearly
2. Elements snap while dragging
3. Smart guides appear
4. Toggle animates smoothly
5. Persists preference
6. No performance impact

**SUCCESS METRIC:**
- Grid visible at all zoom levels
- Snap feels natural
- Guides appear intelligently
- No lag with grid on
- Helps actual alignment

---

# WEEK 7: DATA PERSISTENCE

## L6.1: Save System

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Implement complete save system that preserves project structure, component positions, property values, and metadata with atomic writes and corruption prevention - no data loss scenarios.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- Atomic file writing patterns
- Project state serialization
- Backup strategies
- Corruption detection

**B. RESEARCH ROOT CAUSES:**
- Common save corruption causes
- Race condition scenarios
- Large project performance

**C. DEPTH CHECK - For EACH component explain:**
- Save format (JSON schema)
- Atomic write implementation
- Backup rotation logic
- Compression approach
- Progress indication

**D. DELIVERABLE REQUIREMENTS:**
Complete save system with:
1. Atomic saves (no corruption)
2. Automatic backups (last 5)
3. Progress for large saves
4. Compression for size
5. Validates before write
6. Recovery from crashes

**SUCCESS METRIC:**
- Never loses data
- Saves complete in <2s
- Backups rotate properly
- Can recover from crash
- File size optimized

---

## L6.2: Code Generation

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Implement code generation that exports clean HTML/CSS maintaining formatting, removing editor artifacts, and producing production-ready code - not a simple file dump.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- HTML/CSS beautification
- Editor artifact removal
- Asset handling strategies
- Build optimization options

**B. RESEARCH ROOT CAUSES:**
- Code cleanliness issues
- Asset path problems
- Formatting preservation

**C. DEPTH CHECK - For EACH component explain:**
- Artifact removal algorithm
- Code formatting approach
- Asset copying logic
- Optimization options
- Preview generation

**D. DELIVERABLE REQUIREMENTS:**
Complete export with:
1. Clean, formatted code
2. No editor artifacts
3. Assets copied correctly
4. Optional minification
5. Preview before export
6. Folder structure preserved

**SUCCESS METRIC:**
- Exported site works perfectly
- Code is human-readable
- No editor traces
- Assets load correctly
- Passes HTML/CSS validation

---

## L6.3: History

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Implement history tracking for last 10 actions with timestamps, action descriptions, and basic undo/redo that actually reverts changes - not just a display list.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- Undo/redo pattern implementation
- State snapshot strategies
- Memory management for history
- Action description generation

**B. RESEARCH ROOT CAUSES:**
- Memory growth issues
- State restoration accuracy
- Performance with complex changes

**C. DEPTH CHECK - For EACH component explain:**
- History entry structure
- State diff approach
- Memory limit handling
- Restoration algorithm
- UI update strategy

**D. DELIVERABLE REQUIREMENTS:**
Complete history with:
1. Tracks all user actions
2. Clear descriptions
3. Timestamps included
4. Undo/redo works
5. Memory efficient
6. Survives reload

**SUCCESS METRIC:**
- All actions tracked
- Undo perfectly reverts
- No memory leaks
- Clear action names
- Works after save/load

---

# WEEK 8: MVP POLISH

## L7.1: Error Handling

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Implement comprehensive error handling throughout Canvas Editor with graceful import failures, save error recovery, and user notifications - no unhandled exceptions or silent failures.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- Error categories and priorities
- User notification patterns
- Recovery strategies
- Logging requirements

**B. RESEARCH ROOT CAUSES:**
- Common failure points
- Recovery complexity
- User communication clarity

**C. DEPTH CHECK - For EACH component explain:**
- Error classification system
- Notification UI approach
- Recovery action logic
- Logging implementation
- Debug mode features

**D. DELIVERABLE REQUIREMENTS:**
Complete error handling with:
1. All errors caught
2. User-friendly messages
3. Recovery suggestions
4. Auto-retry for transient
5. Debug log export
6. No data loss

**SUCCESS METRIC:**
- No unhandled exceptions
- Users understand errors
- Recovery always possible
- Logs help debugging
- Graceful degradation

---

## L7.2: Performance

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Implement performance optimizations ensuring smooth drag animations, responsive property updates, and efficient HTML rendering - must maintain 60fps during all operations.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- Performance bottlenecks
- Rendering optimization techniques
- Memory usage patterns
- Animation frame budget

**B. RESEARCH ROOT CAUSES:**
- Current performance issues
- Memory leak sources
- Rendering inefficiencies

**C. DEPTH CHECK - For EACH component explain:**
- Render debouncing strategy
- Memory pooling approach
- Animation optimization
- Lazy loading implementation
- Cache strategy

**D. DELIVERABLE REQUIREMENTS:**
Complete optimization with:
1. 60fps during drag
2. Instant property updates
3. <100ms selection
4. Smooth scrolling
5. Memory stable
6. Large file support

**SUCCESS METRIC:**
- Consistent 60fps
- No UI lag
- Memory doesn't grow
- Handles 1MB+ projects
- Feels native

---

## L7.3: Final Testing

### COMPREHENSIVE IMPLEMENTATION PROMPT

**TASK:**
Perform complete end-to-end testing of Canvas Editor by importing OC2 project, making edits, exporting, and packaging as executable - finding and fixing all remaining issues.

**RESEARCH PHASE (MANDATORY - Complete Before Implementation):**

**A. ANALYZE:**
- Test scenario coverage
- Package requirements
- Distribution options
- User acceptance criteria

**B. RESEARCH ROOT CAUSES:**
- Packaging challenges
- Cross-platform issues
- User workflow problems

**C. DEPTH CHECK - For EACH component explain:**
- Test case structure
- Packaging approach (PyInstaller)
- Distribution format
- Update mechanism
- First-run experience

**D. DELIVERABLE REQUIREMENTS:**
Complete testing with:
1. Full OC2 import/edit/export
2. All features exercised
3. Package as .exe/.app
4. Under 100MB size
5. No external dependencies
6. Professional installer

**SUCCESS METRIC:**
- OC2 roundtrip perfect
- No bugs found
- Installs cleanly
- Runs on fresh system
- Professional appearance

---

# USING THESE PROMPTS

## For Maximum Success:

1. **One Prompt at a Time**: Complete each task fully before moving to the next

2. **Provide Context**: Always include:
   - Current state of the project
   - What's already implemented
   - Any errors you're seeing

3. **Demand Proof**: Ask for:
   - Running code demonstrations
   - Screenshots of working features
   - Actual command outputs

4. **Reject Stubs**: If you see any:
   - `pass` statements
   - `# TODO` comments  
   - `return None  # stub`
   - Mock data instead of real implementation

5. **Test Everything**: Run the verification commands provided

## Example Usage:

```
"I'm starting Week 1, Task F1 of the Canvas Editor. The project is set up at C:\Projects\canvas with the basic main.py file. 

[PASTE THE F1 PROMPT HERE]

Please implement this completely with no stubs or placeholders. Show me the working application with all 4 panels."
```

## Remember:

- These prompts are designed to get COMPLETE implementations
- Don't accept partial solutions
- Each task builds on the previous ones
- Test thoroughly before moving on

Good luck building Canvas! 🎨