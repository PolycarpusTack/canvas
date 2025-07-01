# Nice-to-Haves Enhancement Plan - Development Plan

## Phase 1: Solution Design Analysis & Validation

### 1. Initial Understanding
- **Goal**: Implement platform-specific integrations and advanced UI enhancements
- **Stack**: Flet UI, Python with platform-specific bindings
- **Components**: Eyedropper Tool, Advanced Animation Editor, Platform File Picker
- **User Personas**: Power users requiring advanced editing capabilities

### 2. Clarity Assessment
- **Eyedropper Tool**: Medium (2) - Platform-specific screen capture required
- **Animation Editor**: High (3) - Clear requirements for keyframe editing
- **File Picker**: High (3) - Standard OS file dialog integration
- **Platform Detection**: High (3) - Clear APIs available
- **Overall Clarity**: High (3)

### 3. Technical Feasibility
- **Eyedropper**: High risk (3) - Requires screen capture permissions
- **Animation Editor**: Medium risk (2) - Complex UI but doable
- **File Picker**: Low risk (1) - Standard OS integration
- **Cross-platform**: Medium risk (2) - Different implementations per OS

### 4. Security Assessment
- **Screen Capture**: Requires user permission on modern OS
- **File Access**: Validate file paths and permissions
- **Animation Scripts**: Sanitize keyframe values

### 5. Compliance
- **Privacy**: Screen capture requires explicit consent
- **Accessibility**: Ensure keyboard alternatives for all tools

**Recommendation**: PROCEEDING with selective implementation based on platform

---

## EPIC A: Platform-Specific Integrations

Implement native OS integrations for enhanced user experience.

**Definition of Done:**
- ✓ Platform detection and fallback mechanisms
- ✓ Native file picker on supported platforms
- ✓ Eyedropper with proper permissions
- ✓ Graceful degradation on unsupported platforms

**Business Value:** Enhanced power-user features for professional designers

**Risk Assessment:**
- Platform compatibility (High/3) - Different APIs per OS
- Permission management (Medium/2) - User consent required
- Testing complexity (Medium/2) - Multiple OS versions

**Cross-Functional Requirements:**
- Security: Request minimum required permissions
- UX: Clear permission request dialogs
- Performance: Non-blocking native calls
- Compatibility: Fallback for web/limited environments

---

### USER STORY A-1: Native File Picker Integration

**ID & Title:** A-1: Implement Platform-Native File Picker
**User Persona Narrative:** As a designer, I want to use my OS's native file picker so I have a familiar file selection experience
**Business Value:** Medium (2)
**Priority Score:** 4
**Story Points:** M

**Acceptance Criteria:**
```gherkin
Given I click the file upload button
When the file picker opens
Then I see my OS's native file dialog
And I can navigate my file system normally
And file type filters are properly applied

Given I'm on an unsupported platform
When I click the file upload button
Then I see the web-based file input
And functionality is preserved with graceful degradation
```

**External Dependencies:** 
- Windows: win32 API
- macOS: Cocoa/AppKit
- Linux: GTK or Qt bindings

**Technical Debt Considerations:** Abstract platform detection for reuse

---

#### TASK A-1-T1: Implement Platform Detection Service

**Goal:** Create service to detect platform and capabilities

**Token Budget:** 4,000 tokens

