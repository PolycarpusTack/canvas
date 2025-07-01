# Flet Setup Guide for Windows

## 🔧 Installation

### **Option 1: Simple Install**
```bash
pip install flet
```

### **Option 2: Virtual Environment (Recommended)**
```bash
# Create virtual environment
python -m venv canvas_env

# Activate it
canvas_env\Scripts\activate

# Install packages
pip install -r requirements.txt
```

## 🧪 Test Flet Installation

Create `test_flet.py`:
```python
import flet as ft

def main(page: ft.Page):
    page.title = "Flet Test"
    page.add(
        ft.Text("Hello Canvas!", size=30),
        ft.ElevatedButton("Click me!", on_click=lambda e: page.add(ft.Text("Clicked!")))
    )

ft.app(target=main)
```

Run it:
```bash
python test_flet.py
```

You should see a window with text and a button!

## 🎨 Flet Resources

- **Official Docs**: https://flet.dev/docs/
- **Gallery**: https://flet.dev/gallery/
- **Controls Reference**: https://flet.dev/docs/controls/

## 🚀 Run Canvas Editor

```bash
cd /mnt/c/Projects/canvas
python quickstart.py
```

Or directly:
```bash
python src/main.py
```

## 🐛 Common Issues

### "No module named 'flet'"
- Make sure you activated the virtual environment
- Or install globally: `pip install flet`

### Window doesn't appear
- Check if you have any firewall blocking
- Try: `python -m flet src/main.py`

### Performance issues
- Update graphics drivers
- Flet uses GPU acceleration

## 💡 Development Tips

1. **Hot Reload**: Flet supports hot reload - save file and see changes!
2. **Debug Mode**: Add `page.window.always_on_top = True` for easier development
3. **Console**: Use `print()` statements - they show in terminal

Ready to build something amazing! 🎨