import tkinter as tk
from PIL import Image, ImageTk
import serial  # For serial communication with the GPS device
import pynmea2  # For parsing NMEA sentences from GPS
import threading
import time

class GPSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GPS Tracker")
        self.root.geometry("600x600")
        
        # Default colors
        self.text_color = 'black'
        
        # Initialize GPS variables
        self.latitude = None
        self.longitude = None
        
        # Set up serial connection (adjust port and baud rate as needed)
        self.gps_serial = serial.Serial('/dev/ttyS0', baudrate=9600, timeout=1)
        
        # Load and process background image (or GIF)
        self.bg_image = Image.open("path/to/your/background_image.png").resize((600, 600))
        self.bg_image_tk = ImageTk.PhotoImage(self.bg_image)
        
        # Create the main frame to hold content
        self.frame = tk.Frame(self.root)
        self.frame.pack(expand=True, fill='both')
        
        # Create a Canvas for the background image
        self.canvas = tk.Canvas(self.frame, bg='white', width=600, height=600)
        self.canvas.pack(fill='both', expand=True)
        
        # Add the background image to the Canvas
        self.bg_image_id = self.canvas.create_image(0, 0, anchor='nw', image=self.bg_image_tk)
        
        # Add GPS coordinates text to the Canvas
        self.gps_text_id = self.canvas.create_text(
            300, 580,  # Positioned near the bottom
            text="Waiting for GPS data...",
            font=('Arial', 24, 'bold'),
            fill=self.text_color
        )
        
        # Start the GPS reading thread
        self.gps_thread = threading.Thread(target=self.read_gps_data)
        self.gps_thread.daemon = True
        self.gps_thread.start()
        
        # Update the display
        self.update_display()

    def read_gps_data(self):
        while True:
            try:
                line = self.gps_serial.readline().decode('ascii', errors='replace')
                if line.startswith('$GNRMC'):  # Use your relevant NMEA sentence
                    msg = pynmea2.parse(line)
                    self.latitude = msg.latitude
                    self.longitude = msg.longitude
            except Exception as e:
                print(f"Error reading GPS data: {e}")
            time.sleep(1)

    def update_display(self):
        if self.latitude and self.longitude:
            self.canvas.itemconfig(self.gps_text_id, text=f"Lat: {self.latitude:.6f} Lon: {self.longitude:.6f}")
        else:
            self.canvas.itemconfig(self.gps_text_id, text="Waiting for GPS data...")
        
        # Update the display every 1000 milliseconds (1 second)
        self.root.after(1000, self.update_display)

if __name__ == "__main__":
    root = tk.Tk()
    app = GPSApp(root)
    root.mainloop()
