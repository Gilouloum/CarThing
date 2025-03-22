import tkinter as tk
from tkinter import ttk

class OBDSimulator:
    def __init__(self):
        self.speed = 0
        self.rpm = 0

    def set_speed(self, speed):
        self.speed = speed

    def set_rpm(self, rpm):
        self.rpm = rpm

    def get_data(self):
        # Return simulated OBD-II data
        return {
            "speed": self.speed,
            "rpm": self.rpm
        }

class OBDSimulatorGUI:
    def __init__(self, obd_simulator):
        self.root = tk.Toplevel()  # Create a new top-level window
        self.obd_simulator = obd_simulator

        self.root.title("OBD-II Simulator")

        # Speed slider
        self.speed_label = ttk.Label(self.root, text="Speed (km/h):")
        self.speed_label.pack()
        self.speed_var = tk.DoubleVar(value=0)
        self.speed_slider = ttk.Scale(self.root, from_=0, to=200, variable=self.speed_var, command=self.update_speed)
        self.speed_slider.pack()

        # RPM slider
        self.rpm_label = ttk.Label(self.root, text="RPM:")
        self.rpm_label.pack()
        self.rpm_var = tk.DoubleVar(value=0)
        self.rpm_slider = ttk.Scale(self.root, from_=0, to=8000, variable=self.rpm_var, command=self.update_rpm)
        self.rpm_slider.pack()

        # Remove the start simulation button
        # self.start_button = ttk.Button(self.root, text="Start Simulation", command=self.start_simulation)
        # self.start_button.pack()

        self.simulation_running = True  # Start simulation immediately
        self.simulate()

    def update_speed(self, event):
        speed = self.speed_var.get()
        self.obd_simulator.set_speed(speed)

    def update_rpm(self, event):
        rpm = self.rpm_var.get()
        self.obd_simulator.set_rpm(rpm)

    def simulate(self):
        if self.simulation_running:
            data = self.obd_simulator.get_data()
            # Format speed and rpm as integers without decimal points
            speed_str = f"{int(round(data['speed']))}"
            rpm_str = f"{int(round(data['rpm']))}"
            print(f"Simulated Data - Speed: {speed_str} km/h, RPM: {rpm_str}")
            # Here, you would send the data to your application
            self.root.after(200, self.simulate)

if __name__ == "__main__":
    root = tk.Tk()
    obd_simulator = OBDSimulator()
    gui = OBDSimulatorGUI(obd_simulator)
    root.mainloop()