**Required Implementation:**
```python
import platform
import sys
from enum import Enum, auto
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class Platform(Enum):
    """Supported platforms"""
    WINDOWS = auto()
    MACOS = auto()
    LINUX = auto()
    WEB = auto()
    UNKNOWN = auto()

class Capability(Enum):
    """Platform capabilities"""
    NATIVE_FILE_PICKER = auto()
    SCREEN_CAPTURE = auto()
    SYSTEM_FONTS = auto()
    CLIPBOARD_IMAGE = auto()
    DRAG_DROP_FILES = auto()

class PlatformService:
    """
    CLAUDE.md #1.3: Singleton for platform detection
    CLAUDE.md #1.4: Extensible for new platforms
    """
    _instance = None
    
    def __init__(self):
        self.platform = self._detect_platform()
        self.capabilities = self._detect_capabilities()
        self._init_platform_modules()
    
    def _detect_platform(self) -> Platform:
        """Detect current platform"""
        system = platform.system().lower()
        
        if system == 'windows':
            return Platform.WINDOWS
        elif system == 'darwin':
            return Platform.MACOS
        elif system == 'linux':
            return Platform.LINUX
        elif hasattr(sys, 'platform') and 'emscripten' in sys.platform:
            return Platform.WEB
        else:
            return Platform.UNKNOWN
    
    def _detect_capabilities(self) -> Dict[Capability, bool]:
        """Detect available capabilities for current platform"""
        capabilities = {}
        
        # Platform-specific capability detection
        if self.platform == Platform.WINDOWS:
            capabilities[Capability.NATIVE_FILE_PICKER] = self._check_win32_available()
            capabilities[Capability.SCREEN_CAPTURE] = True
            capabilities[Capability.CLIPBOARD_IMAGE] = True
            
        elif self.platform == Platform.MACOS:
            capabilities[Capability.NATIVE_FILE_PICKER] = self._check_cocoa_available()
            capabilities[Capability.SCREEN_CAPTURE] = self._check_screen_recording_permission()
            capabilities[Capability.CLIPBOARD_IMAGE] = True
            
        elif self.platform == Platform.LINUX:
            capabilities[Capability.NATIVE_FILE_PICKER] = self._check_gtk_available()
            capabilities[Capability.SCREEN_CAPTURE] = self._check_x11_available()
            capabilities[Capability.CLIPBOARD_IMAGE] = self._check_clipboard_available()
            
        else:
            # Web or unknown - limited capabilities
            for cap in Capability:
                capabilities[cap] = False
        
        return capabilities
    
    def has_capability(self, capability: Capability) -> bool:
        """Check if platform has specific capability"""
        return self.capabilities.get(capability, False)
    
    def _check_win32_available(self) -> bool:
        """Check if Windows APIs are available"""
        try:
            import win32api
            return True
        except ImportError:
            logger.warning("win32api not available - native file picker disabled")
            return False
    
    def _check_cocoa_available(self) -> bool:
        """Check if macOS Cocoa APIs are available"""
        try:
            import AppKit
            return True
        except ImportError:
            logger.warning("AppKit not available - native file picker disabled")
            return False
    
    def _check_gtk_available(self) -> bool:
        """Check if GTK is available on Linux"""
        try:
            import gi
            gi.require_version('Gtk', '3.0')
            from gi.repository import Gtk
            return True
        except (ImportError, ValueError):
            logger.warning("GTK not available - trying Qt")
            return self._check_qt_available()
    
    def _check_qt_available(self) -> bool:
        """Check if Qt is available as fallback"""
        try:
            from PyQt5 import QtWidgets
            return True
        except ImportError:
            try:
                from PySide2 import QtWidgets
                return True
            except ImportError:
                return False
```

**Deliverables:**
- Platform detection service
- Capability detection for each platform
- Graceful fallback mechanisms
- Platform-specific module initialization

**Quality Gates:**
- ✓ All platforms correctly detected
- ✓ Capabilities accurately reported
- ✓ No crashes on missing dependencies
- ✓ Proper logging of limitations

**Unblocks:** [A-1-T2, A-2-T1]
**Confidence Score:** High (3)

---

#### TASK A-1-T2: Implement Native File Pickers

**Goal:** Create native file picker implementations for each platform

**Token Budget:** 8,000 tokens

**Windows Implementation:**
```python
class WindowsFilePicker:
    """
    Windows native file picker using win32 APIs
    CLAUDE.md #2.1.4: Graceful error handling
    """
    def __init__(self):
        try:
            import win32gui
            import win32con
            self.win32gui = win32gui
            self.win32con = win32con
            self.available = True
        except ImportError:
            self.available = False
    
    def pick_file(
        self,
        title: str = "Select File",
        file_types: List[Tuple[str, str]] = None,
        initial_dir: str = None,
        multiple: bool = False
    ) -> Optional[Union[str, List[str]]]:
        """
        Show native Windows file picker
        
        Args:
            title: Dialog title
            file_types: List of (description, pattern) tuples
            initial_dir: Starting directory
            multiple: Allow multiple selection
            
        Returns:
            Selected file path(s) or None if cancelled
        """
        if not self.available:
            return None
        
        try:
            # Build filter string
            if file_types:
                filter_str = ""
                for desc, pattern in file_types:
                    filter_str += f"{desc}\0{pattern}\0"
                filter_str += "All Files (*.*)\0*.*\0"
            else:
                filter_str = "All Files (*.*)\0*.*\0"
            
            # Configure dialog
            flags = self.win32con.OFN_EXPLORER | self.win32con.OFN_FILEMUSTEXIST
            if multiple:
                flags |= self.win32con.OFN_ALLOWMULTISELECT
            
            # Show dialog
            file_path = self.win32gui.GetOpenFileNameW(
                Title=title,
                Filter=filter_str,
                InitialDir=initial_dir or "",
                Flags=flags
            )
            
            if file_path:
                return file_path[0] if isinstance(file_path, tuple) else file_path
            
        except Exception as e:
            logger.error(f"Windows file picker error: {e}")
        
        return None
```

