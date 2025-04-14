import tkinter as tk
from PIL import Image, ImageTk, ImageOps
import random
import time
import obd  # Adding the OBD2 library
import os
import threading
from obd_simulator import OBDSimulator, OBDSimulatorGUI
import random


class CarGadgetApp:
    def __init__(self, root):

        self.root = root
        self.root.title("Car Gadget")
        self.root.geometry("450x450")
        self.canvas = tk.Canvas(self.root, width=450, height=450, bg='white')
        self.canvas.pack()

        # Initialize menu to cover the entire screen
        self.menu = tk.Frame(self.root, width=450, height=450, bg='black')
        self.menu.place(x=0, y=-450)  # Place the menu off-screen initially

        # Set button width based on available space (350px for buttons)
        button_width = 350

        # Make the "Start Simulation" button larger and centered with a 50px border
        self.start_simulation_button = tk.Button(self.menu, text="Start Simulation", command=self.toggle_simulation,
                                                bg='black', fg='white', font=('Arial', 18, 'bold'),
                                                height=3, width=int(button_width / 10))  # Adjust the width
        self.start_simulation_button.place(relx=0.5, rely=0.3, anchor='center')  # Center the button in the menu

        # Add the "Error" button for error checking, larger and centered with a 50px border
        self.error_button = tk.Button(self.menu, text="Errors", command=self.show_error_page,
                                    bg='black', fg='white', font=('Arial', 18, 'bold'),
                                    height=3, width=int(button_width / 10))  # Adjust the width
        self.error_button.place(relx=0.5, rely=0.5, anchor='center')  # Center the button

        # Add the "Close App" button, larger and centered with a 50px border
        self.close_app_button = tk.Button(self.menu, text="Close App", command=self.close_app,
                                        bg='black', fg='white', font=('Arial', 18, 'bold'),
                                        height=3, width=int(button_width / 10))  # Adjust the width
        self.close_app_button.place(relx=0.5, rely=0.7, anchor='center')  # Center the button

        # Initialize swipe detection variables
        self.start_y = None
        self.swipe_threshold = 50
        self.menu_visible = False

        # Initialize the loading_complete attribute
        self.loading_complete = False

        # Initialize simulation variables
        self.current_speed = 0
        self.current_rpm = 0
        self.fuel_percentage = 100
        self.simulation_running = False
        self.transition_playing = False  # Track if the transition GIF is playing
        self.transition_finished = False  # Track if transition is done
        self.miata21_playing = False
        self.reverse_transition_playing = False  # Track reverse transition
        self.reverse_transition_finished = False  # Track if reverse transition is done

        # Initialize frame counters
        self.current_frame_intro = 0
        self.current_frame_speed = 0
        self.current_frame_rpm = 0
        self.current_frame_fuel = 0

        # Bind swipe
        self.root.bind("<Button-1>", self.on_click)
        self.root.bind("<B1-Motion>", self.on_swipe)
        self.root.bind("<ButtonRelease-1>", self.on_swipe_end)

        # Initialize the intro GIF and start it immediately
        self.setup_intro_gif()
        self.play_intro()

        self.total_distance = 0.0  # Total distance in kilometers
        self.last_time = time.time()  # Track the last update time

        # OBD2 setup
        self.use_obd2 = False  # Flag to switch between OBD2 and simulation
        self.connection = None  # OBD2 connection initialization

        # Run heavy initialization in a separate thread
        threading.Thread(target=self.deferred_initialization, daemon=True).start()

        # Arrow speed
        self.speed_increment = 1
        self.rpm_increment = 100
        self.max_speed = 180
        self.max_rpm = 7000
        self.min_speed = -20
        self.min_rpm = 0

        # Initialize speed direction and rpm direction
        self.speed_direction = 0
        self.rpm_direction = 0
        self.gif_frames_race = []
        self.update_display()

        # Initialize the OBD simulator
        self.obd_simulator = OBDSimulator()
        self.simulator_gui = None
    


    def update_animation(self):
        self.update_display()
        self.root.after(100, self.update_animation)  # Refresh every 100ms



    def stop_animations(self):
     """Stops background and Miata animation when speed is zero."""
     self.canvas.itemconfig(self.car_image_speed_id, image=self.miata_gif_frames_speed[0])  # Keep first frame
     self.root.after_cancel(self.update_background)  # Stop background updates

    def reverse_animations(self):
      """Reverses background and Miata animation to simulate reversing."""
      self.current_frame_speed = (self.current_frame_speed - 1) % len(self.gif_frames_speed)
      self.canvas.itemconfig(self.speed_image_id, image=self.gif_frames_speed[self.current_frame_speed])

      self.current_frame_miata_speed = (self.current_frame_miata_speed - 1) % len(self.miata_gif_frames_speed)
      self.canvas.itemconfig(self.car_image_speed_id, image=self.miata_gif_frames_speed[self.current_frame_miata_speed])

      self.root.after(100, self.reverse_animations)  # Keep reversing

    def resume_animations(self):
     """Resumes normal animation speed when moving forward."""
     self.update_background()
     self.update_miata_gif()


    def start_simulation(self):
     self.update_animation()  # Replaces simulate_speed()




    def setup_obd2(self):
        if self.use_obd2:
            try:
                self.connection = obd.OBD("/dev/ttyUSB0")  # Connect to the car's OBD-II port
            except Exception as e:
                print(f"Failed to connect to OBD2: {e}")
                self.connection = None
        else:
            self.obd_simulator = OBDSimulator()  # Initialize the simulator


    def read_obd2_data(self):
     if self.use_obd2:
        if not self.connection or not self.connection.is_connected():
            print("OBD2 connection lost. Switching to simulation mode.")
            self.use_obd2 = False
            self.setup_obd2()
            return

        try:
            speed_cmd = obd.commands.SPEED
            rpm_cmd = obd.commands.RPM

            speed_response = self.connection.query(speed_cmd)
            rpm_response = self.connection.query(rpm_cmd)

            if not speed_response.is_null():
                self.current_speed = int(round(speed_response.value.to("km/h").magnitude))
            if not rpm_response.is_null():
                self.current_rpm = int(round(rpm_response.value.magnitude))

            print(f"OBD2 Speed: {self.current_speed} km/h, RPM: {self.current_rpm}")
        except Exception as e:
            print(f"Error reading OBD2 data: {e}")
     else:
        # Use simulated data
        data = self.obd_simulator.get_data()
        self.current_speed = int(round(data["speed"]))
        self.current_rpm = int(round(data["rpm"]))
        print(f"Simulated Speed: {self.current_speed} km/h, RPM: {self.current_rpm}")

     self.update_display()
     self.root.after(500, self.read_obd2_data)

    def toggle_obd2_mode(self):
     self.use_obd2 = not self.use_obd2
     self.setup_obd2()  # Reinitialize the connection or simulator
     if self.use_obd2:
        print("Switched to OBD2 mode.")
     else:
        print("Switched to simulation mode.")
     self.update_status_label()



    def update_status_label(self):
     status_text = "Simulation Mode" if not self.use_obd2 else "OBD-II Mode"
     self.status_label.config(text=status_text)
     self.status_label = tk.Label(self.root, text="Simulation Mode", font=("Arial", 14), fg="white", bg="black")
     self.status_label.pack(anchor="n")



    def deferred_initialization(self):
        # Perform resource-heavy tasks here
        self.setup_speed()
        self.setup_rpm()
        self.setup_fuel()
        self.setup_obd2()  # OBD2 setup

        # Automatically start OBD2 data fetching if connected
        if self.connection and self.connection.is_connected():
            self.use_obd2 = True
            print("OBD-II Connected")
            self.read_obd2_data()  # Start reading OBD2 data
        else:
            print("OBD-II Not Connected")

        # Mark loading as complete
        self.loading_complete = True


         

    def setup_intro_gif(self):
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))

     # Define the relative path to 'speed' folder
        base_path = os.path.join(script_dir, "Other")
        self.bg_gif_intro = Image.open(f"{base_path}/IntroV3.gif")
        self.gif_frames_intro = []

        try:
            while True:
                frame = self.bg_gif_intro.copy().convert('RGBA').resize((450, 450), Image.Resampling.LANCZOS)
                self.gif_frames_intro.append(ImageTk.PhotoImage(frame))
                self.bg_gif_intro.seek(self.bg_gif_intro.tell() + 1)
        except EOFError:
            pass  # End of GIF

        self.intro_image_id = self.canvas.create_image(0, 0, anchor='nw', image=self.gif_frames_intro[0])

    def play_intro(self):
        self.screen_mode = 0
        self.current_frame_intro = 0
        self.update_intro_gif()

    def update_intro_gif(self):
     if self.screen_mode == 0 and hasattr(self, 'gif_frames_intro') and self.gif_frames_intro:
        # Increment the current frame index
        if self.current_frame_intro < len(self.gif_frames_intro) - 1:
            self.current_frame_intro += 1

        # Update the canvas with the current frame
        self.canvas.itemconfig(self.intro_image_id, image=self.gif_frames_intro[self.current_frame_intro])

        # Check if the intro GIF has finished playing
        if self.current_frame_intro == len(self.gif_frames_intro) - 1:
            if self.loading_complete:
                # If loading is complete, transition to the next scene
                self.root.after(2000, self.show_speed)
            else:
                # Hold the last frame and keep checking for loading completion
                self.root.after(100, self.update_intro_gif)
        else:
            # Continue playing the next frame
            self.root.after(100, self.update_intro_gif)




    def setup_speed(self):
     script_dir = os.path.dirname(os.path.abspath(__file__))
     base_path = os.path.join(script_dir, "Speed")

     # Load Miata GIFs
     self.miata_gif_list = []
     for i in range(1, 7):
        gif_path = f"{base_path}/miata{i}.gif"
        miata_gif = Image.open(gif_path)
        frames = []
        try:
            while True:
                frame = miata_gif.copy().convert('RGBA').resize((450, 450), Image.Resampling.LANCZOS)
                frames.append(ImageTk.PhotoImage(frame))
                miata_gif.seek(miata_gif.tell() + 1)
        except EOFError:
            pass
        self.miata_gif_list.append(frames)

     # Load miata20 and miata21 GIFs
     for i in [20, 21]:
        gif_path = f"{base_path}/miata{i}.gif"
        miata_gif = Image.open(gif_path)
        frames = []
        try:
            while True:
                frame = miata_gif.copy().convert('RGBA').resize((450, 450), Image.Resampling.LANCZOS)
                frames.append(ImageTk.PhotoImage(frame))
                miata_gif.seek(miata_gif.tell() + 1)
        except EOFError:
            pass
        self.miata_gif_list.append(frames)

     # Set initial Miata GIF state
     self.current_miata_gif_index = 0
     self.miata_gif_frames_speed = self.miata_gif_list[self.current_miata_gif_index]
     self.current_frame_miata_speed = 0

     # Load background GIF frames
     self.bg_gif_speed = Image.open(f"{base_path}/backgroundv9.gif")
     self.gif_frames_speed = []
     try:
        while True:
            frame = self.bg_gif_speed.copy().convert('RGBA').resize((450, 450), Image.Resampling.LANCZOS)
            self.gif_frames_speed.append(ImageTk.PhotoImage(frame))
            self.bg_gif_speed.seek(self.bg_gif_speed.tell() + 1)
     except EOFError:
        pass

     # Initialize display element IDs
     self.speed_image_id = None
     self.speed_text_id = None
     self.car_image_speed_id = None
     self.current_frame_speed = 0



    def setup_rpm(self):
     # Get the directory where the script is located
     script_dir = os.path.dirname(os.path.abspath(__file__))

     # Define the relative path to 'speed' folder
     base_path = os.path.join(script_dir, r"RPM/RPM")
    
     # Load Turbo images from Turbo15.png to Turbo29.png
     self.turbo_images = {}
    
     # Load Turbo.png (for 0 to 1400 RPM)
     self.turbo_images[0] = ImageTk.PhotoImage(Image.open(f"{base_path}/Turbo.png").resize((300, 300), Image.Resampling.LANCZOS))
    
     # Load from Turbo15.png to Turbo29.png for 1500+ RPM
     for i in range(15, 50):  # 15 to 29 corresponds to 1500 to 3900 RPM
         img_path = f"{base_path}/Turbo{i}.png"
         self.turbo_images[i] = ImageTk.PhotoImage(Image.open(img_path).resize((300, 300), Image.Resampling.LANCZOS))
    
     # Load background GIF frames
     self.bg_gif_rpm = Image.open(f"{base_path}/background.gif")
     self.gif_frames_rpm = []
     try:
         while True:
             frame = self.bg_gif_rpm.copy().convert('RGBA').resize((450, 450), Image.Resampling.LANCZOS)
             self.gif_frames_rpm.append(ImageTk.PhotoImage(frame))
             self.bg_gif_rpm.seek(self.bg_gif_rpm.tell() + 1)
     except EOFError:
         pass  # End of GIF

     self.rpm_image_id = None
     self.rpm_text_id = None

