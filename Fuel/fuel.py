import tkinter as tk
from PIL import Image, ImageTk, ImageEnhance

class CarGadgetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Car Gadget")
        self.root.geometry("600x600")

        self.screen_mode = "fuel"  # Start in Fuel mode for demonstration
        self.fuel_percentage = 100

        # Default colors
        self.text_color = 'black'

        # Define the path to the images
        base_path = r"C:\Users\yanni\Documents\Auto\FlipWatch\Fuel"

        # Load and resize images
        self.miata_image = Image.open(f"{base_path}\\miata.png").resize((400, 400), Image.Resampling.LANCZOS).convert('RGBA')
        self.car_image = ImageTk.PhotoImage(self.miata_image)

        # Load and rotate drink images to add tilt effect
        self.drink_images = []
        for i in range(1, 8):
            drink_image = Image.open(f"{base_path}\\drink{i}.png").resize((200, 200), Image.Resampling.LANCZOS).convert('RGBA')
            tilted_image = drink_image.rotate(25, expand=True)  # Tilt the image by -15 degrees
            self.drink_images.append(ImageTk.PhotoImage(tilted_image))

        # Load and process the background GIF
        self.bg_gif = Image.open(f"{base_path}\\backgroundfull.gif")
        self.gif_frames = [ImageTk.PhotoImage(self.bg_gif.copy().convert('RGBA'))]

        try:
            while True:
                self.bg_gif.seek(self.bg_gif.tell() + 1)
                self.gif_frames.append(ImageTk.PhotoImage(self.bg_gif.copy().convert('RGBA')))
        except EOFError:
            pass  # End of GIF

        self.current_frame = 0

        # Create the main frame to hold content
        self.frame = tk.Frame(self.root)
        self.frame.pack(expand=True, fill='both')

        # Create a Canvas for the background GIF
        self.canvas = tk.Canvas(self.frame, bg='white', width=600, height=400)
        self.canvas.pack(fill='both', expand=True)

        # Add the background GIF to the Canvas
        self.bg_image_id = self.canvas.create_image(0, 0, anchor='nw', image=self.gif_frames[0])

        # Add car image to the Canvas
        self.car_image_id = self.canvas.create_image(20, 240, anchor='nw', image=self.car_image)

        # Add drink image to the Canvas
        self.drink_image_id = self.canvas.create_image(280, 370, anchor='nw', image=self.drink_images[0])

        # Add fuel percentage text to the Canvas with a cooler font and thicker appearance
        self.fuel_text_id = self.canvas.create_text(
            300, 580,  # Adjusted y-coordinate for better position
            text=f"Fuel: {self.fuel_percentage:.1f}%",
            font=('Arial', 24, 'bold'),  # Changed font to Arial, size 24, and made it bold
            fill=self.text_color
        )

        # Start updating the display
        self.update_display()

    def update_display(self):
        # Update GIF frame
        self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
        self.canvas.itemconfig(self.bg_image_id, image=self.gif_frames[self.current_frame])

        # Update drink image based on fuel level
        fuel_images_index = self.get_fuel_image_index()
        self.canvas.itemconfig(self.drink_image_id, image=self.drink_images[fuel_images_index])

        # Update fuel percentage display
        self.canvas.itemconfig(self.fuel_text_id, text=f"Fuel: {self.fuel_percentage:.1f}%")

        # Simulate fuel decrease for demonstration
        self.fuel_percentage = max(0, self.fuel_percentage - 0.1)

        # Update the display every 100 milliseconds (for animation and other dynamic updates)
        self.after_id = self.root.after(100, self.update_display)

    def get_fuel_image_index(self):
        """Returns the index of the drink image to display based on the current fuel percentage."""
        if self.fuel_percentage > 80:
            return 0
        elif self.fuel_percentage > 65:
            return 1
        elif self.fuel_percentage > 50:
            return 2
        elif self.fuel_percentage > 35:
            return 3
        elif self.fuel_percentage > 20:
            return 4
        elif self.fuel_percentage > 5:
            return 5
        else:
            return 6

    def on_closing(self):
        # Cancel any pending updates before closing
        if hasattr(self, 'after_id'):
            self.root.after_cancel(self.after_id)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CarGadgetApp(root)
    root.mainloop()