**macOS Implementation:**
```python
class MacOSFilePicker:
    """macOS native file picker using PyObjC"""
    def __init__(self):
        try:
            from AppKit import NSOpenPanel, NSApplication
            self.NSOpenPanel = NSOpenPanel
            self.NSApplication = NSApplication
            self.available = True
        except ImportError:
            self.available = False
    
    def pick_file(
        self,
        title: str = "Select File",
        file_types: List[Tuple[str, str]] = None,
        initial_dir: str = None,
        multiple: bool = False
    ) -> Optional[Union[str, List[str]]]:
        """Show native macOS file picker"""
        if not self.available:
            return None
        
        try:
            # Create panel
            panel = self.NSOpenPanel.openPanel()
            panel.setTitle_(title)
            panel.setCanChooseFiles_(True)
            panel.setCanChooseDirectories_(False)
            panel.setAllowsMultipleSelection_(multiple)
            
            # Set file types
            if file_types:
                extensions = []
                for _, pattern in file_types:
                    # Extract extensions from patterns like "*.jpg"
                    if pattern.startswith("*."):
                        extensions.append(pattern[2:])
                panel.setAllowedFileTypes_(extensions)
            
            # Set initial directory
            if initial_dir:
                panel.setDirectoryURL_(NSURL.fileURLWithPath_(initial_dir))
            
            # Show dialog
            if panel.runModal() == 1:  # NSModalResponseOK
                urls = panel.URLs()
                paths = [str(url.path()) for url in urls]
                return paths if multiple else paths[0]
                
        except Exception as e:
            logger.error(f"macOS file picker error: {e}")
        
        return None
```

**Linux Implementation:**
```python
class LinuxFilePicker:
    """Linux file picker using GTK or Qt"""
    def __init__(self):
        self.backend = self._detect_backend()
        self.available = self.backend is not None
    
    def _detect_backend(self) -> Optional[str]:
        """Detect available UI backend"""
        try:
            import gi
            gi.require_version('Gtk', '3.0')
            from gi.repository import Gtk
            return 'gtk'
        except:
            try:
                from PyQt5 import QtWidgets
                return 'qt'
            except:
                return None
    
    def pick_file(
        self,
        title: str = "Select File",
        file_types: List[Tuple[str, str]] = None,
        initial_dir: str = None,
        multiple: bool = False
    ) -> Optional[Union[str, List[str]]]:
        """Show native Linux file picker"""
        if self.backend == 'gtk':
            return self._pick_file_gtk(title, file_types, initial_dir, multiple)
        elif self.backend == 'qt':
            return self._pick_file_qt(title, file_types, initial_dir, multiple)
        return None
```

**Unified Interface:**
```python
class NativeFilePicker:
    """
    Unified native file picker interface
    CLAUDE.md #1.4: Extensible for new platforms
    """
    def __init__(self):
        self.platform_service = PlatformService.get_instance()
        self.picker = self._create_picker()
    
    def _create_picker(self):
        """Create platform-specific picker"""
        platform = self.platform_service.platform
        
        if platform == Platform.WINDOWS:
            return WindowsFilePicker()
        elif platform == Platform.MACOS:
            return MacOSFilePicker()
        elif platform == Platform.LINUX:
            return LinuxFilePicker()
        else:
            return None
    
    def pick_file(self, **kwargs) -> Optional[Union[str, List[str]]]:
        """Show file picker with fallback to web input"""
        if self.picker and self.picker.available:
            result = self.picker.pick_file(**kwargs)
            if result is not None:
                return result
        
        # Fallback to web-based input
        logger.info("Using web-based file input fallback")
        return self._web_fallback(**kwargs)
```

**Unblocks:** [A-1-T3]
**Confidence Score:** Medium (2) - Platform-specific complexity

---

#### TASK A-1-T3: Integrate File Picker with Property System

**Goal:** Update FilePropertyInput to use native picker

**Token Budget:** 4,000 tokens

