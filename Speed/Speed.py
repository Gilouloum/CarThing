import tkinter as tk
from PIL import Image, ImageTk

class SpeedLimitApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speed Limit")
        self.root.geometry("600x600")

        self.current_speed = 60  # Start speed for demonstration

        # Default colors
        self.text_color = 'red'

        # Define the path to the images
        base_path = r"C:\Users\yanni\Documents\Auto\FlipWatch\Speed"

        # Load and resize the car image
        self.car_image = Image.open(f"{base_path}\\miata.png").resize((300, 150), Image.Resampling.LANCZOS).convert('RGBA')
        self.car_image_tk = ImageTk.PhotoImage(self.car_image)

        # Load and process the background GIF, resizing each frame to 600x600
        self.bg_gif = Image.open(f"{base_path}\\background2.gif")
        self.gif_frames = []

        try:
            while True:
                frame = self.bg_gif.copy().convert('RGBA').resize((600, 600), Image.Resampling.LANCZOS)
                self.gif_frames.append(ImageTk.PhotoImage(frame))
                self.bg_gif.seek(self.bg_gif.tell() + 1)
        except EOFError:
            pass  # End of GIF

        self.current_frame = 0

        # Create the main frame to hold content
        self.frame = tk.Frame(self.root)
        self.frame.pack(expand=True, fill='both')

        # Create a Canvas for the background GIF
        self.canvas = tk.Canvas(self.frame, bg='white', width=600, height=600)
        self.canvas.pack(fill='both', expand=True)

        # Add the resized background GIF to the Canvas
        self.bg_image_id = self.canvas.create_image(0, 0, anchor='nw', image=self.gif_frames[0])

        # Add car image to the Canvas
        self.car_image_id = self.canvas.create_image(150, 430, anchor='nw', image=self.car_image_tk)

        # Add speed text to the Canvas with a cool font and in red color
        self.speed_text_id = self.canvas.create_text(
            300, 550,  # Positioned near the bottom
            text=f"Speed: {self.current_speed} km/h",
            font=('Arial', 24, 'bold'),  # Cool font, size 24, bold
            fill=self.text_color
        )

        # Start updating the display
        self.update_display()

    def update_display(self):
        # Update GIF frame
        self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
        self.canvas.itemconfig(self.bg_image_id, image=self.gif_frames[self.current_frame])

        # Update speed display
        self.canvas.itemconfig(self.speed_text_id, text=f" {self.current_speed} km/h")

        # Simulate speed change for demonstration
        self.current_speed = (self.current_speed + 1) % 121  # Cycle speed from 0 to 120

        # Update the display every 100 milliseconds (for animation and other dynamic updates)
        self.after_id = self.root.after(100, self.update_display)

    def on_closing(self):
        # Cancel any pending updates before closing
        if hasattr(self, 'after_id'):
            self.root.after_cancel(self.after_id)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SpeedLimitApp(root)
    root.mainloop()
