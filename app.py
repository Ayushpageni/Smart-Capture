import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageGrab
import threading
import time
import os
import sys
import platform
from datetime import datetime

# Platform-specific imports for window capture
if platform.system() == "Windows":
    try:
        import pygetwindow as gw
        import pyautogui
        WINDOWS_CAPTURE = True
    except ImportError:
        WINDOWS_CAPTURE = False
elif platform.system() == "Darwin":  # macOS
    try:
        import Quartz
        from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
        MACOS_CAPTURE = True
    except ImportError:
        MACOS_CAPTURE = False
else:  # Linux
    try:
        import subprocess
        LINUX_CAPTURE = True
    except ImportError:
        LINUX_CAPTURE = False

class PhoneCameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Phone Camera Capture")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Camera variables
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.captured_frame = None
        
        # Default camera source (can be changed)
        self.camera_source = 0  # Default to first USB camera
        
        # Create output directory
        self.output_dir = "Captured_Images"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for responsiveness
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Camera source input section
        source_frame = ttk.LabelFrame(main_frame, text="Camera Source", padding="5")
        source_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        source_frame.columnconfigure(2, weight=1)
        
        # Connection type selection
        self.connection_type = tk.StringVar(value="usb")
        
        ttk.Radiobutton(source_frame, text="USB Camera", variable=self.connection_type, 
                       value="usb", command=self.on_connection_type_change).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Radiobutton(source_frame, text="IP Camera", variable=self.connection_type, 
                       value="ip", command=self.on_connection_type_change).grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        ttk.Radiobutton(source_frame, text="Screen Capture", variable=self.connection_type, 
                       value="screen", command=self.on_connection_type_change).grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        
        # USB camera selection
        self.usb_frame = ttk.Frame(source_frame)
        self.usb_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(5, 0))
        self.usb_frame.columnconfigure(1, weight=1)
        
        ttk.Label(self.usb_frame, text="USB Camera:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.usb_var = tk.StringVar(value="0")
        self.usb_combo = ttk.Combobox(self.usb_frame, textvariable=self.usb_var, 
                                     values=["0", "1", "2", "3"], width=5, state="readonly")
        self.usb_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 5))
        
        self.detect_btn = ttk.Button(self.usb_frame, text="Detect Cameras", command=self.detect_cameras)
        self.detect_btn.grid(row=0, column=2, padx=(5, 0))
        
        # IP camera input
        self.ip_frame = ttk.Frame(source_frame)
        self.ip_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(5, 0))
        self.ip_frame.columnconfigure(1, weight=1)
        
        ttk.Label(self.ip_frame, text="Camera URL:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.url_var = tk.StringVar(value="http://192.168.1.100:8080/video")
        self.url_entry = ttk.Entry(self.ip_frame, textvariable=self.url_var, width=40)
        self.url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # Screen capture input
        self.screen_frame = ttk.Frame(source_frame)
        self.screen_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(5, 0))
        self.screen_frame.columnconfigure(1, weight=1)
        
        ttk.Label(self.screen_frame, text="Window:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.window_var = tk.StringVar()
        self.window_combo = ttk.Combobox(self.screen_frame, textvariable=self.window_var, 
                                        width=50, state="readonly")
        self.window_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        self.refresh_windows_btn = ttk.Button(self.screen_frame, text="Refresh Windows", 
                                            command=self.refresh_windows)
        self.refresh_windows_btn.grid(row=0, column=2, padx=(5, 0))
        
        # Connect button
        self.connect_btn = ttk.Button(source_frame, text="Connect", command=self.toggle_camera)
        self.connect_btn.grid(row=4, column=0, columnspan=4, pady=(10, 0))
        
        # Initialize UI state
        self.on_connection_type_change()
        
        # Initialize window list for screen capture
        self.window_list = []
        if self.connection_type.get() == "screen":
            self.refresh_windows()
        
        # Video preview area
        self.video_frame = ttk.LabelFrame(main_frame, text="Live Preview", padding="5")
        self.video_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        self.video_frame.columnconfigure(0, weight=1)
        self.video_frame.rowconfigure(0, weight=1)
        
        # Video label (will contain the camera feed)
        self.video_label = ttk.Label(self.video_frame, text="Click 'Connect' to start camera feed", 
                                   background="black", foreground="white")
        self.video_label.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Capture Controls", padding="10")
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(1, weight=1)
        
        # Filename input
        ttk.Label(control_frame, text="Filename:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.filename_var = tk.StringVar()
        self.filename_entry = ttk.Entry(control_frame, textvariable=self.filename_var, width=30)
        self.filename_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Buttons frame
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        self.capture_btn = ttk.Button(btn_frame, text="Capture", command=self.capture_frame, state="disabled")
        self.capture_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.save_btn = ttk.Button(btn_frame, text="Save", command=self.save_image, state="disabled")
        self.save_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.browse_btn = ttk.Button(btn_frame, text="Browse Save Location", command=self.browse_save_location)
        self.browse_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Enter camera URL and click Connect")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_connection_type_change(self):
        """Handle connection type radio button changes"""
        connection = self.connection_type.get()
        
        if connection == "usb":
            # Show USB controls, hide others
            for child in self.usb_frame.winfo_children():
                child.configure(state="normal")
            for child in self.ip_frame.winfo_children():
                child.configure(state="disabled")
            for child in self.screen_frame.winfo_children():
                child.configure(state="disabled")
        elif connection == "ip":
            # Show IP controls, hide others
            for child in self.usb_frame.winfo_children():
                child.configure(state="disabled")
            for child in self.ip_frame.winfo_children():
                child.configure(state="normal")
            for child in self.screen_frame.winfo_children():
                child.configure(state="disabled")
        else:  # screen
            # Show screen controls, hide others
            for child in self.usb_frame.winfo_children():
                child.configure(state="disabled")
            for child in self.ip_frame.winfo_children():
                child.configure(state="disabled")
            for child in self.screen_frame.winfo_children():
                child.configure(state="normal")
            self.refresh_windows()
    
    def detect_cameras(self):
        """Detect available USB cameras"""
        self.status_var.set("Detecting cameras...")
        self.root.update()
        
        available_cameras = []
        for i in range(10):  # Check first 10 camera indices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available_cameras.append(str(i))
                cap.release()
        
        if available_cameras:
            self.usb_combo['values'] = available_cameras
            self.usb_var.set(available_cameras[0])
            self.status_var.set(f"Found cameras: {', '.join(available_cameras)}")
        else:
            self.status_var.set("No USB cameras detected")
            messagebox.showinfo("Detection Result", "No USB cameras found. Make sure your phone is connected via USB and USB debugging/camera access is enabled.")
    
    def get_windows_list(self):
        """Get list of open windows based on platform"""
        windows = []
        
        try:
            if platform.system() == "Windows" and WINDOWS_CAPTURE:
                # Windows implementation
                all_windows = gw.getAllWindows()
                for window in all_windows:
                    if window.title and window.title.strip() and window.visible:
                        windows.append({
                            'title': window.title,
                            'id': window._hWnd,
                            'bbox': (window.left, window.top, window.width, window.height)
                        })
            
            elif platform.system() == "Darwin" and MACOS_CAPTURE:
                # macOS implementation
                window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
                for window in window_list:
                    title = window.get('kCGWindowName', '')
                    owner = window.get('kCGWindowOwnerName', '')
                    if title and title.strip():
                        windows.append({
                            'title': f"{owner} - {title}",
                            'id': window['kCGWindowNumber'],
                            'bbox': window.get('kCGWindowBounds', {})
                        })
            
            else:
                # Linux/fallback - add full screen option
                windows.append({
                    'title': 'Full Screen',
                    'id': 'fullscreen',
                    'bbox': None
                })
                
        except Exception as e:
            print(f"Error getting windows: {e}")
            # Fallback to full screen
            windows.append({
                'title': 'Full Screen',
                'id': 'fullscreen',
                'bbox': None
            })
        
        return windows
    
    def refresh_windows(self):
        """Refresh the list of available windows"""
        if self.connection_type.get() != "screen":
            return
            
        self.status_var.set("Refreshing window list...")
        self.root.update()
        
        self.window_list = self.get_windows_list()
        
        if self.window_list:
            window_titles = [w['title'] for w in self.window_list]
            self.window_combo['values'] = window_titles
            if window_titles:
                self.window_var.set(window_titles[0])
            self.status_var.set(f"Found {len(window_titles)} windows")
        else:
            self.window_combo['values'] = ["No windows found"]
            self.status_var.set("No windows found")
    
    def capture_window(self, window_info):
        """Capture a specific window or full screen"""
        try:
            if window_info['id'] == 'fullscreen':
                # Capture full screen
                screenshot = ImageGrab.grab()
            elif platform.system() == "Windows" and WINDOWS_CAPTURE:
                # Windows specific window capture
                import pyautogui
                bbox = window_info['bbox']
                screenshot = pyautogui.screenshot(region=(bbox[0], bbox[1], bbox[2], bbox[3]))
            elif platform.system() == "Darwin" and MACOS_CAPTURE:
                # macOS specific window capture would go here
                screenshot = ImageGrab.grab()  # Fallback to full screen for now
            else:
                # Fallback to full screen
                screenshot = ImageGrab.grab()
            
            # Convert PIL image to OpenCV format
            cv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            return cv_image
            
        except Exception as e:
            print(f"Error capturing window: {e}")
            return None
        
    def toggle_camera(self):
        if not self.is_running:
            self.start_camera()
        else:
            self.stop_camera()
    
    def start_camera(self):
        try:
            self.status_var.set("Connecting...")
            self.root.update()
            
            # Get camera source based on connection type
            if self.connection_type.get() == "usb":
                camera_source = int(self.usb_var.get())
                self.status_var.set(f"Connecting to USB camera {camera_source}...")
            elif self.connection_type.get() == "ip":
                camera_source = self.url_var.get().strip()
                if not camera_source:
                    messagebox.showerror("Error", "Please enter a valid camera URL")
                    return
                self.status_var.set("Connecting to IP camera...")
            else:  # screen capture
                if not self.window_list:
                    messagebox.showerror("Error", "No windows available. Please refresh the window list.")
                    return
                self.status_var.set("Starting screen capture...")
            
            self.root.update()
            
            # Handle screen capture differently
            if self.connection_type.get() == "screen":
                # No camera object needed for screen capture
                self.cap = None
                self.is_running = True
                self.connect_btn.config(text="Disconnect")
                self.capture_btn.config(state="normal")
                
                # Disable source selection while connected
                for child in self.screen_frame.winfo_children():
                    child.configure(state="disabled")
                
                # Start screen capture thread
                self.video_thread = threading.Thread(target=self.update_screen_capture, daemon=True)
                self.video_thread.start()
                
                selected_window = self.window_var.get()
                self.status_var.set(f"Screen capture active: {selected_window}")
                return
            
            # Regular camera setup
            self.cap = cv2.VideoCapture(camera_source)
            
            # Set camera properties for better performance (USB cameras)
            if self.connection_type.get() == "usb":
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for lower latency
            
            # Test if camera is accessible
            ret, frame = self.cap.read()
            if not ret:
                raise Exception("Cannot read from camera")
            
            self.is_running = True
            self.connect_btn.config(text="Disconnect")
            self.capture_btn.config(state="normal")
            
            # Disable source selection while connected
            for child in self.usb_frame.winfo_children():
                child.configure(state="disabled")
            for child in self.ip_frame.winfo_children():
                child.configure(state="disabled")
            
            # Start video thread
            self.video_thread = threading.Thread(target=self.update_video, daemon=True)
            self.video_thread.start()
            
            if self.connection_type.get() == "usb":
                self.status_var.set(f"Connected to USB camera {camera_source}")
            else:
                self.status_var.set(f"Connected to: {camera_source}")
            
        except Exception as e:
            self.status_var.set(f"Connection failed: {str(e)}")
            messagebox.showerror("Connection Error", f"Failed to connect:\n{str(e)}")
            if self.cap:
                self.cap.release()
    
    def stop_camera(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        
        self.connect_btn.config(text="Connect")
        self.capture_btn.config(state="disabled")
        self.save_btn.config(state="disabled")
        
        # Re-enable source selection
        self.on_connection_type_change()
        
        # Clear video display
        self.video_label.config(image="", text="Camera disconnected")
        self.status_var.set("Camera disconnected")
    
    def update_video(self):
        while self.is_running and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if ret:
                    self.current_frame = frame.copy()
                    
                    # Resize frame to fit the display area
                    display_frame = self.resize_frame_for_display(frame)
                    
                    # Convert BGR to RGB
                    rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                    
                    # Convert to PIL Image and then to PhotoImage
                    pil_image = Image.fromarray(rgb_frame)
                    photo = ImageTk.PhotoImage(pil_image)
                    
                    # Update the label with the new frame
                    self.video_label.config(image=photo, text="")
                    self.video_label.image = photo  # Keep a reference
                    
                else:
                    break
                    
            except Exception as e:
                print(f"Error in video update: {e}")
                break
            
            time.sleep(0.016)  # ~60 FPS for USB, lower latency
        
        # Cleanup when thread ends
        if self.is_running:
            self.root.after(0, self.stop_camera)
    
    def update_screen_capture(self):
        """Update screen capture preview"""
        while self.is_running:
            try:
                # Get selected window info
                selected_title = self.window_var.get()
                window_info = None
                for w in self.window_list:
                    if w['title'] == selected_title:
                        window_info = w
                        break
                
                if window_info:
                    # Capture the window
                    frame = self.capture_window(window_info)
                    if frame is not None:
                        self.current_frame = frame.copy()
                        
                        # Resize frame to fit the display area
                        display_frame = self.resize_frame_for_display(frame)
                        
                        # Convert BGR to RGB
                        rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                        
                        # Convert to PIL Image and then to PhotoImage
                        pil_image = Image.fromarray(rgb_frame)
                        photo = ImageTk.PhotoImage(pil_image)
                        
                        # Update the label with the new frame
                        self.video_label.config(image=photo, text="")
                        self.video_label.image = photo  # Keep a reference
                    
            except Exception as e:
                print(f"Error in screen capture update: {e}")
                break
            
            time.sleep(0.1)  # 10 FPS for screen capture (less intensive)
        
        # Cleanup when thread ends
        if self.is_running:
            self.root.after(0, self.stop_camera)
    
    def resize_frame_for_display(self, frame):
        # Get the current size of the video frame widget
        self.root.update_idletasks()
        
        # Get widget dimensions (with some padding)
        widget_width = max(640, self.video_frame.winfo_width() - 20)
        widget_height = max(480, self.video_frame.winfo_height() - 40)
        
        # Get frame dimensions
        frame_height, frame_width = frame.shape[:2]
        
        # Calculate scaling factor to maintain aspect ratio
        scale_width = widget_width / frame_width
        scale_height = widget_height / frame_height
        scale = min(scale_width, scale_height)
        
        # Calculate new dimensions
        new_width = int(frame_width * scale)
        new_height = int(frame_height * scale)
        
        # Resize frame
        resized_frame = cv2.resize(frame, (new_width, new_height))
        return resized_frame
    
    def capture_frame(self):
        if self.connection_type.get() == "screen":
            # For screen capture, take a fresh screenshot
            selected_title = self.window_var.get()
            window_info = None
            for w in self.window_list:
                if w['title'] == selected_title:
                    window_info = w
                    break
            
            if window_info:
                self.captured_frame = self.capture_window(window_info)
                if self.captured_frame is not None:
                    self.save_btn.config(state="normal")
                    self.status_var.set("Window captured! Enter filename and click Save")
                    
                    # Flash effect
                    self.video_label.config(background="white")
                    self.root.after(100, lambda: self.video_label.config(background=self.root.cget('bg')))
                else:
                    messagebox.showwarning("Warning", "Failed to capture window")
            else:
                messagebox.showwarning("Warning", "No window selected")
        else:
            # Regular camera capture
            if self.current_frame is not None:
                self.captured_frame = self.current_frame.copy()
                self.save_btn.config(state="normal")
                self.status_var.set("Frame captured! Enter filename and click Save")
                
                # Flash effect
                self.video_label.config(background="white")
                self.root.after(100, lambda: self.video_label.config(background=self.root.cget('bg')))
            else:
                messagebox.showwarning("Warning", "No frame available to capture")
    
    def save_image(self):
        if self.captured_frame is None:
            messagebox.showwarning("Warning", "No frame captured yet")
            return
        
        # Get filename
        filename = self.filename_var.get().strip()
        if not filename:
            # Generate timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}"
        
        # Ensure .jpg extension
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            filename += '.jpg'
        
        # Full path
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # Save the image
            cv2.imwrite(filepath, self.captured_frame)
            self.status_var.set(f"Image saved: {filepath}")
            messagebox.showinfo("Success", f"Image saved successfully:\n{filepath}")
            
            # Clear the filename entry for next capture
            self.filename_var.set("")
            self.save_btn.config(state="disabled")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save image:\n{str(e)}")
    
    def browse_save_location(self):
        new_dir = filedialog.askdirectory(title="Select Save Location", initialdir=self.output_dir)
        if new_dir:
            self.output_dir = new_dir
            self.status_var.set(f"Save location: {self.output_dir}")
    
    def on_closing(self):
        self.stop_camera()
        self.root.destroy()

def main():
    # Check if required packages are available
    try:
        import cv2
        import PIL
    except ImportError as e:
        print("Missing required packages. Please install them using:")
        print("pip install opencv-python pillow")
        return
    
    # Check for optional screen capture packages
    missing_packages = []
    if platform.system() == "Windows":
        try:
            import pygetwindow
            import pyautogui
        except ImportError:
            missing_packages.extend(["pygetwindow", "pyautogui"])
    elif platform.system() == "Darwin":  # macOS
        try:
            import Quartz
        except ImportError:
            missing_packages.append("pyobjc-framework-Quartz")
    
    if missing_packages:
        print(f"Optional packages for enhanced screen capture: {', '.join(missing_packages)}")
        print(f"Install with: pip install {' '.join(missing_packages)}")
        print("Basic screen capture will still work without these packages.\n")
    
    root = tk.Tk()
    app = PhoneCameraApp(root)
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()