**Implementation:**
```python
class EnhancedFilePropertyInput(FilePropertyInput):
    """
    Enhanced file input with native picker support
    CLAUDE.md #7.2: Graceful degradation
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.native_picker = NativeFilePicker()
        self.platform_service = PlatformService.get_instance()
    
    def _build_input_control(self) -> ft.Control:
        """Build file input with native picker button"""
        # File path display
        self.file_path_field = ft.TextField(
            value=self.value or "",
            read_only=True,
            hint_text="No file selected",
            expand=True,
            height=40,
            border_radius=6
        )
        
        # Native picker button (if available)
        if self.platform_service.has_capability(Capability.NATIVE_FILE_PICKER):
            picker_button = ft.ElevatedButton(
                "Browse...",
                icon=ft.Icons.FOLDER_OPEN,
                on_click=lambda e: self._open_native_picker()
            )
        else:
            # Fallback to web input
            picker_button = ft.ElevatedButton(
                "Choose File",
                icon=ft.Icons.UPLOAD_FILE,
                on_click=lambda e: self._open_web_picker()
            )
        
        # Clear button
        clear_button = ft.IconButton(
            icon=ft.Icons.CLEAR,
            tooltip="Clear selection",
            on_click=lambda e: self._clear_selection(),
            visible=bool(self.value)
        )
        
        # File preview (if applicable)
        preview = self._build_file_preview()
        
        return ft.Column([
            ft.Row([
                self.file_path_field,
                picker_button,
                clear_button
            ], spacing=8),
            preview if preview else ft.Container()
        ], spacing=8)
    
    def _open_native_picker(self) -> None:
        """Open native file picker"""
        # Get file type filters from validation
        file_types = []
        if self.definition.validation and hasattr(self.definition.validation, 'allowed_extensions'):
            for ext in self.definition.validation.allowed_extensions:
                file_types.append((f"{ext.upper()} files", f"*.{ext}"))
        
        # Show picker
        result = self.native_picker.pick_file(
            title=f"Select {self.definition.label}",
            file_types=file_types,
            multiple=False
        )
        
        if result:
            self._handle_file_selection(result)
    
    def _handle_file_selection(self, file_path: str) -> None:
        """Handle file selection with validation"""
        # Validate file
        if self._validate_file(file_path):
            self.file_path_field.value = file_path
            self.clear_button.visible = True
            self._handle_change(file_path)
            self._update_preview(file_path)
        else:
            # Show error
            self._show_error("Invalid file type or size")
```

**Platform-Specific Styling:**
```python
def _get_platform_style(self) -> Dict[str, Any]:
    """Get platform-specific styling"""
    platform = self.platform_service.platform
    
    if platform == Platform.WINDOWS:
        return {
            "button_style": ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=2),
                padding=ft.padding.symmetric(horizontal=12, vertical=6)
            )
        }
    elif platform == Platform.MACOS:
        return {
            "button_style": ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=16, vertical=8)
            )
        }
    else:
        return {}
```

**Unblocks:** [A-2-T1]
**Confidence Score:** High (3)

---

### USER STORY A-2: Eyedropper Color Picker

**ID & Title:** A-2: Implement Screen Color Eyedropper
**User Persona Narrative:** As a designer, I want to pick colors from anywhere on my screen so I can match existing designs
**Business Value:** Low (1) - Nice power-user feature
**Priority Score:** 2
**Story Points:** L

**Acceptance Criteria:**
```gherkin
Given I click the eyedropper button
When I grant screen capture permission
Then I can move my cursor anywhere on screen
And see a magnified preview of the area
And click to capture the color value

Given I'm on a platform without screen capture
When I click the eyedropper button
Then I see a message explaining the limitation
And the button is appropriately disabled
```

---

#### TASK A-2-T1: Implement Screen Capture Service

**Goal:** Create cross-platform screen capture for eyedropper

**Token Budget:** 6,000 tokens

**Implementation:**
```python
import threading
from PIL import ImageGrab, Image
import numpy as np

class ScreenCaptureService:
    """
    Cross-platform screen capture service
    CLAUDE.md #10.1: Proper permission handling
    """
    def __init__(self):
        self.platform_service = PlatformService.get_instance()
        self.permission_granted = False
        self._check_permissions()
    
    def _check_permissions(self) -> None:
        """Check and request screen capture permissions"""
        platform = self.platform_service.platform
        
        if platform == Platform.MACOS:
            # macOS requires explicit permission
            self.permission_granted = self._check_macos_permission()
        elif platform == Platform.WINDOWS:
            # Windows generally allows screen capture
            self.permission_granted = True
        elif platform == Platform.LINUX:
            # Linux depends on display server
            self.permission_granted = self._check_linux_permission()
        else:
            self.permission_granted = False
    
    def _check_macos_permission(self) -> bool:
        """Check macOS screen recording permission"""
        try:
            import Quartz
            # Try to create a screen capture session
            display_id = Quartz.CGMainDisplayID()
            image = Quartz.CGDisplayCreateImage(display_id)
            return image is not None
        except:
            return False
    
    def capture_screen_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int
    ) -> Optional[Image.Image]:
        """Capture a region of the screen"""
        if not self.permission_granted:
            logger.error("Screen capture permission not granted")
            return None
        
        try:
            # Use PIL for cross-platform capture
            bbox = (x, y, x + width, y + height)
            screenshot = ImageGrab.grab(bbox=bbox)
            return screenshot
        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            return None
    
    def get_pixel_color(self, x: int, y: int) -> Optional[Tuple[int, int, int]]:
        """Get color of a single pixel"""
        # Capture 1x1 region for efficiency
        image = self.capture_screen_region(x, y, 1, 1)
        if image:
            return image.getpixel((0, 0))
        return None
```