##################################################################################################################

    def setup_race(self):
     # Initialize race-specific variables
     self.gif_frames_race = []
     self.race_start_time = None
     self.time_to_reach_100kph = None
     self.last_three_times = []
     self.best_time = None
     self.green_filter_id = None

     # Load the background GIF for the race scene
     script_dir = os.path.dirname(os.path.abspath(__file__))
     base_path = os.path.join(script_dir, "Speed")
     self.bg_gif_race = Image.open(f"{base_path}/light-speed.gif")

     try:
         while True:
             frame = self.bg_gif_race.copy().convert('RGBA').resize((450, 450), Image.Resampling.LANCZOS)
             self.gif_frames_race.append(ImageTk.PhotoImage(frame))
             self.bg_gif_race.seek(self.bg_gif_race.tell() + 1)
     except EOFError:
         pass

     self.current_frame_race = 0

##################################################################################################################

    def setup_fuel(self):
    
     # Get the directory where the script is located
     script_dir = os.path.dirname(os.path.abspath(__file__))

     # Define the relative path to 'speed' folder
     base_path = os.path.join(script_dir, "Fuel")
    
     # Load miata gif frames and apply mirroring
     self.miata_gif = Image.open(f"{base_path}/miatagif.gif")
     self.miata_gif_frames = []

     try:
        while True:
            frame = self.miata_gif.copy().convert('RGBA').resize((350, 350), Image.Resampling.LANCZOS)
            mirrored_frame = ImageOps.mirror(frame)  # Mirror the frame
            self.miata_gif_frames.append(ImageTk.PhotoImage(mirrored_frame))
            self.miata_gif.seek(self.miata_gif.tell() + 1)
     except EOFError:
        pass  # End of GIF

     # Load background gif
     self.bg_gif_fuel = Image.open(f"{base_path}/backgroundfull.gif")
     self.gif_frames_fuel = []

     try:
        while True:
            frame = self.bg_gif_fuel.copy().convert('RGBA').resize((450, 450))
            self.gif_frames_fuel.append(ImageTk.PhotoImage(frame))
            self.bg_gif_fuel.seek(self.bg_gif_fuel.tell() + 1)
     except EOFError:
        pass  # End of GIF

     # Load fuel gif (for the drink) and apply tilt
     self.fuel_gif = Image.open(f"{base_path}/Drinkgif.gif")
     self.fuel_gif_frames = []

     try:
        while True:
            frame = self.fuel_gif.copy().convert('RGBA').resize((200, 200), Image.Resampling.LANCZOS)
            tilted_frame = frame.rotate(25, expand=True)  # Apply tilt to the fuel GIF
            self.fuel_gif_frames.append(ImageTk.PhotoImage(tilted_frame))
            self.fuel_gif.seek(self.fuel_gif.tell() + 1)
     except EOFError:
        pass  # End of GIF

     self.total_frames_fuel = len(self.fuel_gif_frames)  # Total number of frames for the fuel gif

     # Initialize IDs
     self.fuel_image_id = None
     self.car_image_id = None
     self.drink_image_id = None
     self.fuel_text_id = None
     self.current_frame_miata = 0  # Initialize the miata gif frame counter


    def play_transition_miata20(self, reverse=False):
     self.miata_gif_frames_speed = self.miata_gif_list[6]  # miata20.gif
     self.current_frame_miata_speed = len(self.miata_gif_frames_speed) - 1 if reverse else 0

     def update_frame():
        if reverse:
            self.current_frame_miata_speed -= 1
            if self.current_frame_miata_speed < 0:
                self.switch_to_miata1()
                self.reverse_transition_playing = False
                return
        else:
            self.current_frame_miata_speed += 1
            if self.current_frame_miata_speed >= len(self.miata_gif_frames_speed):
                self.switch_to_miata21()
                self.transition_playing = False
                return

        self.canvas.itemconfig(self.car_image_speed_id, image=self.miata_gif_frames_speed[self.current_frame_miata_speed])
        self.root.after(100, update_frame)

     update_frame()

    def switch_to_miata21(self):
     self.miata_gif_frames_speed = self.miata_gif_list[7]  # miata21.gif
     self.current_frame_miata_speed = 0
     self.miata21_playing = True

    def switch_to_miata1(self):
     self.miata_gif_frames_speed = self.miata_gif_list[0]  # miata1.gif
     self.current_frame_miata_speed = 0
     self.miata21_playing = False




    def show_speed(self):
     self.screen_mode = 1
     self.canvas.delete("all")

     # Display background
     self.speed_image_id = self.canvas.create_image(0, 0, anchor='nw', image=self.gif_frames_speed[0])

     # Set initial car GIF based on speed threshold
     if self.current_speed >= 100:
        self.miata_gif_frames_speed = self.miata_gif_list[7]  # miata21 frames for speeds >= 100
        self.current_miata_gif_index = 7
     else:
        # Randomly select a GIF (miata1 to miata6) when speed is less than 100
        self.current_miata_gif_index = random.randint(0, 5)  # miata1 to miata6
        self.miata_gif_frames_speed = self.miata_gif_list[self.current_miata_gif_index]

     self.current_frame_miata_speed = 0
     self.car_image_speed_id = self.canvas.create_image(20, 40, anchor='nw', image=self.miata_gif_frames_speed[0])

     # Display speed and distance texts
     self.speed_text_id = self.canvas.create_text(
        225, 400,
        text=f"{self.current_speed} km/h",
        font=('Press Start 2P', 24, 'bold'),
        fill='white'
     )

     self.distance_text_id = self.canvas.create_text(
        325, 50,
        text=f"{self.total_distance:.2f} km",
        font=('Digital-7', 12, 'bold'),
        fill='white'
     )

     # Synchronize animations with current speed
     self.update_speed()
     self.update_background()
     self.update_miata_gif()


    def update_miata_gif(self):
     if self.simulation_running or self.use_obd2:
        if self.current_speed == 0:
            # Freeze the Miata GIF when speed is 0
            return

        # Transition to high speed (miata20 then miata21)
        if self.current_speed >= 100:
            if not self.transition_playing and self.current_miata_gif_index != 7:
                # Start miata20 transition
                self.transition_playing = True
                self.current_miata_gif_index = 6  # miata20
                self.miata_gif_frames_speed = self.miata_gif_list[6]
                self.current_frame_miata_speed = 0  # Start at first frame

            elif self.transition_playing and self.current_miata_gif_index == 6:
                # Play miata20 frames
                if self.current_frame_miata_speed < len(self.miata_gif_frames_speed) - 1:
                    self.current_frame_miata_speed += 1
                else:
                    # Transition to miata21 after miata20 finishes
                    self.transition_playing = False
                    self.current_miata_gif_index = 7  # miata21
                    self.miata_gif_frames_speed = self.miata_gif_list[7]
                    self.current_frame_miata_speed = 0

            elif self.current_miata_gif_index == 7:
                # Loop miata21 frames
                self.current_frame_miata_speed = (self.current_frame_miata_speed + 1) % len(self.miata_gif_frames_speed)

        # Transition to lower speed (reverse miata20 then another GIF)
        else:
            if not self.transition_playing and self.current_miata_gif_index == 7:
                # Start reverse transition with miata20 when leaving miata21
                self.transition_playing = True
                self.current_miata_gif_index = 6  # miata20
                self.miata_gif_frames_speed = self.miata_gif_list[6]
                self.current_frame_miata_speed = len(self.miata_gif_frames_speed) - 1  # Start from last frame

            elif self.transition_playing and self.current_miata_gif_index == 6:
                # Reverse play miata20 frames
                if self.current_frame_miata_speed > 0:
                    self.current_frame_miata_speed -= 1
                else:
                    # Finish reverse transition
                    self.transition_playing = False
                    # Randomly select a new GIF (miata1 to miata6)
                    self.current_miata_gif_index = random.randint(0, 5)  # miata1 to miata6
                    self.miata_gif_frames_speed = self.miata_gif_list[self.current_miata_gif_index]
                    self.current_frame_miata_speed = 0

            elif not self.transition_playing:
                # Continue playing the selected GIF until it completes
                self.current_frame_miata_speed = (self.current_frame_miata_speed + 1) % len(self.miata_gif_frames_speed)

        # Update the canvas with the current frame
        self.canvas.itemconfig(self.car_image_speed_id, image=self.miata_gif_frames_speed[self.current_frame_miata_speed])

        # Schedule the next frame update with a fixed delay
        self.root.after(100, self.update_miata_gif)
     else:
        # Reset to first frame if simulation is not running
        self.current_frame_miata_speed = 0
        self.canvas.itemconfig(self.car_image_speed_id, image=self.miata_gif_frames_speed[self.current_frame_miata_speed])




    def update_background(self):
     if self.simulation_running or self.use_obd2:  # Ensure background only updates when simulation is running
        if self.current_speed == 0:
            # Freeze the background GIF when speed is 0
            return

        # Define the speed limits for scaling
        min_speed = 0    # Minimum speed (no movement)
        max_speed = 175  # Maximum speed for 2x speed

        # Calculate the scaling factor based on the current speed, linearly mapping 0 to 2x speed
        if self.current_speed <= min_speed:
            speed_factor = 0  # No movement at 0 kph
        elif self.current_speed >= max_speed:
            speed_factor = 3  # 2x speed at 175 kph
        else:
            # Linear interpolation to get speed factor between 0 and 3
            speed_factor = (self.current_speed - min_speed) / (max_speed - min_speed) * 3

        # Calculate the delay based on the speed factor
        # Assume the normal frame update delay is 100ms; reduce it as speed_factor increases
        normal_delay = 100  # Base delay for normal speed
        background_animation_delay = normal_delay / (1 + speed_factor)

        # Update the current frame of the background gif
        self.current_frame_speed = (self.current_frame_speed + 1) % len(self.gif_frames_speed)
        self.canvas.itemconfig(self.speed_image_id, image=self.gif_frames_speed[self.current_frame_speed])

        # Schedule the next background frame update based on the adjusted delay
        self.root.after(int(background_animation_delay), self.update_background)



    def update_speed(self):
     if self.screen_mode == 1 and (self.simulation_running or self.use_obd2):
        self.canvas.itemconfig(self.speed_text_id, text=f"{self.current_speed} km/h")

        current_time = time.time()
        elapsed_time = current_time - self.last_time
        self.last_time = current_time

        distance_increment = (self.current_speed / 3450) * elapsed_time
        self.total_distance += distance_increment
        self.canvas.itemconfig(self.distance_text_id, text=f"{self.total_distance:.2f} km")

        # Adjust speed based on key press
        self.current_speed += self.speed_direction
        self.current_speed = max(self.min_speed, min(self.current_speed, self.max_speed))  # Keep within limits

        # Re-trigger animations if speed changes from 0 to a positive value
        if self.current_speed > 0 and self.last_speed == 0:
            self.update_miata_gif()
            self.update_background()

        # Update the last speed
        self.last_speed = self.current_speed

        # Schedule next update
        self.root.after(100, self.update_speed)



    def show_rpm(self):
     self.screen_mode = 2
     self.canvas.delete("all")
    
     # Display background GIF (initial frame)
     self.rpm_image_id = self.canvas.create_image(0, 0, anchor='nw', image=self.gif_frames_rpm[0])
    
     # Display initial Turbo image (starting with Turbo.png for 0 RPM)
     self.turbo_image_id = self.canvas.create_image(100, 100, anchor='nw', image=self.turbo_images[0])
    
     # RPM text display
     self.rpm_text_id = self.canvas.create_text(
        225, 400,
        text=f"{self.current_rpm}",
        font=('Digital-7', 24, 'bold'),
        fill='white'
     )
    
     self.update_rpm()

    def update_rpm(self):
     if self.screen_mode == 2 and (self.simulation_running or self.use_obd2):
        # Update background GIF frame
        self.current_frame_rpm = (self.current_frame_rpm + 1) % len(self.gif_frames_rpm)
        self.canvas.itemconfig(self.rpm_image_id, image=self.gif_frames_rpm[self.current_frame_rpm])
        
        # Determine which Turbo image to display based on RPM
        if self.current_rpm <= 1400:
            turbo_image_index = 0  # Display Turbo.png for RPM 0 to 1400
        elif self.current_rpm < 1500:
            turbo_image_index = 0  # Still display Turbo.png for RPM less than 1500
        else:
            turbo_image_index = min(self.current_rpm // 100, 49)  # 1500 to 4900 RPM -> Turbo15.png to Turbo49.png
            
        # Avoiding KeyError by ensuring valid index
        if turbo_image_index >= 0 and turbo_image_index in self.turbo_images:
            self.canvas.itemconfig(self.turbo_image_id, image=self.turbo_images[turbo_image_index])
        else:
            self.canvas.itemconfig(self.turbo_image_id, image=self.turbo_images[0])  # Fallback to Turbo.png

        # Update RPM text
        self.canvas.itemconfig(self.rpm_text_id, text=f"{self.current_rpm}")

        # Cycle RPM from 0 to 7000
        #self.current_rpm = (self.current_rpm + 100) % 7001

        # Repeat update after 100ms
        self.root.after(100, self.update_rpm)


    def show_fuel(self):
     self.screen_mode = 3
     self.canvas.delete("all")

     # Display the background animation
     self.fuel_image_id = self.canvas.create_image(0, 0, anchor='nw', image=self.gif_frames_fuel[0])
    
     # Display the Miata GIF animation
     if self.miata_gif_frames:
         self.car_image_id = self.canvas.create_image(0, 130, anchor='nw', image=self.miata_gif_frames[0])
    
     # Display the fuel container gif (the "drink" animation)
     if self.fuel_gif_frames:
         self.drink_image_id = self.canvas.create_image(200, 240, anchor='nw', image=self.fuel_gif_frames[0])
    
     # Display the fuel percentage text
     self.fuel_text_id = self.canvas.create_text(
         225, 400,
         text=f"Fuel: {self.fuel_percentage:.1f}%",
         font=('Arial', 24, 'bold'),
         fill='white'
     )
    
     self.update_fuel()


    def update_fuel(self):
     if self.screen_mode == 3 and self.simulation_running:
        # Update background animation
        self.current_frame_fuel = (self.current_frame_fuel + 1) % len(self.gif_frames_fuel)
        self.canvas.itemconfig(self.fuel_image_id, image=self.gif_frames_fuel[self.current_frame_fuel])

        # Update car gif animation (miata gif)
        self.current_frame_miata = (self.current_frame_miata + 1) % len(self.miata_gif_frames)
        self.canvas.itemconfig(self.car_image_id, image=self.miata_gif_frames[self.current_frame_miata])

        # Update drink gif animation based on fuel percentage (linear frame calculation)
        frame_index = self.get_fuel_frame_index()
        self.canvas.itemconfig(self.drink_image_id, image=self.fuel_gif_frames[frame_index])

        # Update fuel percentage text
        self.canvas.itemconfig(self.fuel_text_id, text=f"{self.fuel_percentage:.1f}%")

        # Decrease fuel percentage
        self.fuel_percentage = max(0, self.fuel_percentage - 0.1)

        # Schedule the next update
        self.root.after(100, self.update_fuel)

    def get_fuel_frame_index(self):
     # Calculate the frame index based on the fuel percentage
     frame_index = int((1 - (self.fuel_percentage / 100)) * (self.total_frames_fuel - 1))
     return frame_index




##################################################################################################################
    def show_race(self):
     self.screen_mode = 5  # Set screen mode to race
     self.canvas.delete("all")

     if not self.gif_frames_race:
        self.setup_race()

     self.race_image_id = self.canvas.create_image(0, 0, anchor='nw', image=self.gif_frames_race[0])

     self.speed_text_id = self.canvas.create_text(
        225, 250,
        text=f"{self.current_speed} km/h",
        font=('Press Start 2P', 48, 'bold'),
        fill='white'
     )

     if self.current_speed == 0:
        self.race_start_time = time.time()

     self.update_race()

    def update_race(self):
     if self.screen_mode == 5 and (self.simulation_running or self.use_obd2):
        self.canvas.itemconfig(self.speed_text_id, text=f"{self.current_speed} km/h")

        current_time = time.time()
        elapsed_time = current_time - self.last_time
        self.last_time = current_time

        self.current_speed += self.speed_direction
        self.current_speed = max(self.min_speed, min(self.current_speed, self.max_speed))

        if self.current_speed > 0:
            self.current_frame_race = (self.current_frame_race + 1) % len(self.gif_frames_race)
            self.canvas.itemconfig(self.race_image_id, image=self.gif_frames_race[self.current_frame_race])

        if self.race_start_time is not None:
            if self.current_speed >= 100 and self.time_to_reach_100kph is None:
                self.time_to_reach_100kph = current_time - self.race_start_time
                self.last_three_times.append(self.time_to_reach_100kph)
                if len(self.last_three_times) > 3:
                    self.last_three_times.pop(0)
                if self.best_time is None or self.time_to_reach_100kph < self.best_time:
                    self.best_time = self.time_to_reach_100kph

                self.update_time_display()

        if self.current_speed >= 100 and self.green_filter_id is None:
            self.green_filter_id = self.canvas.create_rectangle(
                0, 0, 450, 450, fill='green', stipple='gray50'
            )
        elif self.current_speed < 100 and self.green_filter_id is not None:
            self.canvas.delete(self.green_filter_id)
            self.green_filter_id = None

        # Reset time_to_reach_100kph when speed drops to 0
        if self.current_speed == 0:
            self.time_to_reach_100kph = None
            self.race_start_time = current_time  # Reset the start time for the next race

        self.root.after(max(100 - self.current_speed, 10), self.update_race)

    def update_time_display(self):
     self.canvas.delete("time_text")

     # Display last three times at the far left corner
     y_position = 50
     self.canvas.create_text(
        10, y_position - 20,
        text="Last 0-100:",
        font=('Press Start 2P', 12, 'bold'),
        fill='white',
        anchor='nw',
        tags="time_text"
     )
     for i, time_to_100 in enumerate(self.last_three_times):
        self.canvas.create_text(
            10, y_position,
            text=f"       - {time_to_100:.2f} s",
            font=('Press Start 2P', 12, 'bold'),
            fill='white',
            anchor='nw',
            tags="time_text"
        )
        y_position += 20

     # Display best time at the far right corner
     if self.best_time is not None:
        self.canvas.create_text(
            440, 50,
            text=f"Best Time: {self.best_time:.2f} s",
            font=('Press Start 2P', 12, 'bold'),
            fill='white',
            anchor='ne',
            tags="time_text"
        )



##################################################################################################################



     
    def show_clock(self):
     self.screen_mode = 4
     self.canvas.delete("all")  # Clear the canvas
    
     # Create a black background
     self.canvas.config(bg='black')
    
     # Create the clock text on the canvas
     self.clock_text_id = self.canvas.create_text(
         225, 225,  # Center of the 450x450 canvas
         text=self.get_current_time(),
         font=('Digital-7', 48, 'bold'),  # Slick, large font
         fill='white'
     )
    
     # Start updating the clock
     self.update_clock()



    def update_clock(self):
     if self.screen_mode == 4:  # Ensure we're in the clock mode
        current_time = self.get_current_time()
        self.canvas.itemconfig(self.clock_text_id, text=current_time)
        
        # Update the clock every second (1000 milliseconds)
        self.root.after(1000, self.update_clock)



    def get_current_time(self):
     # Returns the current time in hours:minutes:seconds format
     return time.strftime("%H:%M:%S")
    

 

    def on_click(self, event):

     if self.menu_visible:
         return
     elif self.screen_mode == 0:  # Intro mode
         return
     elif self.screen_mode == 1:  # Speed mode
         self.show_rpm()
     elif self.screen_mode == 2:  # RPM mode
         self.show_fuel()
     elif self.screen_mode == 3:  # Fuel mode
         self.show_race()  # Show race scene after fuel scene
     elif self.screen_mode == 4:  # Clock mode
         self.show_speed()
     elif self.screen_mode == 5:  # Race mode
         self.show_clock()  # Show clock scene after race scene ##################################################################################################################




    def create_menu(self):
     # Create menu frame and place it out of view initially
     self.menu = tk.Frame(self.root, bg="black")
     self.menu.place(x=0, y=-450, width=450, height=450)

     # Start/Stop Simulation button
     self.start_simulation_button = tk.Button(self.menu, text="Start Simulation", command=self.toggle_simulation, 
                                             bg='black', fg='white', font=('Arial', 12, 'bold'), height=12, width=24, padx=5, pady=5)
     self.start_simulation_button.place(relx=0.5, rely=0.3, anchor='center')  # Adjusted relx to 0.5 for centering

     # Error button
     self.error_button = tk.Button(self.menu, text="Errors", command=self.show_errors, 
                                  bg='black', fg='white', font=('Arial', 12, 'bold'), height=12, width=24, padx=5, pady=5)
     self.error_button.place(relx=0.5, rely=0.5, anchor='center')  # Adjusted relx to 0.5 for centering

     # Close App button
     self.close_button = tk.Button(self.menu, text="Close App", command=self.close_app, 
                                  bg='black', fg='white', font=('Arial', 12, 'bold'), height=12, width=24, padx=5, pady=5)
     self.close_button.place(relx=0.5, rely=0.7, anchor='center')  # Adjusted relx to 0.5 for centering


    def update_display(self):
        if self.screen_mode == 1:  # Speed mode
            self.canvas.itemconfig(self.speed_text_id, text=f"{self.current_speed:.0f} km/h")
            self.canvas.itemconfig(self.distance_text_id, text=f"{self.total_distance:.2f} km")
        elif self.screen_mode == 2:  # RPM mode
            self.canvas.itemconfig(self.rpm_text_id, text=f"{self.current_rpm:.0f}")


    def toggle_simulation(self):
     if self.simulation_running:
        self.stop_simulation()
     else:
        self.start_simulation()

    def start_simulation(self):
        if self.use_obd2:
            print("Cannot start simulation while OBD-II is active.")
            return

        self.simulation_running = True
        self.use_obd2 = False  # Switch to simulation mode
        self.current_speed = 0
        self.current_rpm = 0
        self.simulator_gui = OBDSimulatorGUI(self.obd_simulator)  # Pass the obd_simulator instance
        self.read_obd2_data()  # Start reading simulated data
        self.start_simulation_button.config(text="Stop Simulation")
        self.show_speed()

    def stop_simulation(self):
        self.simulation_running = False
        if self.simulator_gui:
            self.simulator_gui.simulation_running = False
            self.simulator_gui.root.destroy()  # Close the simulator window
        self.start_simulation_button.config(text="Start Simulation")

    def show_menu(self):
        self.menu_visible = True
        self.menu.place(x=0, y=0)

    def hide_menu(self):
        self.menu_visible = False
        self.menu.place(x=0, y=-450)

    def close_app(self):
        self.root.quit()


    def show_error_page(self):
     # Close the menu if it's visible
     if self.menu_visible:
        self.hide_menu()

     # Clear the canvas to show the error page
     self.canvas.delete("all")
     
     # Get the directory where the script is located
     script_dir = os.path.dirname(os.path.abspath(__file__))

     # Define the relative path to 'speed' folder
     base_path = os.path.join(script_dir, "Other")
     original_image = Image.open(f"{base_path}/Error.png")
     resized_image = original_image.resize((450, 450), Image.Resampling.LANCZOS)  # Use LANCZOS for high-quality resizing
     self.error_bg = ImageTk.PhotoImage(resized_image)

     # Display the resized image
     self.canvas.create_image(0, 0, anchor="nw", image=self.error_bg)

     error_text = ""
     if self.connection and self.connection.is_connected():
        # If there is a connection, query for errors
        errors = self.connection.query(obd.commands.GET_DTC)
        if errors.is_null():
            error_text = "No errors"
        else:
            error_text = "\n".join([f"{code}: {desc}" for code, desc in errors.value])
     else:
        # If no connection is established, display this message
        error_text = "OBD2 connection not established"

     # Display the errors or message on the canvas
     self.canvas.create_text(225, 100, text=error_text, fill="white", font=("Arial", 18, "bold"))

     # Bind swipe events for closing the error page
     self.canvas.bind("<Button-1>", self.on_swipe)  # Start swipe detection
     self.canvas.bind("<ButtonRelease-1>", self.on_swipe_end_error)  # End swipe detection to close error page

    def on_swipe_end_error(self, event):
     if self.start_y is not None:
        swipe_distance = event.y - self.start_y
        if swipe_distance < -self.swipe_threshold:  # Swipe up
            self.hide_error_page()  # Close the error page on swipe up
        self.start_y = None

    def hide_error_page(self, event=None):
     # Clear the error page and return to the previous scene
     self.canvas.delete("all")
     self.show_speed()  # Or any other scene you want to return to
    
     # Re-bind the swipe events for opening/closing the menu
     self.canvas.bind("<Button-1>", self.on_swipe)  # Start swipe detection for menu
     self.canvas.bind("<ButtonRelease-1>", self.on_swipe_end)  # End swipe detection for menu




    def show_errors(self):
        self.hide_menu()  # Hide menu when showing errors

        # Background for the error page
        self.error_bg_label = tk.Label(self.root, image=self.error_background_image)
        self.error_bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Query OBD2 errors
        if self.connection and self.connection.is_connected():
            errors = self.query_obd2_errors()
        else:
            errors = ["No OBD2 connection"]

        # Display errors in a scrollable text widget
        self.error_text = tk.Text(self.root, wrap="word", font=("Helvetica", 14), bg="black", fg="white")
        self.error_text.place(x=50, y=50, width=225, height=100)

        if not errors:
            self.error_text.insert("1.0", "No errors")
        else:
            for error in errors:
                self.error_text.insert("end", f"{error}\n")

        # Scrollbar for multiple errors
        self.scrollbar = tk.Scrollbar(self.error_text)
        self.error_text.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.error_text.yview)
        self.scrollbar.pack(side="right", fill="y")

        # Back button to return to the animation
        self.back_button = tk.Button(self.root, text="Back", command=self.show_speed)
        self.back_button.place(x=50, y=300, width=100, height=50)

    def query_obd2_errors(self):
        errors = []
        try:
            trouble_codes_cmd = obd.commands.GET_DTC
            trouble_codes = self.connection.query(trouble_codes_cmd)
            if trouble_codes.value:
                errors = [f"{code}" for code in trouble_codes.value]  # Parse error codes
        except Exception as e:
            print(f"Error querying OBD2: {e}")
        return errors

    def on_swipe(self, event):
        if self.start_y is None:
            self.start_y = event.y

    def on_swipe_end(self, event):
        if self.start_y is not None:
            swipe_distance = event.y - self.start_y
            if swipe_distance > self.swipe_threshold:
                if not self.menu_visible:
                    self.show_menu()
            elif swipe_distance < -self.swipe_threshold:
                if self.menu_visible:
                    self.hide_menu()
            self.start_y = None

if __name__ == "__main__":
    root = tk.Tk()
    app = CarGadgetApp(root)
    root.mainloop()