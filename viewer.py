#!/usr/bin/env python3

import tkinter as tk
import os
import signal
import sys
import cairosvg
from PIL import Image, ImageTk
import threading
import evdev
import select

class KeyboardLayerPopup:
    def __init__(self, svg_path):
        # SVG and popup management
        self.svg_path = svg_path
        self.popup = None
        self.popup_visible = False
        
        # Keyboard event tracking
        self.keyboard_devices = []
        self.find_keyboard_devices()
        
        # Threading for keyboard monitoring
        self.stop_event = threading.Event()
        self.keyboard_thread = threading.Thread(
            target=self.monitor_keyboard, 
            daemon=True
        )
        
        # Signal handling
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

    def find_keyboard_devices(self):
        """Find all keyboard input devices"""
        for path in evdev.list_devices():
            device = evdev.InputDevice(path)
            if evdev.ecodes.EV_KEY in device.capabilities():
                print(f"Found keyboard device: {device.name}")
                self.keyboard_devices.append(device)

    def convert_svg_to_png(self):
        """Convert SVG to PNG using cairosvg"""
        png_path = self.svg_path.replace('.svg', '.png')
        
        try:
            with open(self.svg_path, 'rb') as svg_file:
                cairosvg.svg2png(
                    file_obj=svg_file, 
                    write_to=png_path,
                    output_width=400,
                    output_height=300
                )
            return png_path
        except Exception as e:
            print(f"Error converting SVG: {e}")
            return None

    def show_popup(self):
        """Display popup with SVG image"""
        # Prevent multiple popups
        if self.popup_visible:
            return

        # Create popup in main thread
        def create_popup():
            root = tk.Tk()
            root.title("Keyboard Layer Popup")
            
            # Frameless and always on top
            root.overrideredirect(True)
            root.attributes('-topmost', True)
            
            # Popup dimensions
            popup_width = 400
            popup_height = 300
            margin_bottom = 50
            
            # Position popup (centered bottom)
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            
            x = (screen_width - popup_width) // 2
            y = screen_height - popup_height - margin_bottom
            
            root.geometry(f'{popup_width}x{popup_height}+{x}+{y}')
            
            # Convert SVG to PNG
            png_path = self.convert_svg_to_png()
            
            if png_path and os.path.exists(png_path):
                # Load image with Pillow and convert to PhotoImage
                pil_img = Image.open(png_path)
                img = ImageTk.PhotoImage(pil_img)
                
                # Create label with image
                label = tk.Label(root, image=img)
                label.image = img  # Keep a reference
                label.pack(fill=tk.BOTH, expand=True)
                
                # Store reference and set visibility
                self.popup = root
                self.popup_visible = True
                
                # Auto-close after 3 seconds
                root.after(3000, self.hide_popup)
                
                # Start the Tkinter event loop
                root.mainloop()
            else:
                print("Could not load SVG image")

        # Run popup creation in main thread
        self.popup_visible = False
        create_popup()

    def hide_popup(self):
        """Hide the popup"""
        if self.popup:
            self.popup.destroy()
            self.popup = None
            self.popup_visible = False

    def monitor_keyboard(self):
        """Monitor keyboard events"""
        while not self.stop_event.is_set():
            # Use select to wait for keyboard events with timeout
            readable, _, _ = select.select(
                self.keyboard_devices, [], [], 0.1
            )
            
            for device in readable:
                # Read events from the device
                for event in device.read():
                    # Hide popup on any key press
                    if event.type == evdev.ecodes.EV_KEY and event.value == 1:
                        # Ensure we run hide_popup in the main thread
                        if self.popup:
                            self.popup.after(0, self.hide_popup)
                        return

    def start(self):
        """Start monitoring keyboard"""
        if not self.keyboard_devices:
            print("No keyboard devices found!")
            return

        # Start keyboard monitoring thread
        self.keyboard_thread.start()

        # For testing - show popup
        self.show_popup()

    def cleanup(self, signum=None, frame=None):
        """Clean up resources on exit"""
        self.stop_event.set()
        if self.popup:
            self.popup.destroy()
        sys.exit(0)

def main():
    # Specify the path to your SVG file
    svg_path = os.path.expanduser('~/keyboard_layers/layer_example.svg')
    
    # Ensure SVG directory exists
    os.makedirs(os.path.dirname(svg_path), exist_ok=True)
    
    # Create a sample SVG if it doesn't exist
    if not os.path.exists(svg_path):
        sample_svg = '''
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300">
            <rect width="400" height="300" fill="#f0f0f0"/>
            <text x="50%" y="50%" text-anchor="middle" font-size="20" fill="black">
                Keyboard Layer Popup
            </text>
        </svg>
        '''
        with open(svg_path, 'w') as f:
            f.write(sample_svg)
    
    # Create and start popup manager
    popup_manager = KeyboardLayerPopup(svg_path)
    popup_manager.start()

if __name__ == '__main__':
    main()