**Eyedropper Implementation:**
```python
class EyedropperTool:
    """
    Screen color eyedropper tool
    CLAUDE.md #9.3: Keyboard shortcuts for accessibility
    """
    def __init__(self, on_color_picked: Callable[[str], None]):
        self.on_color_picked = on_color_picked
        self.capture_service = ScreenCaptureService()
        self.active = False
        self.magnifier_size = 11  # 11x11 pixel grid
        self.zoom_factor = 10
        
    def start_picking(self) -> bool:
        """Start eyedropper mode"""
        if not self.capture_service.permission_granted:
            self._show_permission_dialog()
            return False
        
        self.active = True
        self._start_capture_thread()
        return True
    
    def _start_capture_thread(self) -> None:
        """Start background thread for cursor tracking"""
        def capture_loop():
            while self.active:
                # Get cursor position
                x, y = self._get_cursor_position()
                
                # Capture area around cursor
                half_size = self.magnifier_size // 2
                region = self.capture_service.capture_screen_region(
                    x - half_size,
                    y - half_size,
                    self.magnifier_size,
                    self.magnifier_size
                )
                
                if region:
                    self._update_magnifier(region, x, y)
                
                # Small delay to reduce CPU usage
                time.sleep(0.016)  # ~60 FPS
        
        thread = threading.Thread(target=capture_loop, daemon=True)
        thread.start()
    
    def _update_magnifier(self, region: Image.Image, cursor_x: int, cursor_y: int) -> None:
        """Update magnifier preview"""
        # Get center pixel color
        center = self.magnifier_size // 2
        center_color = region.getpixel((center, center))
        hex_color = "#{:02x}{:02x}{:02x}".format(*center_color)
        
        # Update UI (would need to be connected to actual UI)
        self._update_ui_preview(region, hex_color)
    
    def pick_color(self) -> None:
        """Pick color at current cursor position"""
        if not self.active:
            return
        
        x, y = self._get_cursor_position()
        color = self.capture_service.get_pixel_color(x, y)
        
        if color:
            hex_color = "#{:02x}{:02x}{:02x}".format(*color)
            self.on_color_picked(hex_color)
            self.stop_picking()
```

**UI Integration:**
```python
class EyedropperButton(ft.Container):
    """Eyedropper button with platform awareness"""
    def __init__(self, on_color_picked: Callable[[str], None]):
        super().__init__()
        self.on_color_picked = on_color_picked
        self.platform_service = PlatformService.get_instance()
        self.eyedropper = None
        
        # Check if eyedropper is available
        self.available = self.platform_service.has_capability(Capability.SCREEN_CAPTURE)
        
        self.content = self._build_button()
    
    def _build_button(self) -> ft.Control:
        """Build eyedropper button"""
        if self.available:
            return ft.IconButton(
                icon=ft.Icons.COLORIZE,
                tooltip="Pick color from screen (Alt+E)",
                on_click=lambda e: self._start_eyedropper()
            )
        else:
            return ft.IconButton(
                icon=ft.Icons.COLORIZE,
                tooltip="Eyedropper not available on this platform",
                disabled=True
            )
    
    def _start_eyedropper(self) -> None:
        """Start eyedropper tool"""
        if not self.eyedropper:
            self.eyedropper = EyedropperTool(self.on_color_picked)
        
        if self.eyedropper.start_picking():
            # Show eyedropper UI overlay
            self._show_eyedropper_overlay()
```

**Unblocks:** [B-1-T1]
**Confidence Score:** Low (1) - Complex platform-specific implementation

---

## EPIC B: Advanced UI Enhancements

Implement advanced editors and UI improvements for power users.

---

### USER STORY B-1: Advanced Animation Editor

**ID & Title:** B-1: Create Keyframe Animation Editor
**User Persona Narrative:** As a designer, I want to create complex animations with keyframes so I can build engaging interactions
**Business Value:** Low (1) - Advanced feature for power users
**Priority Score:** 2
**Story Points:** XL

**Acceptance Criteria:**
```gherkin
Given I select an animatable property
When I click "Create Animation"
Then I see a timeline editor
And I can add keyframes at specific times
And set easing functions between keyframes
And preview the animation in real-time

Given I have created an animation
When I save the component
Then the animation data is properly stored
And can be played back correctly
```

---

#### TASK B-1-T1: Implement Animation Timeline UI

**Goal:** Create timeline-based animation editor

**Token Budget:** 10,000 tokens

