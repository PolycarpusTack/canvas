# 🎨 Canvas Editor - Start Here!

## What We're Building
A local visual editor for your web projects (starting with OC2). Think Webflow, but:
- 🏠 **Local** - Your files stay on your computer
- 🔓 **No Lock-in** - Import any project, export clean code
- 🎯 **Focused** - Just what's in the mockup, no bloat

## Quick Start (5 minutes)

### 1. Check Python
```bash
python --version
# Need 3.8 or higher
```

### 2. Install & Test
```bash
cd /mnt/c/Projects/canvas
pip install flet
python test_flet.py
```
You should see a window with a working counter!

### 3. Run the Editor
```bash
python src/main.py
```

## What You'll See
- **Left**: Navigation sidebar (80px)
- **Component Panel**: Draggable components (280px)  
- **Canvas**: Your website preview (center)
- **Properties**: Edit selected elements (320px)

## Development Plan
**8 weeks** to MVP, building one layer at a time:

1. **Week 1**: Foundation (import/export, save/load)
2. **Week 2**: Core UI (all panels working)
3. **Week 3**: Component system
4. **Week 4**: Selection & editing
5. **Week 5**: Properties panel
6. **Week 6**: Drag & drop
7. **Week 7**: Save system & export
8. **Week 8**: Polish & testing

## Key Files
- `MVP_DEVELOPMENT_PLAN.md` - Detailed week-by-week plan
- `src/main.py` - The actual editor (run this!)
- `test_flet.py` - Test if Flet works
- `FUTURE_IDEAS.md` - Cool stuff for later

## Design Decisions
- **Python + Flet** instead of Electron (50MB vs 150MB)
- **Local files** instead of cloud (your data stays yours)
- **MVP focus** (no feature creep!)

## Next Step
1. Run `python test_flet.py` to verify setup
2. Run `python src/main.py` to see the editor
3. Start with Week 1 tasks in `docs/WEEK_1_PLAN.md`

## Remember
We're building exactly what's in the mockup. Nothing more, nothing less. Everything else goes in FUTURE_IDEAS.md.

Let's build something great! 🚀