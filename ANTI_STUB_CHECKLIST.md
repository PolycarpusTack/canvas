# Canvas Editor - Anti-Stub Checklist

## 🚨 Run This After EVERY Task Implementation

This checklist ensures you get REAL implementations, not stubs or placeholders.

## 1️⃣ Automated Checks

Run these commands after each task:

```bash
# Check for stub patterns
cd /mnt/c/Projects/canvas
grep -r "TODO\|FIXME\|stub\|mock" src/ | grep -v test_

# Check for empty functions
grep -r "pass\s*$\|pass\s*#" src/

# Check for NotImplemented
grep -r "NotImplementedError\|not.*implemented" src/

# Check for placeholder returns
grep -r "return\s*None\s*#\|return\s*{}\s*#\|return\s*\[\]\s*#" src/

# Check for print-only handlers
grep -r "def.*:[\s]*print.*only" src/ -A 2
```

**Expected result**: All commands should return NOTHING

## 2️⃣ Manual Verification

### For EVERY Function, Verify:

#### ❌ STUB EXAMPLE:
```python
def save_project(self, path):
    print(f"Saving to {path}")
    return True  # TODO: implement
```

#### ✅ REAL EXAMPLE:
```python
def save_project(self, path):
    try:
        # Create backup
        if os.path.exists(path):
            shutil.copy2(path, f"{path}.bak")
        
        # Prepare data
        data = {
            'version': '1.0',
            'name': self.name,
            'created': self.created_at.isoformat(),
            'modified': datetime.now().isoformat(),
            'files': self._serialize_files(),
            'metadata': self.metadata
        }
        
        # Write atomically
        temp_path = f"{path}.tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        # Validate written file
        with open(temp_path, 'r', encoding='utf-8') as f:
            json.load(f)  # Ensures valid JSON
        
        # Atomic rename
        os.replace(temp_path, path)
        
        self.last_saved = datetime.now()
        return True
        
    except Exception as e:
        logger.error(f"Save failed: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise SaveError(f"Could not save project: {e}")
```

## 3️⃣ Feature Testing Checklist

### Week 1: Foundation
- [ ] Can import a real folder (try with OC2)
- [ ] Files are actually detected and listed
- [ ] Save creates a real file on disk
- [ ] Load actually restores the project
- [ ] Window state persists between runs

### Week 2: Core UI
- [ ] Every navigation button shows different content
- [ ] Device switcher actually changes canvas size
- [ ] Save button shows real progress
- [ ] Undo/redo maintains a real history

### Week 3: Components
- [ ] Search actually filters the component list
- [ ] Dragging shows a real preview
- [ ] Components have real HTML templates
- [ ] Canvas renders actual HTML

### Week 4: Selection
- [ ] Can click and select real elements
- [ ] Selection outline appears correctly
- [ ] Toolbar buttons modify real HTML
- [ ] Changes are reflected immediately

### Week 5: Properties
- [ ] Property changes update the canvas
- [ ] Rich text editor produces real HTML
- [ ] Color picker changes actual colors
- [ ] All inputs validate properly

### Week 6: Interactions
- [ ] Drag and drop inserts real components
- [ ] Grid actually helps with alignment
- [ ] Snap-to-grid works while dragging
- [ ] No performance issues

### Week 7: Persistence
- [ ] Save doesn't lose any data
- [ ] Export produces working HTML/CSS
- [ ] History tracks real actions
- [ ] Can undo/redo everything

### Week 8: Polish
- [ ] No unhandled errors anywhere
- [ ] 60fps during all operations
- [ ] Exports working website
- [ ] Runs as standalone executable

## 4️⃣ Code Smell Detectors

### 🚨 Immediate Red Flags:
```python
# Empty except blocks
except:
    pass

# Ignored errors
except Exception:
    continue

# Fake success
def complex_operation():
    time.sleep(1)  # Simulate work
    return {"success": True}

# Placeholder loops
for item in items:
    pass  # Process later

# Mock responses
def fetch_data():
    return [
        {"id": 1, "name": "Test"},
        {"id": 2, "name": "Demo"}
    ]
```

## 5️⃣ Acceptance Criteria

### A Task is ONLY Complete When:

1. **It Works**: The feature does what it promises
2. **It's Real**: No fake data or mock responses
3. **It's Complete**: All edge cases handled
4. **It's Tested**: You've tried to break it
5. **It's Clean**: No TODO/FIXME comments
6. **It's Useful**: You could use it in production

## 6️⃣ What to Say When Rejecting Stubs

```
"This implementation contains stubs/placeholders:
- Line X: Empty function with just 'pass'
- Line Y: Returns hardcoded test data
- Line Z: TODO comment

Please provide a COMPLETE implementation with:
1. Real functionality for every function
2. Proper error handling
3. No placeholder data
4. Working code I can test

I need production-ready code, not prototypes."
```

## 7️⃣ Testing Script

Create `test_implementation.py`:

```python
#!/usr/bin/env python3
"""Test if implementation is complete (no stubs)"""

import os
import re
import sys

def check_stubs(directory):
    stub_patterns = [
        (r'\bTODO\b', 'TODO comment'),
        (r'\bFIXME\b', 'FIXME comment'),
        (r'pass\s*$', 'Empty function'),
        (r'pass\s*#', 'Stub pass statement'),
        (r'NotImplementedError', 'Not implemented'),
        (r'return\s*None\s*#.*stub', 'Stub return'),
        (r'print\(.*coming soon', 'Coming soon message'),
        (r'mock', 'Mock implementation'),
    ]
    
    issues = []
    
    for root, dirs, files in os.walk(directory):
        # Skip test directories
        if 'test' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                    
                for pattern, description in stub_patterns:
                    for match in re.finditer(pattern, content, re.MULTILINE):
                        line_no = content[:match.start()].count('\n') + 1
                        issues.append(f"{filepath}:{line_no} - {description}")
    
    return issues

if __name__ == "__main__":
    issues = check_stubs('src')
    
    if issues:
        print("❌ STUB CODE DETECTED:\n")
        for issue in issues:
            print(f"  {issue}")
        print(f"\n{len(issues)} issues found!")
        sys.exit(1)
    else:
        print("✅ No stubs detected - implementation appears complete!")
        sys.exit(0)
```

Run after each task:
```bash
python test_implementation.py
```

## 🎯 Remember

**Every line of code should do real work.** If it doesn't, it's a stub that needs to be replaced with actual implementation.

No exceptions. No "we'll fix it later." No "this is just for testing."

Build it right the first time! 💪