**Implementation:**
```python
@dataclass
class Keyframe:
    """Single keyframe in animation"""
    time: float  # Time in seconds
    value: Any  # Property value at this time
    easing: str = "linear"  # Easing function
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class AnimationTrack:
    """Animation track for a single property"""
    property_name: str
    keyframes: List[Keyframe] = field(default_factory=list)
    duration: float = 1.0
    loop: bool = False
    
    def add_keyframe(self, time: float, value: Any, easing: str = "linear") -> None:
        """Add keyframe maintaining time order"""
        keyframe = Keyframe(time=time, value=value, easing=easing)
        self.keyframes.append(keyframe)
        self.keyframes.sort(key=lambda k: k.time)
        self.duration = max(self.duration, time)
    
    def get_value_at_time(self, time: float) -> Any:
        """Calculate interpolated value at specific time"""
        if not self.keyframes:
            return None
        
        # Handle loop
        if self.loop and time > self.duration:
            time = time % self.duration
        
        # Find surrounding keyframes
        prev_kf = None
        next_kf = None
        
        for kf in self.keyframes:
            if kf.time <= time:
                prev_kf = kf
            else:
                next_kf = kf
                break
        
        # Interpolate between keyframes
        if prev_kf and next_kf:
            progress = (time - prev_kf.time) / (next_kf.time - prev_kf.time)
            eased_progress = self._apply_easing(progress, prev_kf.easing)
            return self._interpolate_values(prev_kf.value, next_kf.value, eased_progress)
        elif prev_kf:
            return prev_kf.value
        else:
            return self.keyframes[0].value if self.keyframes else None

class AnimationTimeline(ft.UserControl):
    """
    Visual timeline editor for animations
    CLAUDE.md #1.1: Professional UI design
    """
    def __init__(
        self,
        track: AnimationTrack,
        property_type: PropertyType,
        on_change: Callable[[AnimationTrack], None]
    ):
        super().__init__()
        self.track = track
        self.property_type = property_type
        self.on_change = on_change
        self.selected_keyframe: Optional[Keyframe] = None
        self.timeline_width = 600
        self.timeline_height = 80
        self.playhead_position = 0.0
        self.playing = False
        
    def build(self) -> ft.Control:
        return ft.Column([
            # Timeline header
            self._build_header(),
            
            # Timeline canvas
            ft.Container(
                content=ft.Stack([
                    # Timeline background
                    self._build_timeline_background(),
                    
                    # Keyframe markers
                    self._build_keyframe_markers(),
                    
                    # Playhead
                    self._build_playhead(),
                    
                    # Time ruler
                    self._build_time_ruler()
                ]),
                width=self.timeline_width,
                height=self.timeline_height,
                border=ft.border.all(1, "#E5E7EB"),
                border_radius=4,
                bgcolor="#F9FAFB"
            ),
            
            # Keyframe editor
            self._build_keyframe_editor(),
            
            # Animation controls
            self._build_controls()
        ], spacing=12)
    
    def _build_header(self) -> ft.Control:
        """Build timeline header with property info"""
        return ft.Row([
            ft.Icon(ft.Icons.ANIMATION, size=20, color="#5E6AD2"),
            ft.Text(
                f"Animation: {self.track.property_name}",
                size=16,
                weight=ft.FontWeight.W_500
            ),
            ft.Container(expand=True),
            ft.Text(
                f"Duration: {self.track.duration}s",
                size=14,
                color="#6B7280"
            )
        ])
    
    def _build_keyframe_markers(self) -> ft.Control:
        """Build interactive keyframe markers"""
        markers = []
        
        for kf in self.track.keyframes:
            x_pos = (kf.time / self.track.duration) * self.timeline_width
            
            marker = ft.Container(
                content=ft.Icon(
                    ft.Icons.CIRCLE,
                    size=12,
                    color="#5E6AD2" if kf == self.selected_keyframe else "#9CA3AF"
                ),
                left=x_pos - 6,
                top=self.timeline_height // 2 - 6,
                on_click=lambda e, k=kf: self._select_keyframe(k),
                tooltip=f"Time: {kf.time}s\nValue: {kf.value}"
            )
            markers.append(marker)
        
        return ft.Stack(markers)
    
    def _build_keyframe_editor(self) -> ft.Control:
        """Build keyframe property editor"""
        if not self.selected_keyframe:
            return ft.Container(
                content=ft.Text(
                    "Select a keyframe to edit",
                    size=14,
                    color="#9CA3AF",
                    text_align=ft.TextAlign.CENTER
                ),
                padding=20,
                bgcolor="#F9FAFB",
                border_radius=4,
                alignment=ft.alignment.center
            )
        
        # Time input
        time_input = ft.TextField(
            label="Time (s)",
            value=str(self.selected_keyframe.time),
            width=100,
            on_change=lambda e: self._update_keyframe_time(float(e.control.value))
        )
        
        # Value input (type-specific)
        value_input = self._create_value_input()
        
        # Easing selector
        easing_dropdown = ft.Dropdown(
            label="Easing",
            options=[
                ft.dropdown.Option("linear", "Linear"),
                ft.dropdown.Option("ease-in", "Ease In"),
                ft.dropdown.Option("ease-out", "Ease Out"),
                ft.dropdown.Option("ease-in-out", "Ease In-Out"),
                ft.dropdown.Option("cubic-bezier", "Custom Cubic"),
                ft.dropdown.Option("spring", "Spring")
            ],
            value=self.selected_keyframe.easing,
            on_change=lambda e: self._update_keyframe_easing(e.control.value)
        )
        
        # Delete button
        delete_button = ft.IconButton(
            icon=ft.Icons.DELETE,
            icon_color="#EF4444",
            tooltip="Delete keyframe",
            on_click=lambda e: self._delete_keyframe()
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Keyframe Properties", size=14, weight=ft.FontWeight.W_500),
                ft.Row([
                    time_input,
                    value_input,
                    easing_dropdown,
                    delete_button
                ], spacing=12)
            ], spacing=8),
            padding=12,
            bgcolor="#F9FAFB",
            border_radius=4
        )
```

**Animation Preview:**
```python
class AnimationPreview(ft.UserControl):
    """
    Real-time animation preview
    CLAUDE.md #12.4: Smooth 60fps animations
    """
    def __init__(self, component_id: str, track: AnimationTrack):
        super().__init__()
        self.component_id = component_id
        self.track = track
        self.preview_component = None
        self.animation_timer = None
        self.start_time = None
        
    def build(self) -> ft.Control:
        return ft.Container(
            content=ft.Column([
                ft.Text("Preview", size=14, weight=ft.FontWeight.W_500),
                ft.Container(
                    content=self._build_preview_area(),
                    height=200,
                    bgcolor="#F9FAFB",
                    border=ft.border.all(1, "#E5E7EB"),
                    border_radius=4,
                    alignment=ft.alignment.center
                )
            ], spacing=8),
            padding=12
        )
    
    def start_preview(self) -> None:
        """Start animation preview"""
        self.start_time = time.time()
        self._animate_frame()
    
    def _animate_frame(self) -> None:
        """Animate single frame"""
        if not self.start_time:
            return
        
        # Calculate current time
        elapsed = time.time() - self.start_time
        
        # Get interpolated value
        value = self.track.get_value_at_time(elapsed)
        
        # Apply to preview component
        if self.preview_component and value is not None:
            self._apply_animated_value(value)
        
        # Continue animation
        if elapsed < self.track.duration or self.track.loop:
            self.page.run_task(self._animate_frame, delay=16)  # 60 FPS
        else:
            self.start_time = None
```

**Unblocks:** [B-1-T2]
**Confidence Score:** Medium (2) - Complex UI component

---

#### TASK B-1-T2: Implement Animation Export/Import

**Goal:** Save and load animation data

**Token Budget:** 4,000 tokens

**Implementation:**
```python
@dataclass
class AnimationData:
    """
    Serializable animation data
    CLAUDE.md #4.3: Explicit versioning
    """
    version: str = "1.0"
    tracks: Dict[str, AnimationTrack] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "version": self.version,
            "tracks": {
                name: {
                    "property_name": track.property_name,
                    "duration": track.duration,
                    "loop": track.loop,
                    "keyframes": [
                        {
                            "time": kf.time,
                            "value": kf.value,
                            "easing": kf.easing,
                            "id": kf.id
                        }
                        for kf in track.keyframes
                    ]
                }
                for name, track in self.tracks.items()
            },
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimationData":
        """Deserialize from dictionary"""
        # Version compatibility check
        version = data.get("version", "1.0")
        if version != cls.version:
            data = cls._migrate_data(data, version)
        
        # Reconstruct tracks
        tracks = {}
        for name, track_data in data.get("tracks", {}).items():
            track = AnimationTrack(
                property_name=track_data["property_name"],
                duration=track_data["duration"],
                loop=track_data.get("loop", False)
            )
            
            for kf_data in track_data.get("keyframes", []):
                track.keyframes.append(Keyframe(
                    time=kf_data["time"],
                    value=kf_data["value"],
                    easing=kf_data.get("easing", "linear"),
                    id=kf_data.get("id", str(uuid.uuid4()))
                ))
            
            tracks[name] = track
        
        return cls(
            version=version,
            tracks=tracks,
            metadata=data.get("metadata", {})
        )

class AnimationExporter:
    """Export animations to various formats"""
    
    @staticmethod
    def export_to_css(animation_data: AnimationData) -> str:
        """Export as CSS keyframes"""
        css_output = []
        
        for name, track in animation_data.tracks.items():
            # Generate keyframe name
            keyframe_name = f"animation-{name.replace('_', '-')}"
            
            # Build keyframes
            css_output.append(f"@keyframes {keyframe_name} {{")
            
            for kf in track.keyframes:
                percentage = (kf.time / track.duration) * 100
                css_value = AnimationExporter._convert_value_to_css(
                    track.property_name,
                    kf.value
                )
                css_output.append(f"  {percentage:.1f}% {{ {css_value} }}")
            
            css_output.append("}")
            
            # Animation declaration
            css_output.append(f".animated-{name} {{")
            css_output.append(f"  animation: {keyframe_name} {track.duration}s;")
            if track.loop:
                css_output.append(f"  animation-iteration-count: infinite;")
            css_output.append("}")
        
        return "\n".join(css_output)
    
    @staticmethod
    def export_to_lottie(animation_data: AnimationData) -> Dict[str, Any]:
        """Export as Lottie JSON format"""
        # Simplified Lottie export
        return {
            "v": "5.7.0",
            "fr": 60,
            "ip": 0,
            "op": int(max(track.duration for track in animation_data.tracks.values()) * 60),
            "w": 100,
            "h": 100,
            "layers": [
                AnimationExporter._track_to_lottie_layer(name, track)
                for name, track in animation_data.tracks.items()
            ]
        }
```

**Unblocks:** None
**Confidence Score:** High (3)

---

## Testing Strategy

### Platform Testing Matrix
```python
@pytest.mark.parametrize("platform,capability,expected", [
    (Platform.WINDOWS, Capability.NATIVE_FILE_PICKER, True),
    (Platform.WINDOWS, Capability.SCREEN_CAPTURE, True),
    (Platform.MACOS, Capability.NATIVE_FILE_PICKER, True),
    (Platform.MACOS, Capability.SCREEN_CAPTURE, False),  # Without permission
    (Platform.LINUX, Capability.NATIVE_FILE_PICKER, True),  # If GTK available
    (Platform.WEB, Capability.NATIVE_FILE_PICKER, False),
])
def test_platform_capabilities(platform, capability, expected):
    """Test platform capability detection"""
    with mock.patch('platform.system') as mock_system:
        # Mock platform
        mock_system.return_value = platform.name
        
        service = PlatformService()
        assert service.has_capability(capability) == expected
```

### Integration Testing
```python
def test_native_file_picker_fallback():
    """Test fallback when native picker unavailable"""
    picker = NativeFilePicker()
    
    # Mock unavailable native picker
    picker.picker = None
    
    # Should fall back gracefully
    result = picker.pick_file(title="Test")
    assert result is None or isinstance(result, str)
```

---

## Security Considerations

### Permission Management
```python
class PermissionManager:
    """
    Centralized permission management
    CLAUDE.md #10.1: Explicit permission handling
    """
    REQUIRED_PERMISSIONS = {
        Capability.SCREEN_CAPTURE: {
            Platform.MACOS: ["NSScreenCaptureUsageDescription"],
            Platform.WINDOWS: [],
            Platform.LINUX: ["x11_access"]
        },
        Capability.NATIVE_FILE_PICKER: {
            Platform.MACOS: ["NSOpenPanel"],
            Platform.WINDOWS: ["file_dialog"],
            Platform.LINUX: ["gtk_file_chooser"]
        }
    }
    
    @staticmethod
    def request_permission(capability: Capability) -> bool:
        """Request permission for capability"""
        platform = PlatformService.get_instance().platform
        required = PermissionManager.REQUIRED_PERMISSIONS.get(capability, {})
        
        if platform not in required:
            return False
        
        # Platform-specific permission request
        if platform == Platform.MACOS:
            return PermissionManager._request_macos_permission(required[platform])
        elif platform == Platform.WINDOWS:
            return True  # Windows typically doesn't require explicit permission
        elif platform == Platform.LINUX:
            return PermissionManager._check_linux_capability(required[platform])
        
        return False
```

---

## Performance Optimization

### Lazy Loading
```python
class LazyPlatformModule:
    """
    Lazy load platform-specific modules
    CLAUDE.md #1.5: Performance optimization
    """
    def __init__(self, module_name: str):
        self.module_name = module_name
        self._module = None
    
    def __getattr__(self, name):
        if self._module is None:
            try:
                self._module = importlib.import_module(self.module_name)
            except ImportError:
                raise AttributeError(f"Module {self.module_name} not available")
        return getattr(self._module, name)
```

---

## Implementation Priority

### Phase 1: Core Platform Support (1-2 days)
1. Platform detection service
2. Native file picker implementations
3. Integration with existing FilePropertyInput

### Phase 2: Eyedropper Tool (2-3 days)
1. Screen capture service
2. Eyedropper UI and interaction
3. Permission handling

### Phase 3: Animation Editor (3-4 days)
1. Timeline UI component
2. Keyframe management
3. Animation preview
4. Export/import functionality

### Total Estimated Time: 6-9 days

---

## Success Metrics

- Platform detection accuracy: 100%
- Graceful fallback rate: 100%
- Permission request success rate: Track per platform
- Animation editor performance: 60 FPS preview
- User satisfaction: Power user feature adoption

---

## Technical Debt Management

- Abstract platform-specific code into separate modules
- Create comprehensive platform compatibility matrix
- Document permission requirements clearly
- Plan for future platform support (mobile, etc.)